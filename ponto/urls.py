from django.urls import path
from . import views

urlpatterns = [
    path('bater/', views.bater_ponto, name='bater_ponto'),
    path('historico/', views.historico_ponto, name='historico_ponto'),
    path('relatorio/', views.relatorio_jornadas, name='relatorio_jornadas'),
]