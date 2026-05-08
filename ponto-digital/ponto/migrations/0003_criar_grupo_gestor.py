from django.db import migrations


def criar_grupo(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Gestor')


def remover_grupo(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Gestor').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ponto', '0002_alter_registroponto_data_hora_jornadadiaria'),  # ajuste para o número da sua última migration
    ]

    operations = [
        migrations.RunPython(criar_grupo, remover_grupo),
    ]