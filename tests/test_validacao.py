import pytest

from portaria.validacao import (
    cpf_valido, mascarar_documento, normalizar_documento, normalizar_nome,
)

@pytest.mark.parametrize("entrada, esperado", [
    ("529.982.247-25", "52998224725"),
    (" 52998224725 ", "52998224725"),
    ("", ""),
    (None, ""),
])
def test_normalizar_documento(entrada, esperado):
    assert normalizar_documento(entrada) == esperado

@pytest.mark.parametrize("cpf, valido", [
    ("529.982.247-25", True),
    ("111.444.777-35", True),
    ("529.982.247-24", False),   # dígito verificador errado
    ("111.111.111-11", False),   # todos iguais
    ("1234567890", False),       # 10 dígitos
    ("", False),
])
def test_cpf_valido(cpf, valido):
    assert cpf_valido(cpf) is valido

def test_normalizar_nome_remove_espacos_extras():
    assert normalizar_nome("  Ana   Lima ") == "Ana Lima"

def test_mascarar_documento_exibe_apenas_miolo():
    assert mascarar_documento("52998224725") == "***.982.247-**"
    assert mascarar_documento("123") == "***"