from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil


class CadastroColaboradorForm(UserCreationForm):
    """
    Formulário usado pelo gestor para criar um novo colaborador.
    """
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label='Usuário (login)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Senha inicial',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2')


class PerfilColaboradorForm(forms.ModelForm):
    """
    Formulário usado pelo gestor para preencher os dados contratuais.
    """
    class Meta:
        model = Perfil
        fields = ('cargo', 'data_admissao', 'turno', 'valor_hora', 'jornada_diaria_horas')
        labels = {
            'cargo': 'Cargo',
            'data_admissao': 'Data de admissão',
            'turno': 'Turno',
            'valor_hora': 'Valor por hora (R$)',
            'jornada_diaria_horas': 'Jornada diária (horas)',
        }
        widgets = {
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_admissao': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'valor_hora': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01'}
            ),
            'jornada_diaria_horas': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PrimeiroAcessoForm(forms.Form):
    """
    Formulário preenchido pelo colaborador no primeiro acesso.
    """
    first_name = forms.CharField(
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Sobrenome',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    nova_senha = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirmar_senha = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('nova_senha')
        confirmacao = cleaned_data.get('confirmar_senha')

        if senha and confirmacao and senha != confirmacao:
            raise forms.ValidationError('As senhas não conferem.')

        return cleaned_data