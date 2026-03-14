from django.contrib import admin
from .models import RegistroPonto, JornadaDiaria


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'data_hora')
    list_filter = ('tipo', 'data_hora')
    search_fields = (
        'funcionario__username',
        'funcionario__first_name',
        'funcionario__last_name'
    )
    ordering = ('-data_hora',)


@admin.register(JornadaDiaria)
class JornadaDiariaAdmin(admin.ModelAdmin):
    list_display = (
        'funcionario',
        'data',
        'total_trabalhado_fmt',
        'total_intervalo_fmt',
        'horas_extras_fmt'
    )
    list_filter = ('data',)
    search_fields = ('funcionario__username',)
    ordering = ('-data',)