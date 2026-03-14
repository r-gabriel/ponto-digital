from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import datetime

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

@login_required
def relatorio_jornadas(request):
    # Parâmetros do filtro
    funcionario_id = request.GET.get('funcionario')
    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')

    funcionarios = User.objects.all().order_by('username')
    jornadas = JornadaDiaria.objects.none()
    totais = {}

    if funcionario_id and data_inicial and data_final:
        try:
            data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()

            jornadas = JornadaDiaria.objects.filter(
                funcionario_id=funcionario_id,
                data__range=(data_ini, data_fim)
            ).order_by('data')

            # Agregados
            agregados = jornadas.aggregate(
                trabalhado=Sum('total_trabalhado'),
                intervalo=Sum('total_intervalo'),
                extras=Sum('horas_extras'),
            )

            def fmt(dur):
                if not dur:
                    return '--:--'
                total_segundos = int(dur.total_seconds())
                horas, resto = divmod(total_segundos, 3600)
                minutos = resto // 60
                return f'{horas:02d}:{minutos:02d}'

            totais = {
                'trabalhado': fmt(agregados['trabalhado']),
                'intervalo': fmt(agregados['intervalo']),
                'extras': fmt(agregados['extras']),
            }

        except ValueError:
            messages.error(request, 'Datas em formato inválido. Use o seletor de datas.')

    return render(request, 'ponto/relatorio_jornadas.html', {
        'funcionarios': funcionarios,
        'jornadas': jornadas,
        'totais': totais,
        'funcionario_id': funcionario_id or '',
        'data_inicial': data_inicial or '',
        'data_final': data_final or '',
    })