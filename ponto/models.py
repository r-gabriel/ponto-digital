from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


FUSO_BRASILIA = ZoneInfo('America/Sao_Paulo')


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

    # Campos calculados — preenchidos automaticamente
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
        """
        Lê os registros de ponto do dia desse funcionário
        e calcula total trabalhado, intervalo e horas extras.
        Padrão CLT:
          - Intervalo obrigatório de 1h para jornadas acima de 6h
          - Horas extras = total trabalhado - jornada esperada (se positivo)
        """
        registros = list(
            RegistroPonto.objects.filter(
                funcionario=self.funcionario,
                data_hora__date=self.data
            ).order_by('data_hora')
        )

        if len(registros) < 2:
            # Dia incompleto, não calcula
            self.total_trabalhado = None
            self.total_intervalo = None
            self.horas_extras = None
            self.save()
            return

        total_trabalhado = timedelta()
        total_intervalo = timedelta()

        # Percorre os pares E/S
        for i in range(0, len(registros) - 1, 2):
            entrada = registros[i]
            saida = registros[i + 1]

            # Garante que o par está correto
            if entrada.tipo == 'E' and saida.tipo == 'S':
                total_trabalhado += saida.data_hora - entrada.data_hora

            # Calcula intervalo entre saída e próxima entrada
            if i + 2 < len(registros):
                proxima_entrada = registros[i + 2]
                total_intervalo += proxima_entrada.data_hora - saida.data_hora

        self.total_trabalhado = total_trabalhado
        self.total_intervalo = total_intervalo

        # Horas extras: somente se trabalhou além da jornada esperada
        diferenca = total_trabalhado - self.jornada_esperada
        self.horas_extras = diferenca if diferenca > timedelta(0) else timedelta(0)

        self.save()

    def formatar_duracao(self, duracao):
        """Formata timedelta para exibição como HH:MM"""
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