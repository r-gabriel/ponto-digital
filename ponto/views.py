from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from django.http import HttpResponse
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction

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

            # Pega o último registro do usuário
            ultimo = RegistroPonto.objects.filter(
                funcionario=request.user
            ).order_by('-data_hora').first()

            # Valida a ordem E-S-E-S
            if tipo == 'E' and ultimo and ultimo.tipo == 'E':
                messages.error(request, 'Você já registrou uma entrada. Registre a saída antes.')
                return redirect('bater_ponto')

            if tipo == 'S' and (not ultimo or ultimo.tipo == 'S'):
                messages.error(request, 'Você precisa registrar uma entrada antes de registrar a saída.')
                return redirect('bater_ponto')

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

    # GET — busca último registro para exibir no template
    ultimo = (
        RegistroPonto.objects
        .filter(funcionario=request.user)
        .order_by('-data_hora')
        .first()
    )

    if ultimo:
        proximo_tipo = 'S' if ultimo.tipo == 'E' else 'E'
    else:
        proximo_tipo = 'E'

    return render(request, 'ponto/bater_ponto.html', {
        'ultimo': ultimo,
        'proximo_tipo': proximo_tipo,
    })


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
            try:
                with transaction.atomic():
                    # cria o usuário
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
                    # neste ponto o signal já pode ter criado o Perfil

                    # pega o perfil existente (criado pelo signal) ou cria se não existir
                    perfil, _ = Perfil.objects.get_or_create(usuario=user)

                    # aplica os dados do formulário no perfil
                    perfil.cargo = perfil_form.cleaned_data.get('cargo', '')
                    perfil.data_admissao = perfil_form.cleaned_data.get('data_admissao')
                    perfil.turno = perfil_form.cleaned_data.get('turno', '')
                    perfil.valor_hora = perfil_form.cleaned_data.get('valor_hora')
                    perfil.jornada_diaria_horas = perfil_form.cleaned_data.get('jornada_diaria_horas', 8)
                    perfil.primeiro_acesso = primeiro_acesso
                    perfil.save()

                messages.success(
                    request,
                    f'Colaborador "{user.get_full_name() or user.username}" '
                    f'cadastrado com sucesso.'
                )
                return redirect('lista_colaboradores')

            except Exception as e:
                messages.error(request, f'Erro ao cadastrar: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros destacados abaixo.')
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

@gestor_required
def exportar_relatorio_pdf(request):
    funcionario_id = request.GET.get('funcionario', '')
    data_inicial   = request.GET.get('data_inicial', '')
    data_final     = request.GET.get('data_final', '')

    if not (funcionario_id and data_inicial and data_final):
        messages.error(request, 'Preencha todos os filtros antes de exportar o PDF.')
        return redirect('relatorio_jornadas')

    try:
        funcionario = User.objects.get(pk=funcionario_id)
    except User.DoesNotExist:
        messages.error(request, 'Funcionário não encontrado.')
        return redirect('relatorio_jornadas')

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
    total_intervalo  = timedelta()
    total_extras     = timedelta()

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

    # Monta o PDF em memória
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'titulo',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    estilo_subtitulo = ParagraphStyle(
        'subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=colors.grey,
    )

    estilo_rodape = ParagraphStyle(
        'rodape',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT,
        textColor=colors.grey,
    )

    nome_funcionario = funcionario.get_full_name() or funcionario.username

    elementos = []

    # Cabeçalho
    elementos.append(Paragraph('Ponto Digital — UNIVESP', estilo_titulo))
    elementos.append(Paragraph('Relatório de Jornadas', estilo_subtitulo))
    elementos.append(Paragraph(
        f'Colaborador: <b>{nome_funcionario}</b> &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'Período: <b>{data_inicial} a {data_final}</b>',
        estilo_subtitulo
    ))
    elementos.append(Spacer(1, 0.5 * cm))

    # Cabeçalho da tabela
    cabecalho = ['Data', 'Trabalhado', 'Intervalo', 'Horas Extras']

    linhas = [cabecalho]

    for j in jornadas:
        extras_str = j.horas_extras_fmt
        tem_extra  = j.horas_extras and j.horas_extras.total_seconds() > 0

        linhas.append([
            j.data.strftime('%d/%m/%Y'),
            j.total_trabalhado_fmt,
            j.total_intervalo_fmt,
            extras_str if tem_extra else '—',
        ])

    # Linha de totais
    linhas.append([
        'TOTAL',
        fmt(total_trabalhado),
        fmt(total_intervalo),
        fmt(total_extras),
    ])

    tabela = Table(
        linhas,
        colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm],
        repeatRows=1,
    )

    tabela.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  10),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  8),
        ('TOPPADDING',    (0, 0), (-1, 0),  8),

        # Linhas de dados
        ('FONTNAME',      (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -2), 9),
        ('ALIGN',         (0, 1), (-1, -2), 'CENTER'),
        ('ROWBACKGROUNDS',(0, 1), (-1, -2), [colors.white, colors.HexColor('#f2f2f2')]),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
        ('TOPPADDING',    (0, 1), (-1, -2), 6),

        # Linha de totais
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, -1), (-1, -1), colors.white),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, -1), (-1, -1), 9),
        ('ALIGN',         (0, -1), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),

        # Grid geral
        ('GRID',          (0, 0),  (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('BOX',           (0, 0),  (-1, -1), 0.8, colors.HexColor('#2c3e50')),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 0.5 * cm))

    # Rodapé
    from django.utils.timezone import localtime, now
    gerado_em = localtime(now()).strftime('%d/%m/%Y às %H:%M')
    elementos.append(Paragraph(
        f'Relatório gerado em {gerado_em} por {request.user.get_full_name() or request.user.username}.',
        estilo_rodape
    ))

    doc.build(elementos)

    buffer.seek(0)

    nome_arquivo = (
        f'relatorio_{funcionario.username}_'
        f'{data_inicial}_a_{data_final}.pdf'
    )

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    return response
