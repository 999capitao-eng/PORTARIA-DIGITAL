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