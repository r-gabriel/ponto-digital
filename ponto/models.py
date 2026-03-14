from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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