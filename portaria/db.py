import sqlite3
from pathlib import Path

ESQUEMA = Path(__file__).with_name("schema.sql")

def conectar(caminho="portaria.db"):
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row             # acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")   # vale por conexão
    return conn

def preparar_banco(conn):
    conn.executescript(ESQUEMA.read_text(encoding="utf-8"))
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO setor (nome, lotacao_maxima) VALUES (?, ?)",
            [("Secretaria", 5), ("Coordenação", 3), ("Laboratório", 10)],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO cracha (codigo) VALUES (?)",
            [(f"V-{n:02d}",) for n in range(1, 11)],
        )
Path(__file__).with_name("schema.sql")
→ acha o esquema ao lado de db.py, de onde quer que o programa seja aberto

row_factory = sqlite3.Row
→ linha["nome"] em vez de linha[1]

PRAGMA foreign_keys = ON
→ no SQLite, chaves estrangeiras vêm DESLIGADAS; é preciso ligar em cada conexão

executescript
→ executa vários comandos SQL de uma vez (o esquema inteiro)

INSERT OR IGNORE
→ não duplica setores e crachás quando o programa abre de novo