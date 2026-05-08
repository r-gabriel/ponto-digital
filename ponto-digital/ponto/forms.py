from django import forms
from django.contrib.auth.models import User
from .models import Perfil


class CadastroColaboradorForm(forms.ModelForm):
    senha_inicial = forms.CharField(
        label='Senha inicial',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Deixe em branco para que o colaborador defina a senha no primeiro acesso.'
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'username': 'Usuário (login)',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                f'O usuário "{username}" já existe. Escolha outro nome de usuário.'
            )
        return username

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha_inicial')
        confirmar = cleaned.get('confirmar_senha')
        if senha or confirmar:
            if senha != confirmar:
                raise forms.ValidationError('As senhas não conferem.')
        return cleaned


class PerfilColaboradorForm(forms.ModelForm):
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
            'data_admissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jornada_diaria_horas': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class EditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'username': 'Usuário (login)',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EditarPerfilForm(forms.ModelForm):
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
            'data_admissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jornada_diaria_horas': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PrimeiroAcessoForm(forms.Form):
    senha = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        confirmar = cleaned.get('confirmar_senha')
        if senha and confirmar and senha != confirmar:
            raise forms.ValidationError('As senhas não conferem.')
        return cleaned


class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ('foto',)
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }