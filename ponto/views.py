from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime

from .decorators import gestor_required
from .forms import CadastroColaboradorForm, PerfilColaboradorForm, PrimeiroAcessoForm, EditarPerfilForm, EditarUsuarioForm, FotoPerfilForm
from .models import RegistroPonto, JornadaDiaria, Perfil


@login_required
def bater_ponto(request):
    # Redireciona para o primeiro acesso se necessário
    if hasattr(request.user, 'perfil') and request.user.perfil.primeiro_acesso:
        return redirect('primeiro_acesso')

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

    jornadas = JornadaDiaria.objects.filter(
        funcionario=request.user
    ).order_by('-data')[:30]

    return render(request, 'ponto/historico_ponto.html', {
        'registros': registros,
        'jornadas': jornadas,
    })


@gestor_required
def relatorio_jornadas(request):
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

            def fmt(dur):
                if not dur:
                    return '--:--'
                total_segundos = int(dur.total_seconds())
                horas, resto = divmod(total_segundos, 3600)
                minutos = resto // 60
                return f'{horas:02d}:{minutos:02d}'

            agregados = jornadas.aggregate(
                trabalhado=Sum('total_trabalhado'),
                intervalo=Sum('total_intervalo'),
                extras=Sum('horas_extras'),
            )

            totais = {
                'trabalhado': fmt(agregados['trabalhado']),
                'intervalo': fmt(agregados['intervalo']),
                'extras': fmt(agregados['extras']),
            }

        except ValueError:
            messages.error(request, 'Datas em formato inválido.')

    return render(request, 'ponto/relatorio_jornadas.html', {
        'funcionarios': funcionarios,
        'jornadas': jornadas,
        'totais': totais,
        'funcionario_id': funcionario_id or '',
        'data_inicial': data_inicial or '',
        'data_final': data_final or '',
    })


@gestor_required
def cadastrar_colaborador(request):
    if request.method == 'POST':
        user_form = CadastroColaboradorForm(request.POST)
        perfil_form = PerfilColaboradorForm(request.POST)

        if user_form.is_valid() and perfil_form.is_valid():
            usuario = user_form.save()

            # O perfil já foi criado pelo signal, só atualiza os dados
            perfil = usuario.perfil
            perfil.cargo = perfil_form.cleaned_data['cargo']
            perfil.data_admissao = perfil_form.cleaned_data['data_admissao']
            perfil.turno = perfil_form.cleaned_data['turno']
            perfil.valor_hora = perfil_form.cleaned_data['valor_hora']
            perfil.jornada_diaria_horas = perfil_form.cleaned_data['jornada_diaria_horas']
            perfil.primeiro_acesso = True
            perfil.save()

            messages.success(
                request,
                f'Colaborador {usuario.get_full_name() or usuario.username} '
                f'cadastrado com sucesso.'
            )
            return redirect('lista_colaboradores')
    else:
        user_form = CadastroColaboradorForm()
        perfil_form = PerfilColaboradorForm()

    return render(request, 'ponto/cadastrar_colaborador.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
    })


@gestor_required
def lista_colaboradores(request):
    colaboradores = User.objects.select_related('perfil').order_by('first_name', 'last_name')
    return render(request, 'ponto/lista_colaboradores.html', {
        'colaboradores': colaboradores,
    })


@login_required
def primeiro_acesso(request):
    # Se não é primeiro acesso, manda para o ponto
    if not request.user.perfil.primeiro_acesso:
        return redirect('bater_ponto')

    if request.method == 'POST':
        form = PrimeiroAcessoForm(request.POST)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['nova_senha'])
            user.save()

            # Marca que o primeiro acesso foi concluído
            user.perfil.primeiro_acesso = False
            user.perfil.save()

            messages.success(
                request,
                'Perfil atualizado com sucesso. Faça login com sua nova senha.'
            )
            return redirect('login')
    else:
        form = PrimeiroAcessoForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    return render(request, 'ponto/primeiro_acesso.html', {'form': form})

@gestor_required
def editar_colaborador(request, user_id):
    colaborador = get_object_or_404(User, pk=user_id)

    # Garante que o perfil existe
    perfil, _ = Perfil.objects.get_or_create(usuario=colaborador)

    if request.method == 'POST':
        user_form = EditarUsuarioForm(request.POST, instance=colaborador)
        perfil_form = EditarPerfilForm(request.POST, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(
                request,
                f'Dados de {colaborador.get_full_name() or colaborador.username} '
                f'atualizados com sucesso.'
            )
            return redirect('lista_colaboradores')
    else:
        user_form = EditarUsuarioForm(instance=colaborador)
        perfil_form = EditarPerfilForm(instance=perfil)

    return render(request, 'ponto/editar_colaborador.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'colaborador': colaborador,
    })

@login_required
def meu_perfil(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto atualizada com sucesso.')
            return redirect('meu_perfil')
    else:
        form = FotoPerfilForm(instance=perfil)

    return render(request, 'ponto/meu_perfil.html', {
        'perfil': perfil,
        'form': form,
    })