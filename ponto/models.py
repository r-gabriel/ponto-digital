from django.conf import settings
from django.db import models


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
    data_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    observacao = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Registro de ponto'
        verbose_name_plural = 'Registros de ponto'
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.funcionario} - {self.get_tipo_display()} em {self.data_hora}'