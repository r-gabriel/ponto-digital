from django.urls import path
from . import views

urlpatterns = [
    path('bater/', views.bater_ponto, name='bater_ponto'),
    path('historico/', views.historico_ponto, name='historico_ponto'),
    path('relatorio/', views.relatorio_jornadas, name='relatorio_jornadas'),
    path('colaboradores/', views.lista_colaboradores, name='lista_colaboradores'),
    path('colaboradores/novo/', views.cadastrar_colaborador, name='cadastrar_colaborador'),
    path('colaboradores/<int:user_id>/editar/', views.editar_colaborador, name='editar_colaborador'),
    path('primeiro-acesso/', views.primeiro_acesso, name='primeiro_acesso'),
]