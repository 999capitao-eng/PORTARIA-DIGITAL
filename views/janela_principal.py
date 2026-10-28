
import logging
import sqlite3

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from portaria import repositorio as repo
from portaria import servicos
from portaria.erros import RegraNegocioError
from portaria.ui.dialogo_setor import DialogoSetor
from portaria.validacao import (
    mascarar_documento,
    normalizar_documento,
)

log = logging.getLogger(__name__)
FALHA = object()

COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]

COLUNAS_HISTORICO = [
    "Visita", "Nome", "CPF", "Setor", "Crachá",
    "Entrada", "Saída", "Min."
]

COLUNAS_SETORES = [
    "Código", "Setor", "Lotação", "Situação", "Visitas registradas"
]


def nova_tabela(colunas):
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )
    tabela.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows
    )
    tabela.setSelectionMode(
        QAbstractItemView.SelectionMode.SingleSelection
    )
    tabela.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.Stretch
    )
    tabela.horizontalHeader().setSectionResizeMode(
        0, QHeaderView.ResizeMode.ResizeToContents
    )
    tabela.verticalHeader().setVisible(False)
    return tabela


def preencher_tabela(tabela, linhas):
    tabela.setRowCount(len(linhas))

    for i, valores in enumerate(linhas):
        for j, valor in enumerate(valores):
            tabela.setItem(
                i,
                j,
                QTableWidgetItem(
                    "" if valor is None else str(valor)
                ),
            )

    tabela.setCurrentCell(-1, -1)


