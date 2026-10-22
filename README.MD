
# Registro de Visitantes — Desktop

Aplicação didática de registro de visitantes com Python e PySide6.

Armazena registros somente em memória durante a execução.

## Requisitos

- Python 3
- PySide6

## Executar

1. Criar ambiente virtual:

   `python -m venv .venv`

2. Ativar o ambiente virtual:

   Windows PowerShell:

   `.venv\Scripts\Activate.ps1`

3. Instalar as dependências:

   `python -m pip install -r requirements.txt`

4. Executar a aplicação:

   `python main.py`

## Funcionalidades

- Registrar nome e setor
- Validar campos obrigatórios
- Listar visitas da sessão
- Limpar formulário e exibir contador

## Limitação

Sem banco de dados; os registros são perdidos ao encerrar.
