from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

SETORES = ["Secretaria", "Coordenação", "Laboratório"]

class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portaria Digital")
        self.resize(820, 520)

        # ---------- widgets ----------
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)
        self.campo_cpf.setStyleSheet("background-color: #FFFFFF; color: black;")
        self.campo_nome = QLineEdit()
        self.campo_nome.setStyleSheet("background-color: #FFFFFF; color: black;")
        self.campo_nome.setPlaceholderText("Escreva seu nome aqui")
        self.combo_setor = QComboBox()
        self.combo_setor.addItem("Selecione um setor")
        self.combo_setor.addItems(SETORES)
        self.combo_setor.setStyleSheet("background-color: #FFFFFF; color: black;")
        
        self.botao_entrada = QPushButton("Registrar entrada")
        self.botao_entrada.setStyleSheet("background-color: #FF0000 ; color: white; border-radius: 8px; padding: 6px 12px; ")

        self.botao_limpar = QPushButton("Limpar campos")
        self.mensagem = QLabel("Informe o CPF do visitante.")

        self.botao_limpar.setStyleSheet(
        "background-color: #008000; color: white; border-radius: 8px; padding: 6px 12px;"
        )
        # ---------- layouts ----------
        formulario = QFormLayout()
        formulario.addRow("CPF:", self.campo_cpf)
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Setor:", self.combo_setor)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_entrada)
        botoes.addWidget(self.botao_limpar)

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addLayout(botoes)
        layout.addWidget(self.mensagem)
        layout.addStretch()
        self.setLayout(layout)
