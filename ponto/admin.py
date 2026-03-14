from django.contrib import admin
from django.utils import timezone
from .models import RegistroPonto, JornadaDiaria, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cargo', 'turno', 'data_admissao', 'valor_hora', 'primeiro_acesso')
    list_filter = ('turno', 'primeiro_acesso')
    search_fields = ('usuario__username', 'usuario__first_name', 'cargo')
    ordering = ('usuario__username',)


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalcula a jornada do dia após salvar pelo admin
        data = obj.data_hora.date()
        jornada, _ = JornadaDiaria.objects.get_or_create(
            funcionario=obj.funcionario,
            data=data
        )
        jornada.calcular()

    def delete_model(self, request, obj):
        data = obj.data_hora.date()
        funcionario = obj.funcionario
        super().delete_model(request, obj)
        # Recalcula após deletar também
        jornada, _ = JornadaDiaria.objects.get_or_create(
            funcionario=funcionario,
            data=data
        )
        jornada.calcular()


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