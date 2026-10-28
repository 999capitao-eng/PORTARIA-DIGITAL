import pytest

from portaria.db import conectar, preparar_banco

# CPFs fictícios com dígitos verificadores válidos, usados só nos testes.
CPF_A = "52998224725"
CPF_B = "11144477735"

@pytest.fixture
def conn():
    """Banco em memória, novo a cada teste: um teste não interfere no outro."""
    c = conectar(":memory:")
    preparar_banco(c)
    yield c
    c.close()

@pytest.fixture
def secretaria(conn):
    return conn.execute("SELECT id FROM setor WHERE nome = 'Secretaria'").fetchone()["id"]

@pytest.fixture
def coordenacao(conn):
    return conn.execute("SELECT id FROM setor WHERE nome = 'Coordenação'").fetchone()["id"]