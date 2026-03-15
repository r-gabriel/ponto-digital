from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import RegistroPonto, JornadaDiaria, Perfil
from .forms import (
    CadastroColaboradorForm,
    PerfilColaboradorForm,
    EditarUsuarioForm,
    EditarPerfilForm,
    PrimeiroAcessoForm,
    FotoPerfilForm,
)


# ── helper ──────────────────────────────────────────────────────────────
def is_gestor(user):
    """Retorna True se o usuário é superuser OU pertence a qualquer grupo."""
    return user.is_superuser or user.groups.exists()


def gestor_required(view_func):
    """Decorator simples: redireciona para bater_ponto se não for gestor."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_gestor(request.user):
            messages.error(request, 'Acesso restrito a gestores.')
            return redirect('bater_ponto')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Bater ponto ─────────────────────────────────────────────────────────
@login_required
def bater_ponto(request):
    # Redireciona para primeiro acesso se necessário
    try:
        if request.user.perfil.primeiro_acesso:
            return redirect('primeiro_acesso')
    except Perfil.DoesNotExist:
        pass

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo in ('E', 'S'):
            RegistroPonto.objects.create(
                funcionario=request.user,
                tipo=tipo,
                data_hora=timezone.now(),
            )

            # Recalcula jornada do dia
            hoje = timezone.localdate()
            jornada, _ = JornadaDiaria.objects.get_or_create(
                funcionario=request.user,
                data=hoje,
            )
            jornada.calcular()

            tipo_label = 'Entrada' if tipo == 'E' else 'Saída'
            messages.success(request, f'{tipo_label} registrada com sucesso.')
            return redirect('bater_ponto')

    return render(request, 'ponto/bater_ponto.html')


# ── Histórico ────────────────────────────────────────────────────────────
@login_required
def historico_ponto(request):
    registros = (
        RegistroPonto.objects
        .filter(funcionario=request.user)
        .order_by('-data_hora')
    )
    jornadas = (
        JornadaDiaria.objects
        .filter(funcionario=request.user)
        .order_by('-data')
    )
    return render(request, 'ponto/historico_ponto.html', {
        'registros': registros,
        'jornadas': jornadas,
    })


# ── Relatório ────────────────────────────────────────────────────────────
@gestor_required
def relatorio_jornadas(request):
    from datetime import timedelta

    funcionarios = User.objects.filter(is_active=True).order_by('first_name', 'username')
    jornadas = []
    totais = {'trabalhado': '00:00', 'intervalo': '00:00', 'extras': '00:00'}
    funcionario_id = request.GET.get('funcionario', '')
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    if funcionario_id and data_inicial and data_final:
        try:
            funcionario = User.objects.get(pk=funcionario_id)
            jornadas = (
                JornadaDiaria.objects
                .filter(
                    funcionario=funcionario,
                    data__gte=data_inicial,
                    data__lte=data_final,
                )
                .order_by('data')
            )

            # Calcula totais
            total_trabalhado = timedelta()
            total_intervalo = timedelta()
            total_extras = timedelta()

            for j in jornadas:
                if j.total_trabalhado:
                    total_trabalhado += j.total_trabalhado
                if j.total_intervalo:
                    total_intervalo += j.total_intervalo
                if j.horas_extras and j.horas_extras.total_seconds() > 0:
                    total_extras += j.horas_extras

            def fmt(td):
                total_s = int(td.total_seconds())
                h, m = divmod(total_s // 60, 60)
                return f'{h:02d}:{m:02d}'

            totais = {
                'trabalhado': fmt(total_trabalhado),
                'intervalo': fmt(total_intervalo),
                'extras': fmt(total_extras),
            }
        except User.DoesNotExist:
            pass

    return render(request, 'ponto/relatorio_jornadas.html', {
        'funcionarios': funcionarios,
        'jornadas': jornadas,
        'totais': totais,
        'funcionario_id': funcionario_id,
        'data_inicial': data_inicial,
        'data_final': data_final,
    })


# ── Lista de colaboradores ───────────────────────────────────────────────
@gestor_required
def lista_colaboradores(request):
    colaboradores = (
        User.objects
        .filter(is_active=True)
        .select_related('perfil')
        .order_by('first_name', 'username')
    )
    return render(request, 'ponto/lista_colaboradores.html', {
        'colaboradores': colaboradores,
    })


# ── Cadastrar colaborador ────────────────────────────────────────────────
@gestor_required
def cadastrar_colaborador(request):
    if request.method == 'POST':
        user_form = CadastroColaboradorForm(request.POST)
        perfil_form = PerfilColaboradorForm(request.POST)

        if user_form.is_valid() and perfil_form.is_valid():
            # Cria o usuário
            user = user_form.save(commit=False)
            user.is_active = True

            senha = user_form.cleaned_data.get('senha_inicial')
            if senha:
                user.set_password(senha)
                primeiro_acesso = False
            else:
                user.set_unusable_password()
                primeiro_acesso = True

            user.save()

            # Cria o perfil vinculado
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user
            perfil.primeiro_acesso = primeiro_acesso
            perfil.save()

            messages.success(
                request,
                f'Colaborador "{user.get_full_name() or user.username}" '
                f'cadastrado com sucesso.'
            )
            return redirect('lista_colaboradores')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        user_form = CadastroColaboradorForm()
        perfil_form = PerfilColaboradorForm()

    return render(request, 'ponto/cadastrar_colaborador.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
    })


# ── Editar colaborador ───────────────────────────────────────────────────
@gestor_required
def editar_colaborador(request, user_id):
    colaborador = get_object_or_404(User, pk=user_id)
    perfil, _ = Perfil.objects.get_or_create(usuario=colaborador)

    if request.method == 'POST':
        user_form = EditarUsuarioForm(request.POST, instance=colaborador)
        perfil_form = EditarPerfilForm(request.POST, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, 'Colaborador atualizado com sucesso.')
            return redirect('lista_colaboradores')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        user_form = EditarUsuarioForm(instance=colaborador)
        perfil_form = EditarPerfilForm(instance=perfil)

    return render(request, 'ponto/editar_colaborador.html', {
        'colaborador': colaborador,
        'user_form': user_form,
        'perfil_form': perfil_form,
    })


# ── Primeiro acesso ──────────────────────────────────────────────────────
@login_required
def primeiro_acesso(request):
    try:
        if not request.user.perfil.primeiro_acesso:
            return redirect('bater_ponto')
    except Perfil.DoesNotExist:
        return redirect('bater_ponto')

    if request.method == 'POST':
        form = PrimeiroAcessoForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['senha'])
            request.user.save()
            request.user.perfil.primeiro_acesso = False
            request.user.perfil.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha definida com sucesso! Bem-vindo.')
            return redirect('bater_ponto')
    else:
        form = PrimeiroAcessoForm()

    return render(request, 'ponto/primeiro_acesso.html', {
        'form': form,
        'hide_chrome': True,
    })


# ── Meu perfil ───────────────────────────────────────────────────────────
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