class JanelaPrincipal(QMainWindow):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Portaria Digital")
        self.resize(1000, 650)

        abas = QTabWidget()
        abas.addTab(self.montar_aba_portaria(), "&Portaria")
        abas.addTab(self.montar_aba_historico(), "&Histórico")
        abas.addTab(self.montar_aba_setores(), "Se&tores")
        abas.currentChanged.connect(self.atualizar_tudo)

        self.setCentralWidget(abas)
        self.statusBar().showMessage("Sistema iniciado.", 5000)

        self.atualizar_tudo()

    # ---------- Aba Portaria ----------

    def montar_aba_portaria(self):
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)

        self.campo_nome = QLineEdit()
        self.combo_setor = QComboBox()

        self.botao_entrada = QPushButton("Registrar entrada")
        self.botao_limpar = QPushButton("Limpar campos")
        self.mensagem = QLabel("Informe o CPF do visitante.")

        formulario = QFormLayout()
        formulario.addRow("CPF:", self.campo_cpf)
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Setor:", self.combo_setor)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_entrada)
        botoes.addWidget(self.botao_limpar)

        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText(
            "Filtrar por nome ou setor"
        )

        self.tabela = nova_tabela(COLUNAS)
        self.botao_saida = QPushButton(
            "Registrar saída da visita selecionada"
        )
        self.contador = QLabel()

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addLayout(botoes)
        layout.addWidget(self.mensagem)
        layout.addWidget(QLabel("No prédio agora:"))
        layout.addWidget(self.campo_filtro)
        layout.addWidget(self.tabela)
        layout.addWidget(self.botao_saida)
        layout.addWidget(self.contador)

        self.campo_cpf.editingFinished.connect(
            self.buscar_visitante
        )
        self.botao_entrada.clicked.connect(
            self.registrar_entrada
        )
        self.botao_limpar.clicked.connect(
            self.limpar_campos
        )
        self.botao_saida.clicked.connect(
            self.registrar_saida
        )
        self.campo_filtro.textChanged.connect(
            self.atualizar_tabela
        )

        aba = QWidget()
        aba.setLayout(layout)
        return aba

    # ---------- Aba Histórico ----------

    def montar_aba_historico(self):
        hoje = QDate.currentDate()

        self.data_inicio = QDateEdit(hoje.addDays(-7))
        self.data_fim = QDateEdit(hoje)

        for campo in (self.data_inicio, self.data_fim):
            campo.setCalendarPopup(True)
            campo.setDisplayFormat("dd/MM/yyyy")

        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Nome ou setor")

        botao_filtrar = QPushButton("&Filtrar")
        self.tabela_historico = nova_tabela(COLUNAS_HISTORICO)
        self.resumo = QLabel()
        self.resumo.setWordWrap(True)

        botao_filtrar.clicked.connect(self.atualizar_historico)
        self.campo_busca.returnPressed.connect(
            self.atualizar_historico
        )

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("De:"))
        filtros.addWidget(self.data_inicio)
        filtros.addWidget(QLabel("Até:"))
        filtros.addWidget(self.data_fim)
        filtros.addWidget(self.campo_busca, 1)
        filtros.addWidget(botao_filtrar)

        layout = QVBoxLayout()
        layout.addLayout(filtros)
        layout.addWidget(self.tabela_historico)
        layout.addWidget(self.resumo)

        aba = QWidget()
        aba.setLayout(layout)
        return aba

    # ---------- Aba Setores ----------

    def montar_aba_setores(self):
        self.tabela_setores = nova_tabela(COLUNAS_SETORES)
        self._setores = []

        botao_novo = QPushButton("&Novo setor")
        botao_editar = QPushButton("E&ditar selecionado")
        botao_excluir = QPushButton("E&xcluir selecionado")

        botao_novo.clicked.connect(self.novo_setor)
        botao_editar.clicked.connect(self.editar_setor)
        botao_excluir.clicked.connect(self.excluir_setor)
        self.tabela_setores.doubleClicked.connect(
            self.editar_setor
        )

        botoes = QHBoxLayout()
        botoes.addWidget(botao_novo)
        botoes.addWidget(botao_editar)
        botoes.addWidget(botao_excluir)
        botoes.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(botoes)
        layout.addWidget(self.tabela_setores)

        aba = QWidget()
        aba.setLayout(layout)
        return aba

    def atualizar_setores(self):
        setores = self._executar(repo.listar_setores, self.conn)

        if setores is FALHA:
            return

        self._setores = setores

        preencher_tabela(
            self.tabela_setores,
            [
                [
                    s["id"],
                    s["nome"],
                    s["lotacao_maxima"],
                    "Ativo" if s["ativo"] else "Inativo",
                    s["total_visitas"],
                ]
                for s in setores
            ],
        )

    def setor_selecionado(self):
        linha = self.tabela_setores.currentRow()

        if linha < 0:
            self._avisar("Selecione um setor na tabela.")
            return None

        setor_id = int(self.tabela_setores.item(linha, 0).text())

        return next(
            (s for s in self._setores if s["id"] == setor_id),
            None,
        )

    def novo_setor(self):
        dialogo = DialogoSetor(self)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            resultado = self._executar(
                servicos.salvar_setor,
                self.conn,
                dados["nome"],
                dados["lotacao_maxima"],
            )

            if resultado is not FALHA:
                self.atualizar_tudo()

    def editar_setor(self):
        setor = self.setor_selecionado()

        if setor is None:
            return

        dialogo = DialogoSetor(self, setor)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            resultado = self._executar(
                servicos.salvar_setor,
                self.conn,
                dados["nome"],
                dados["lotacao_maxima"],
                dados["ativo"],
                setor["id"],
            )

            if resultado is not FALHA:
                self.atualizar_tudo()

    def excluir_setor(self):
        setor = self.setor_selecionado()

        if setor is None:
            return

        resposta = QMessageBox.question(
            self,
            "Portaria Digital",
            f"Excluir o setor {setor['nome']}?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        resultado = self._executar(
            servicos.excluir_setor,
            self.conn,
            setor["id"],
        )

        if resultado is not FALHA:
            self.atualizar_tudo()

    # ---------- Visitantes e visitas ----------

    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())

        visitante = self._executar(
            repo.buscar_visitante_por_documento,
            self.conn,
            cpf,
        )

        if visitante is FALHA:
            return

        if visitante:
            self.campo_nome.setText(visitante["nome"])
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText(
                "Visitante já cadastrado. Escolha o setor."
            )
        else:
            self.campo_nome.setReadOnly(False)

    def registrar_entrada(self):
        documento = self.campo_cpf.text()
        setor_id = self.combo_setor.currentData()

        if setor_id is None:
            self._avisar("Selecione o setor de destino.")
            return

        def operacao():
            cpf = normalizar_documento(documento)

            if repo.buscar_visitante_por_documento(
                self.conn, cpf
            ) is None:
                servicos.cadastrar_visitante(
                    self.conn,
                    self.campo_nome.text(),
                    documento,
                )

            return servicos.registrar_entrada(
                self.conn,
                documento,
                setor_id,
            )

        if self._executar(operacao) is FALHA:
            self.mensagem.setText(
                "Entrada não registrada. Corrija os dados e tente novamente."
            )
            return

        self.limpar_campos()
        self.mensagem.setText(
            "Entrada registrada. Entregue o crachá indicado na tabela."
        )
        self.atualizar_tudo()

    def registrar_saida(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            self._avisar("Selecione uma visita na tabela.")
            return

        visita_id = int(self.tabela.item(linha, 0).text())

        resultado = self._executar(
            servicos.registrar_saida,
            self.conn,
            visita_id,
        )

        if resultado is not FALHA:
            self.mensagem.setText(
                "Saída registrada. Crachá devolvido."
            )
            self.atualizar_tudo()

    # ---------- Atualização das telas ----------

    def atualizar_tudo(self, *_):
        self.carregar_setores()
        self.atualizar_tabela()
        self.atualizar_historico()
        self.atualizar_setores()

    def carregar_setores(self):
        setores = self._executar(
            repo.listar_setores_ativos,
            self.conn,
        )

        if setores is FALHA:
            return

        selecionado = self.combo_setor.currentData()
        self.combo_setor.clear()
        self.combo_setor.addItem("Selecione um setor", None)

        for setor in setores:
            ocupacao = self._executar(
                repo.contar_presentes_no_setor,
                self.conn,
                setor["id"],
            )

            if ocupacao is FALHA:
                return

            self.combo_setor.addItem(
                f"{setor['nome']} ({ocupacao}/{setor['lotacao_maxima']})",
                setor["id"],
            )

        self.combo_setor.setCurrentIndex(
            max(self.combo_setor.findData(selecionado), 0)
        )

    def atualizar_tabela(self):
        presentes = self._executar(
            repo.listar_presentes,
            self.conn,
        )

        if presentes is FALHA:
            return

        termo = self.campo_filtro.text().strip().lower()

        linhas = [
            [
                l["id"],
                l["nome"],
                mascarar_documento(l["documento"]),
                l["setor"],
                l["cracha"],
                l["entrada"],
            ]
            for l in presentes
            if termo in f"{l['nome']} {l['setor']}".lower()
        ]

        preencher_tabela(self.tabela, linhas)

        crachas = self._executar(
            repo.contar_crachas_por_situacao,
            self.conn,
        )

        if crachas is FALHA:
            return

        self.contador.setText(
            f"No prédio: {len(presentes)} | "
            f"Crachás livres: {crachas.get('disponivel', 0)}"
        )

    def atualizar_historico(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd")
        fim = self.data_fim.date().toString("yyyy-MM-dd")

        linhas = self._executar(
            repo.listar_historico,
            self.conn,
            inicio,
            fim,
            self.campo_busca.text(),
        )

        if linhas is FALHA:
            return

        preencher_tabela(
            self.tabela_historico,
            [
                [
                    l["id"],
                    l["nome"],
                    mascarar_documento(l["documento"]),
                    l["setor"],
                    l["cracha"],
                    l["entrada"],
                    l["saida"] or "no prédio",
                    l["minutos"],
                ]
                for l in linhas
            ],
        )

        resumos = self._executar(
            repo.resumo_por_setor,
            self.conn,
            inicio,
            fim,
        )

        if resumos is FALHA:
            return

        partes = []

        for r in resumos:
            texto = f"{r['setor']}: {r['visitas']} visita(s)"

            if r["media_minutos"] is not None:
                texto += f", média de {r['media_minutos']} min"

            partes.append(texto)

        self.resumo.setText(
            "Resumo do período. " + "; ".join(partes)
        )

    # ---------- Campos e erros ----------

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()

    def _executar(self, funcao, *args):
        """Executa uma operação com tratamento centralizado de erros."""
        try:
            return funcao(*args)

        except RegraNegocioError as erro:
            self._avisar(str(erro))

        except sqlite3.Error:
            log.exception(
                "Falha de banco em %s",
                getattr(funcao, "__name__", "operação"),
            )

            QMessageBox.critical(
                self,
                "Portaria Digital",
                "Não foi possível acessar o banco de dados. "
                "Nenhuma alteração parcial foi gravada. "
                "Tente novamente ou avise o suporte.",
            )

        return FALHA

    def _avisar(self, texto):
        self.statusBar().showMessage(texto, 8000)
        QMessageBox.warning(
            self,
            "Portaria Digital",
            texto,
        )
