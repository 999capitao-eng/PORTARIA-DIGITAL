
from portaria import repositorio as repo
from portaria.erros import RegraNegocioError
from portaria.validacao import normalizar_documento, normalizar_nome


# ---------- visitantes ----------

def cadastrar_visitante(conn, nome: str, documento: str) -> int:
    """Cadastra um visitante após validar os dados."""
    nome = normalizar_nome(nome)
    documento = normalizar_documento(documento)

    if not nome:
        raise RegraNegocioError("Informe o nome do visitante.")

    visitante = repo.buscar_visitante_por_documento(conn, documento)
    if visitante is not None:
        return visitante["id"]

    with conn:
        return repo.inserir_visitante(conn, nome, documento)


# ---------- visitas ----------

def registrar_entrada(conn, documento: str, setor_id: int) -> int:
    """Registra a entrada e associa um crachá disponível."""
    documento = normalizar_documento(documento)

    visitante = repo.buscar_visitante_por_documento(conn, documento)
    if visitante is None:
        raise RegraNegocioError(
            "Visitante não cadastrado. Informe o nome e cadastre-o primeiro."
        )

    visitante_id = visitante["id"]

    aberta = repo.buscar_visita_aberta_por_visitante(conn, visitante_id)
    if aberta is not None:
        raise RegraNegocioError(
            f"{visitante['nome']} já está no prédio. Registre a saída antes."
        )

    setor = next(
        (s for s in repo.listar_setores_ativos(conn) if s["id"] == setor_id),
        None,
    )
    if setor is None:
        raise RegraNegocioError("O setor selecionado não existe ou está inativo.")

    ocupacao = repo.contar_presentes_no_setor(conn, setor_id)
    if ocupacao >= setor["lotacao_maxima"]:
        raise RegraNegocioError(
            f"O setor {setor['nome']} atingiu sua lotação máxima."
        )

    cracha = repo.buscar_cracha_disponivel(conn)
    if cracha is None:
        raise RegraNegocioError(
            "Não há crachá disponível. Aguarde uma devolução."
        )

    with conn:
        visita_id = repo.inserir_visita(
            conn,
            visitante_id,
            setor_id,
            cracha["id"],
        )
        repo.atualizar_situacao_cracha(conn, cracha["id"], "em_uso")

    return visita_id


def registrar_saida(conn, visita_id: int) -> None:
    """Encerra uma visita e devolve o crachá na mesma transação."""
    visita = repo.buscar_visita_aberta_por_id(conn, visita_id)

    if visita is None:
        raise RegraNegocioError("Esta visita já foi encerrada ou não existe.")

    with conn:
        repo.encerrar_visita(conn, visita_id)
        repo.atualizar_situacao_cracha(
            conn,
            visita["cracha_id"],
            "disponivel",
        )


# ---------- setores ----------

def salvar_setor(
    conn,
    nome: str,
    lotacao_maxima: int,
    ativo: bool = True,
    setor_id: int | None = None,
) -> int:
    """Cria ou altera um setor, aplicando as regras de cadastro."""
    nome = normalizar_nome(nome)

    if not nome:
        raise RegraNegocioError("Informe o nome do setor.")

    if lotacao_maxima < 1:
        raise RegraNegocioError(
            "A lotação máxima precisa ser de pelo menos 1 visitante."
        )

    # Comparação em Python para tratar corretamente letras acentuadas.
    for setor in repo.listar_setores(conn):
        if (
            setor["nome"].casefold() == nome.casefold()
            and setor["id"] != setor_id
        ):
            raise RegraNegocioError(
                f"Já existe o setor {setor['nome']}."
            )

    with conn:
        if setor_id is None:
            return repo.inserir_setor(conn, nome, lotacao_maxima)

        presentes = repo.contar_presentes_no_setor(conn, setor_id)

        if lotacao_maxima < presentes:
            raise RegraNegocioError(
                f"Há {presentes} visitante(s) no setor agora. "
                "A lotação não pode ficar abaixo disso."
            )

        if not ativo and presentes:
            raise RegraNegocioError(
                "Não é possível desativar um setor com visitantes no prédio."
            )

        repo.atualizar_setor(
            conn,
            setor_id,
            nome,
            lotacao_maxima,
            ativo,
        )

        return setor_id


def excluir_setor(conn, setor_id: int) -> None:
    """Impede excluir setores que tenham histórico de visitas."""
    with conn:
        if repo.contar_visitas_do_setor(conn, setor_id):
            raise RegraNegocioError(
                "Este setor tem histórico de visitas e não pode ser excluído. "
                "Desative-o."
            )

        repo.excluir_setor(conn, setor_id)
