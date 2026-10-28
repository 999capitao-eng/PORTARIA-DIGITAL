import sqlite3

import pytest

from portaria import repositorio as repo
from portaria import servicos
from portaria.db import preparar_banco
from portaria.erros import RegraNegocioError
from portaria.ui.tema import TEMAS, gerar_folha


def cpf_de(base: str) -> str:
    d = [int(c) for c in base]
    for n in (9, 10):
        soma = sum(v * (n + 1 - i) for i, v in enumerate(d))
        d.append(soma * 10 % 11 % 10)
    return "".join(map(str, d))


BASES = ["123456789", "234567890", "345678901", "456789012"]
CPFS = [cpf_de(b) for b in BASES]


@pytest.fixture
def banco():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    preparar_banco(conn)
    yield conn
    conn.close()


def setor_id(conn, nome):
    return next(s["id"] for s in repo.listar_setores(conn) if s["nome"] == nome)


def test_setor_inativo_nao_aceita_entrada(banco):
    servicos.cadastrar_visitante(banco, "Ana Lima", CPFS[0])
    sid = setor_id(banco, "Secretaria")
    servicos.salvar_setor(banco, "Secretaria", 5, False, sid)
    with pytest.raises(RegraNegocioError):
        servicos.registrar_entrada(banco, CPFS[0], sid)


def test_cracha_devolvido_volta_a_ser_o_primeiro_disponivel(banco):
    sid = setor_id(banco, "Secretaria")
    servicos.cadastrar_visitante(banco, "Ana Lima", CPFS[0])
    servicos.cadastrar_visitante(banco, "Bruno Sousa", CPFS[1])
    primeira = servicos.registrar_entrada(banco, CPFS[0], sid)
    servicos.registrar_entrada(banco, CPFS[1], sid)
    servicos.registrar_saida(banco, primeira)
    assert repo.buscar_cracha_disponivel(banco)["codigo"] == "V-01"


def test_resumo_por_setor_lista_setores_sem_visitas(banco):
    linhas = repo.resumo_por_setor(banco, "2000-01-01", "2999-12-31")
    nomes = {l["setor"] for l in linhas}
    assert {"Secretaria", "Coordenação", "Laboratório"} <= nomes
    assert all(l["visitas"] == 0 for l in linhas)


def test_lotacao_do_setor_e_respeitada(banco):
    sid = setor_id(banco, "Coordenação")  # lotação 3
    for i in range(3):
        servicos.cadastrar_visitante(banco, f"Pessoa {i}", CPFS[i])
        servicos.registrar_entrada(banco, CPFS[i], sid)
    servicos.cadastrar_visitante(banco, "Pessoa 3", CPFS[3])
    with pytest.raises(RegraNegocioError):
        servicos.registrar_entrada(banco, CPFS[3], sid)


def test_mesma_semente_gera_os_mesmos_cpfs():
    dados = pytest.importorskip("dados_ficticios")
    if not hasattr(dados, "gerar_cpfs"):
        pytest.skip("gerar_cpfs não existe neste dados_ficticios.py")
    assert dados.gerar_cpfs(7, 5) == dados.gerar_cpfs(7, 5)
    assert dados.gerar_cpfs(7, 5) != dados.gerar_cpfs(8, 5)


@pytest.mark.parametrize("nome", list(TEMAS))
def test_folha_de_estilo_gera_para_todos_os_temas(nome):
    assert "$" not in gerar_folha(nome)


def test_tema_institucional_existe():
    assert "institucional" in TEMAS