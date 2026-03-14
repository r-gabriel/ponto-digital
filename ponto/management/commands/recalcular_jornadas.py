from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ponto.models import RegistroPonto, JornadaDiaria


class Command(BaseCommand):
    help = 'Recalcula todas as jornadas diárias com base nos registros de ponto existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Recalcular apenas para um usuário específico (username)',
        )

    def handle(self, *args, **options):
        username = options.get('usuario')

        if username:
            try:
                usuarios = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Usuário "{username}" não encontrado.'))
                return
        else:
            usuarios = User.objects.all()

        total = 0

        for usuario in usuarios:
            # Busca todas as datas únicas com registros desse usuário
            datas = (
                RegistroPonto.objects
                .filter(funcionario=usuario)
                .dates('data_hora', 'day')
            )

            for data in datas:
                jornada, _ = JornadaDiaria.objects.get_or_create(
                    funcionario=usuario,
                    data=data
                )
                jornada.calcular()
                total += 1
                self.stdout.write(
                    f'  Recalculado: {usuario.username} - {data}'
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nConcluído. {total} jornada(s) recalculada(s).')
        )