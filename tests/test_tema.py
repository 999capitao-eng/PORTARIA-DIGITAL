import re
from pathlib import Path

import pytest

from portaria.ui.tema import TEMAS, contraste, gerar_folha

def test_temas_definem_os_mesmos_tokens():
    for nome, cores in TEMAS.items():
        assert cores.keys() == TEMAS["claro"].keys(), nome

def test_folha_gerada_nao_deixa_marcador_sem_valor():
    for nome in TEMAS:
        assert "$" not in gerar_folha(nome)

def test_icones_referenciados_existem():
    for nome in TEMAS:
        for caminho in re.findall(r'url\("([^"]+)"\)', gerar_folha(nome)):
            assert Path(caminho).exists(), caminho

PARES_DE_TEXTO = [
    ("texto", "superficie"), ("texto", "fundo"), ("texto_suave", "superficie"),
    ("primaria_texto", "primaria"), ("primaria_texto", "primaria_hover"),
    ("perigo", "superficie"), ("perigo_texto", "perigo"), ("aviso_texto", "aviso_fundo"),
    ("texto", "zebra"), ("texto", "selecao"),
]

@pytest.mark.parametrize("nome_tema", list(TEMAS))
def test_cores_de_texto_tem_contraste_minimo(nome_tema):
    """WCAG 2.x: texto normal precisa de contraste de pelo menos 4,5:1."""
    cores = TEMAS[nome_tema]
    for texto, fundo in PARES_DE_TEXTO:
        assert contraste(cores[texto], cores[fundo]) >= 4.5, (texto, fundo)