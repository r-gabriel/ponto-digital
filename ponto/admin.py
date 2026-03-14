from django.contrib import admin
from .models import RegistroPonto


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'data_hora')
    list_filter = ('tipo', 'data_hora')
    search_fields = ('funcionario__username', 'funcionario__first_name', 'funcionario__last_name')
    ordering = ('-data_hora',)