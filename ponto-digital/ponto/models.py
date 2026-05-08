from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


FUSO_BRASILIA = ZoneInfo('America/Sao_Paulo')


class Perfil(models.Model):
    TURNO_CHOICES = (
        ('M', 'Manhã'),
        ('T', 'Tarde'),
        ('N', 'Noturno'),
        ('I', 'Integral'),
    )

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    cargo = models.CharField(max_length=100, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES, blank=True)
    valor_hora = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    jornada_diaria_horas = models.PositiveSmallIntegerField(
        default=8,
        help_text='Jornada diária esperada em horas (ex: 8)'
    )
    primeiro_acesso = models.BooleanField(default=True)
    foto = models.ImageField(
        upload_to='fotos_perfil/',
        null=True,
        blank=True,
        verbose_name='Foto de perfil'
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.usuario.username}'

# Cria automaticamente o Perfil quando um novo User é criado
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(usuario=instance)


class RegistroPonto(models.Model):
    TIPO_CHOICES = (
        ('E', 'Entrada'),
        ('S', 'Saída'),
    )

    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_ponto'
    )
    data_hora = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    observacao = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Registro de ponto'
        verbose_name_plural = 'Registros de ponto'
        ordering = ['-data_hora']

    def __str__(self):
        return (
            f'{self.funcionario} - '
            f'{self.get_tipo_display()} em '
            f'{self.data_hora.astimezone(FUSO_BRASILIA).strftime("%d/%m/%Y às %H:%M")}'
        )

    def clean(self):
        ultimo = (
            RegistroPonto.objects
            .filter(funcionario=self.funcionario)
            .exclude(pk=self.pk)
            .order_by('-data_hora')
            .first()
        )

        if ultimo and ultimo.tipo == self.tipo:
            data_hora_local = ultimo.data_hora.astimezone(FUSO_BRASILIA)
            raise ValidationError(
                f'Sequência inválida: você já registrou uma '
                f'{self.get_tipo_display().lower()} anteriormente. '
                f'O último registro foi: {ultimo.get_tipo_display()} '
                f'em {data_hora_local.strftime("%d/%m/%Y às %H:%M")}.'
            )


class JornadaDiaria(models.Model):
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jornadas'
    )
    data = models.DateField()
    total_trabalhado = models.DurationField(null=True, blank=True)
    total_intervalo = models.DurationField(null=True, blank=True)
    horas_extras = models.DurationField(null=True, blank=True)
    jornada_esperada = models.DurationField(default=timedelta(hours=8))

    class Meta:
        verbose_name = 'Jornada diária'
        verbose_name_plural = 'Jornadas diárias'
        unique_together = ('funcionario', 'data')
        ordering = ['-data']

    def __str__(self):
        return f'{self.funcionario} - {self.data}'

    def calcular(self):
        registros = list(
            RegistroPonto.objects.filter(
                funcionario=self.funcionario,
                data_hora__date=self.data
            ).order_by('data_hora')
        )

        if len(registros) < 2:
            self.total_trabalhado = None
            self.total_intervalo = None
            self.horas_extras = None
            self.save()
            return

        # Pega a jornada esperada do perfil do funcionário
        try:
            horas = self.funcionario.perfil.jornada_diaria_horas
            self.jornada_esperada = timedelta(hours=horas)
        except Perfil.DoesNotExist:
            self.jornada_esperada = timedelta(hours=8)

        total_trabalhado = timedelta()
        total_intervalo = timedelta()

        for i in range(0, len(registros) - 1, 2):
            entrada = registros[i]
            saida = registros[i + 1]

            if entrada.tipo == 'E' and saida.tipo == 'S':
                total_trabalhado += saida.data_hora - entrada.data_hora

            if i + 2 < len(registros):
                proxima_entrada = registros[i + 2]
                total_intervalo += proxima_entrada.data_hora - saida.data_hora

        self.total_trabalhado = total_trabalhado
        self.total_intervalo = total_intervalo

        diferenca = total_trabalhado - self.jornada_esperada
        self.horas_extras = diferenca if diferenca > timedelta(0) else timedelta(0)

        self.save()

    def formatar_duracao(self, duracao):
        if duracao is None:
            return '--:--'
        total_segundos = int(duracao.total_seconds())
        horas, resto = divmod(total_segundos, 3600)
        minutos = resto // 60
        return f'{horas:02d}:{minutos:02d}'

    @property
    def total_trabalhado_fmt(self):
        return self.formatar_duracao(self.total_trabalhado)

    @property
    def total_intervalo_fmt(self):
        return self.formatar_duracao(self.total_intervalo)

    @property
    def horas_extras_fmt(self):
        return self.formatar_duracao(self.horas_extras)
