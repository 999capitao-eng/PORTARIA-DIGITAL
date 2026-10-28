
import sqlite3

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
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
from portaria.validacao import (
    mascarar_documento,
    normalizar_documento,
)

COLUNAS = [
    "Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"
]

COLUNAS_HISTORICO = [
    "Visita", "Nome", "CPF", "Setor",
    "Crachá", "Entrada", "Saída", "Min."
]


def nova_tabela(colunas):
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabela.setSelectionMode(
        QAbstractItemView.SingleSelection
    )
    tabela.horizontalHeader().setSectionResizeMode(
        QHeaderView.Stretch
    )
    tabela.horizontalHeader().setSectionResizeMode(
        0, QHeaderView.ResizeToContents
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
        self.resize(1000, 600)

        abas = QTabWidget()
        abas.addTab(
            self.montar_aba_portaria(),
            "&Portaria",
        )
        abas.addTab(
            self.montar_aba_historico(),
            "&Histórico",
        )
        abas.currentChanged.connect(self.atualizar_tudo)

        self.setCentralWidget(abas)
        self.atualizar_tudo()

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
        self.tabela_historico = nova_tabela(
            COLUNAS_HISTORICO
        )
        self.resumo = QLabel()
        self.resumo.setWordWrap(True)

        botao_filtrar.clicked.connect(
            self.atualizar_historico
        )
        self.campo_busca.returnPressed.connect(
            self.atualizar_historico
        )
        self.data_inicio.dateChanged.connect(
            self.atualizar_historico
        )
        self.data_fim.dateChanged.connect(
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

    def carregar_setores(self):
        selecionado = self.combo_setor.currentData()

        self.combo_setor.clear()
        self.combo_setor.addItem(
            "Selecione um setor",
            None,
        )

        for setor in repo.listar_setores_ativos(self.conn):
            ocupacao = repo.contar_presentes_no_setor(
                self.conn,
                setor["id"],
            )
            self.combo_setor.addItem(
                f'{setor["nome"]} '
                f'({ocupacao}/{setor["lotacao_maxima"]})',
                setor["id"],
            )

        indice = self.combo_setor.findData(selecionado)
        self.combo_setor.setCurrentIndex(max(indice, 0))

    def buscar_visitante(self):
        cpf = normalizar_documento(
            self.campo_cpf.text()
        )

        visitante = repo.buscar_visitante_por_documento(
            self.conn,
            cpf,
        )

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
            self.mensagem.setText(
                "Selecione o setor de destino."
            )
            return

        try:
            cpf = normalizar_documento(documento)

            if repo.buscar_visitante_por_documento(
                self.conn,
                cpf,
            ) is None:
                servicos.cadastrar_visitante(
                    self.conn,
                    self.campo_nome.text(),
                    documento,
                )

            servicos.registrar_entrada(
                self.conn,
                documento,
                setor_id,
            )

        except RegraNegocioError as erro:
            self.mensagem.setText(str(erro))
            return

        except sqlite3.Error:
            QMessageBox.critical(
                self,
                "Portaria Digital",
                "Não foi possível registrar a entrada por "
                "um erro no banco de dados.",
            )
            return

        self.limpar_campos()
        self.mensagem.setText(
            "Entrada registrada. Confira o crachá na tabela."
        )
        self.atualizar_tudo()

    def registrar_saida(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            self.mensagem.setText(
                "Selecione uma visita na tabela."
            )
            return

        visita_id = int(
            self.tabela.item(linha, 0).text()
        )

        try:
            servicos.registrar_saida(
                self.conn,
                visita_id,
            )

        except RegraNegocioError as erro:
            self.mensagem.setText(str(erro))
            return

        except sqlite3.Error:
            QMessageBox.critical(
                self,
                "Portaria Digital",
                "Não foi possível registrar a saída por "
                "um erro no banco de dados.",
            )
            return

        self.mensagem.setText(
            "Saída registrada. Crachá devolvido."
        )
        self.atualizar_tudo()

    def atualizar_tudo(self, *_):
        try:
            self.carregar_setores()
            self.atualizar_tabela()
            self.atualizar_historico()
        except sqlite3.Error:
            QMessageBox.critical(
                self,
                "Portaria Digital",
                "Não foi possível atualizar os dados.",
            )

    def atualizar_tabela(self, *_):
        presentes = repo.listar_presentes(self.conn)
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
            if termo in (
                f'{l["nome"]} {l["setor"]}'.lower()
            )
        ]

        preencher_tabela(self.tabela, linhas)

        crachas = repo.contar_crachas_por_situacao(
            self.conn
        )
        self.contador.setText(
            f"No prédio: {len(presentes)} | "
            f"Crachás livres: "
            f'{crachas.get("disponivel", 0)}'
        )

    def atualizar_historico(self, *_):
        inicio = self.data_inicio.date().toString(
            "yyyy-MM-dd"
        )
        fim = self.data_fim.date().toString(
            "yyyy-MM-dd"
        )

        if inicio > fim:
            preencher_tabela(
                self.tabela_historico,
                [],
            )
            self.resumo.setText(
                "A data inicial não pode ser posterior "
                "à data final."
            )
            return

        linhas = repo.listar_historico(
            self.conn,
            inicio,
            fim,
            self.campo_busca.text(),
        )

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

        partes = []

        for r in repo.resumo_por_setor(
            self.conn,
            inicio,
            fim,
        ):
            texto = (
                f'{r["setor"]}: {r["visitas"]} visita(s)'
            )

            if r["media_minutos"] is not None:
                texto += (
                    f', média de {r["media_minutos"]} min'
                )

            partes.append(texto)

        self.resumo.setText(
            "Resumo do período. "
            + "; ".join(partes)
        )

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()
