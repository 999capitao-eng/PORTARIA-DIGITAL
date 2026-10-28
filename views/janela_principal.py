from datetime import datetime

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from portaria.validacao import (
    cpf_valido,
    mascarar_documento,
    normalizar_documento,
)

SETORES = ["secretaria", "coordenação", "laboratório"]
CRACHAS = [f"V-{n:02d}" for n in range(1, 11)]
COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]


class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portaria Digital")
        self.resize(830, 520)

        self.visitantes = {}
        self.visitas = []
        self.crachas_livres = list(CRACHAS)
        self.proximo_id = 1

        # Formulário
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)

        self.campo_nome = QLineEdit()

        self.combo_setor = QComboBox()
        self.combo_setor.addItem("Selecionar um setor")
        self.combo_setor.addItems(SETORES)

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

        # Tabela de presentes
        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText(
            "Filtrar por nome ou setor"
        )

        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabela.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela.verticalHeader().setVisible(False)

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
        self.setLayout(layout)

        # Eventos
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

        self.atualizar_tabela()

    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())

        if cpf in self.visitantes:
            self.campo_nome.setText(self.visitantes[cpf])
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText(
                "Visitante já cadastrado. Escolha o setor."
            )
        else:
            self.campo_nome.setReadOnly(False)

    def registrar_entrada(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        nome = " ".join(self.campo_nome.text().split())

        if not cpf_valido(cpf):
            self.mensagem.setText(
                "CPF inválido. Confira os 11 dígitos."
            )
            self.campo_cpf.setFocus()
            return

        if not nome:
            self.mensagem.setText(
                "Informe o nome do visitante."
            )
            self.campo_nome.setFocus()
            return

        if self.combo_setor.currentIndex() == 0:
            self.mensagem.setText(
                "Selecione o setor de destino."
            )
            return

        if any(
            v["cpf"] == cpf for v in self.presentes()
        ):
            self.mensagem.setText(
                f"{nome} já está no prédio. "
                "Registre a saída antes."
            )
            return

        if not self.crachas_livres:
            self.mensagem.setText(
                "Não há crachá disponível. "
                "Aguarde uma devolução."
            )
            return

        self.visitantes.setdefault(cpf, nome)

        cracha = self.crachas_livres.pop(0)

        self.visitas.append({
            "id": self.proximo_id,
            "cpf": cpf,
            "setor": self.combo_setor.currentText(),
            "cracha": cracha,
            "entrada": datetime.now().strftime("%H:%M:%S"),
            "saida": None,
        })

        self.proximo_id += 1
        self.limpar_campos()
        self.mensagem.setText(
            f"Entrada registrada. Entregue o crachá {cracha}."
        )
        self.atualizar_tabela()

    def registrar_saida(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            self.mensagem.setText(
                "Selecione uma visita na tabela."
            )
            return

        item = self.tabela.item(linha, 0)

        if item is None:
            self.mensagem.setText(
                "Selecione uma visita válida."
            )
            return

        visita_id = int(item.text())

        for visita in self.visitas:
            if (
                visita["id"] == visita_id
                and visita["saida"] is None
            ):
                visita["saida"] = datetime.now().strftime(
                    "%H:%M:%S"
                )
                self.crachas_livres.append(
                    visita["cracha"]
                )
                self.mensagem.setText(
                    f"Saída registrada. Crachá "
                    f"{visita['cracha']} devolvido."
                )
                break

        self.atualizar_tabela()

    def presentes(self):
        return [
            v for v in self.visitas
            if v["saida"] is None
        ]

    def atualizar_tabela(self):
        termo = self.campo_filtro.text().strip().lower()
        linhas = []

        for visita in self.presentes():
            texto = (
                f"{self.visitantes[visita['cpf']]} "
                f"{visita['setor']}"
            ).lower()

            if termo in texto:
                linhas.append(visita)

        self.tabela.setRowCount(len(linhas))

        for i, visita in enumerate(linhas):
            valores = [
                visita["id"],
                self.visitantes[visita["cpf"]],
                mascarar_documento(visita["cpf"]),
                visita["setor"],
                visita["cracha"],
                visita["entrada"],
            ]

            for j, valor in enumerate(valores):
                self.tabela.setItem(
                    i,
                    j,
                    QTableWidgetItem(str(valor)),
                )

        self.tabela.setCurrentCell(-1, -1)

        self.contador.setText(
            f"No prédio: {len(self.presentes())} | "
            f"Crachás livres: {len(self.crachas_livres)}"
        )

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.campo_cpf.setFocus()