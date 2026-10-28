def listar_historico(conn, inicio: str, fim: str, termo: str = "") -> list[Linha]:
    """Visitas com entrada no intervalo [inicio, fim], filtrando por nome ou setor."""
    padrao = f"%{termo.strip()}%"  # o curinga vai no PARÂMETRO, não no SQL
    return conn.execute(
        """
        SELECT v.id, p.nome, p.documento, s.nome AS setor, c.codigo AS cracha,
               v.entrada, v.saida,
               CAST(ROUND((julianday(v.saida) - julianday(v.entrada)) * 1440) AS INTEGER)
                   AS minutos
          FROM visita v
          JOIN visitante p ON p.id = v.visitante_id
          JOIN setor s     ON s.id = v.setor_id
          JOIN cracha c    ON c.id = v.cracha_id
         WHERE date(v.entrada) BETWEEN ? AND ?
           AND (p.nome LIKE ? OR s.nome LIKE ?)
         ORDER BY v.entrada DESC
        """,
        (inicio, fim, padrao, padrao),
    ).fetchall()

def resumo_por_setor(conn, inicio: str, fim: str) -> list[Linha]:
    return conn.execute(
        """
        SELECT s.nome AS setor, COUNT(v.id) AS visitas,
               ROUND(AVG((julianday(v.saida) - julianday(v.entrada)) * 1440), 1)
                   AS media_minutos
          FROM setor s
          LEFT JOIN visita v
                 ON v.setor_id = s.id AND date(v.entrada) BETWEEN ? AND ?
         GROUP BY s.id
         ORDER BY visitas DESC, s.nome
        """,
        (inicio, fim),
    ).fetchall()

def listar_setores(conn) -> list[Linha]:
    """Todos os setores, inclusive os inativos, para a tela de gestão."""
    return conn.execute(
        """
        SELECT s.id, s.nome, s.lotacao_maxima, s.ativo,
               COUNT(v.id) AS total_visitas
          FROM setor s
          LEFT JOIN visita v ON v.setor_id = s.id
         GROUP BY s.id
         ORDER BY s.nome
        """
    ).fetchall()

def inserir_setor(conn, nome: str, lotacao_maxima: int) -> int:
    cur = conn.execute(
        "INSERT INTO setor (nome, lotacao_maxima) VALUES (?, ?)", (nome, lotacao_maxima)
    )
    return cur.lastrowid

def atualizar_setor(conn, setor_id: int, nome: str, lotacao_maxima: int, ativo: bool) -> None:
    conn.execute(
        "UPDATE setor SET nome = ?, lotacao_maxima = ?, ativo = ? WHERE id = ?",
        (nome, lotacao_maxima, int(ativo), setor_id),
    )

def excluir_setor(conn, setor_id: int) -> None:
    conn.execute("DELETE FROM setor WHERE id = ?", (setor_id,))

def contar_visitas_do_setor(conn, setor_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM visita WHERE setor_id = ?", (setor_id,)
    ).fetchone()[0]