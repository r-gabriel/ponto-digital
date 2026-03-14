from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import RegistroPonto


@login_required
def bater_ponto(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')

        # Segurança mínima: aceita só 'E' ou 'S'
        if tipo in ['E', 'S']:
            RegistroPonto.objects.create(
                funcionario=request.user,
                tipo=tipo,
                data_hora=timezone.now()
            )
        return redirect('historico_ponto')

    return render(request, 'ponto/bater_ponto.html')


@login_required
def historico_ponto(request):
    registros = RegistroPonto.objects.filter(
        funcionario=request.user
    ).order_by('-data_hora')[:50]  # últimos 50 registros

    return render(request, 'ponto/historico_ponto.html', {'registros': registros})