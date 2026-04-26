# Ponto Digital

Sistema web de controle de ponto eletrônico voltado para pequenas empresas, desenvolvido como **Projeto Integrador (PI)** na **UNIVESP**.  
Permite registrar entradas e saídas dos colaboradores, controlar jornada diária e histórico de registros, com autenticação de usuários e gestão de perfis.

---

## 🔎 Objetivo do Projeto

Este projeto tem como objetivo oferecer uma solução simples e acessível de **controle de ponto eletrônico** para empresas de pequeno porte, com foco em:

- Registrar automaticamente **entrada** e **saída** dos colaboradores;
- Garantir integridade dos registros com fluxo **E-S-E-S**;
- Facilitar o acompanhamento da jornada diária e histórico de pontos;
- Oferecer controle de acesso diferenciado entre **colaboradores** e **gestores**;
- Servir como estudo de caso prático para o **Projeto Integrador**.

---

## 🏗️ Arquitetura e Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Django 4.2 |
| Banco de Dados | PostgreSQL (Heroku Postgres) |
| Deploy | Heroku |
| Autenticação | Django Auth |
| Armazenamento de Imagens | Cloudinary |
| Front-end | HTML, CSS, Bootstrap, Templates Django |
| Arquivos Estáticos | Whitenoise |
| Servidor WSGI | Gunicorn |

---

## ⚙️ Funcionalidades

### Autenticação e Segurança
- Login de usuários (colaboradores e gestores)
- Controle de **primeiro acesso**: ao acessar o sistema pela primeira vez, o colaborador é obrigado a definir uma senha própria antes de continuar

### Gestão de Colaboradores (Gestor)
- Cadastro de novos colaboradores
- Definição de cargo, turno, jornada diária e valor por hora
- Listagem de colaboradores ativos

### Controle de Ponto
- Tela de **Bater Ponto** com lógica automática **E-S-E-S**:
  - O sistema identifica automaticamente se o próximo registro é uma Entrada ou Saída
- Registro de data e hora com precisão

### Jornada e Histórico
- Cálculo automático da jornada diária
- Histórico de registros por colaborador
- Visualização dos pontos registrados por dia

### Perfil do Usuário
- Edição de dados pessoais
- Upload e visualização de foto de perfil (armazenada no Cloudinary)

---

## 📂 Estrutura do Projeto

```text
ponto-digital/
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ponto/
│   ├── models.py        # Perfil, RegistroPonto, JornadaDiaria
│   ├── views.py         # Bater ponto, cadastro, perfil, histórico, etc.
│   ├── urls.py
│   └── templates/
│       └── ponto/
├── static/
│   └── css/
├── manage.py
├── Procfile
├── .python-version
└── requirements.txt
```

---

## 💻 Como Rodar Localmente

### Pré-requisitos

- Python 3.12+
- Git
- Virtualenv (recomendado)

### 1. Clonar o repositório

```bash
git clone https://github.com/r-gabriel/ponto-digital.git
cd ponto-digital
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
export SECRET_KEY='sua_chave_secreta'
export DEBUG=True
export ALLOWED_HOSTS='localhost,127.0.0.1'

# Banco de dados (opcional, usa SQLite se não definido)
export DATABASE_URL='postgres://usuario:senha@localhost:5432/ponto_digital'

# Cloudinary (opcional localmente)
export CLOUDINARY_CLOUD_NAME='seu_cloud_name'
export CLOUDINARY_API_KEY='sua_api_key'
export CLOUDINARY_API_SECRET='seu_api_secret'
```

### 5. Aplicar migrations e criar superusuário

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Rodar o servidor

```bash
python manage.py runserver
```

Acesse em: `http://localhost:8000`

---

## 🚀 Deploy no Heroku

### 1. Criar o app e o banco de dados

```bash
heroku create nome-do-app
heroku addons:create heroku-postgresql:essential-0 --app nome-do-app
```

### 2. Configurar variáveis de ambiente

```bash
heroku config:set SECRET_KEY='sua_chave_secreta' --app nome-do-app
heroku config:set DEBUG=False --app nome-do-app
heroku config:set ALLOWED_HOSTS='nome-do-app.herokuapp.com' --app nome-do-app

heroku config:set CLOUDINARY_CLOUD_NAME='seu_cloud_name' --app nome-do-app
heroku config:set CLOUDINARY_API_KEY='sua_api_key' --app nome-do-app
heroku config:set CLOUDINARY_API_SECRET='seu_api_secret' --app nome-do-app
```

### 3. Fazer o deploy

```bash
git push heroku main
```

### 4. Criar superusuário no Heroku

```bash
heroku run python manage.py createsuperuser --app nome-do-app
```

---

## 👥 Perfis de Usuário

### Colaborador
- Faz login no sistema
- No primeiro acesso é obrigado a definir uma senha própria
- Pode bater ponto, visualizar histórico e editar o perfil

### Gestor
- Todas as funcionalidades do colaborador
- Cadastra e gerencia colaboradores
- Visualiza lista de colaboradores com seus dados de jornada

---

## 🔐 Lógica de Primeiro Acesso

Quando um colaborador é cadastrado pelo gestor:
- Se **sem senha inicial**: `primeiro_acesso = True` → ao logar, é redirecionado para definir a própria senha
- Se **com senha inicial**: `primeiro_acesso = False` → acessa normalmente

Após definir a senha, `primeiro_acesso` é marcado como `False` e o colaborador é redirecionado para a tela de bater ponto.

---

## 📷 Armazenamento de Fotos (Cloudinary)

O Heroku utiliza um filesystem efêmero, ou seja, arquivos enviados são perdidos a cada novo deploy. Para contornar isso, as fotos de perfil são armazenadas no **Cloudinary**:

- Pacotes utilizados: `cloudinary` e `django-cloudinary-storage`
- Configuração no `settings.py`:

```python
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

---

## 🧰 Principais Comandos

```bash
# Rodar servidor local
python manage.py runserver

# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Ver logs no Heroku
heroku logs --tail --app nome-do-app
```

---

## ✅ Status do Projeto

- [x] Controle de ponto com lógica E-S-E-S
- [x] Gestão de colaboradores
- [x] Controle de primeiro acesso com troca de senha obrigatória
- [x] Upload de foto de perfil com Cloudinary
- [x] Deploy no Heroku com PostgreSQL
- [ ] Reconhecimento facial (planejado para implementação futura)
- [ ] Relatórios e dashboards gerenciais

---

## 👨‍💻 Autor

- **Nome**: Grupo 6
- **Instituição**: UNIVESP
- **Projeto**: Projeto Integrador I 

---

## 📄 Licença

Este projeto é de uso acadêmico.