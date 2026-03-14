from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import RegistroPonto, JornadaDiaria


@login_required
def bater_ponto(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')

        if tipo in ['E', 'S']:
            try:
                registro = RegistroPonto(
                    funcionario=request.user,
                    tipo=tipo,
                )
                registro.full_clean()
                registro.save()

                # Recalcula a jornada do dia automaticamente
                hoje = timezone.localdate()
                jornada, _ = JornadaDiaria.objects.get_or_create(
                    funcionario=request.user,
                    data=hoje
                )
                jornada.calcular()

                messages.success(request, 'Ponto registrado com sucesso.')
                return redirect('historico_ponto')

            except ValidationError as e:
                for erro in e.messages:
                    messages.error(request, erro)
        else:
            messages.error(request, 'Tipo de registro inválido.')

    return render(request, 'ponto/bater_ponto.html')


@login_required
def historico_ponto(request):
    registros = RegistroPonto.objects.filter(
        funcionario=request.user
    ).order_by('-data_hora')[:50]

    # Busca as jornadas calculadas para exibir no histórico
    jornadas = JornadaDiaria.objects.filter(
        funcionario=request.user
    ).order_by('-data')[:30]

    return render(request, 'ponto/historico_ponto.html', {
        'registros': registros,
        'jornadas': jornadas,
    })