from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def gestor_required(view_func):
    """
    Restringe o acesso à view apenas para usuários
    do grupo 'Gestor' ou superusuários.
    Retorna 403 se o usuário estiver logado mas não tiver permissão.
    """
    def check_gestor(user):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name='Gestor').exists()

    decorated = user_passes_test(
        check_gestor,
        login_url='login',
    )(view_func)

    return decorated