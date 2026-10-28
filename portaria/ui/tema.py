from string import Template

from PySide6.QtCore import QSettings

TEMAS = {
    "claro": {
        "fundo": "#F4F6F8",
        "superficie": "#FFFFFF",
        "zebra": "#F8FAFC",
        "texto": "#1F2933",
        "texto_suave": "#52606D",
        "borda": "#CBD2D9",
        "primaria": "#1D4ED8",
        "primaria_hover": "#1E40AF",
        "primaria_texto": "#FFFFFF",
        "perigo": "#B42318",
        "perigo_hover": "#912018",
        "perigo_texto": "#FFFFFF",
        "selecao": "#DBEAFE",
        "selecao_texto": "#1F2933",
        "aviso_fundo": "#FEF3C7",
        "aviso_texto": "#7A2E0E",
    },
    "escuro": {
        "fundo": "#111827",
        "superficie": "#1F2937",
        "zebra": "#243041",
        "texto": "#F3F4F6",
        "texto_suave": "#A8B3C2",
        "borda": "#374151",
        "primaria": "#3B82F6",
        "primaria_hover": "#60A5FA",
        "primaria_texto": "#0B1220",
        "perigo": "#F87171",
        "perigo_hover": "#FCA5A5",
        "perigo_texto": "#1F0A0A",
        "selecao": "#1E3A8A",
        "selecao_texto": "#FFFFFF",
        "aviso_fundo": "#78350F",
        "aviso_texto": "#FEF3C7",
    },
}

TEMAS["institucional"] = {
    **TEMAS["claro"],
    "fundo": "#F2F6FA",
    "superficie": "#FFFFFF",
    "zebra": "#EAF1F8",
    "texto": "#0F2540",
    "texto_suave": "#40566F",
    "borda": "#A9BBD0",
    "primaria": "#004A8D",
    "primaria_hover": "#003A70",
    "primaria_texto": "#FFFFFF",
    "selecao": "#FDE3BF",
    "selecao_texto": "#0F2540",
    "aviso_fundo": "#FFF1D6",
    "aviso_texto": "#6B3A00",
}

ROTULOS = {
    "claro": "Tema &claro",
    "escuro": "Tema &escuro",
    "institucional": "Tema &institucional",
}

_CHAVE = "tema"


def _luminancia(cor):
    cor = cor.lstrip("#")
    canais = [int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        for c in canais
    ]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(cor_a, cor_b):
    """Razão de contraste WCAG entre duas cores hexadecimais."""
    la, lb = _luminancia(cor_a), _luminancia(cor_b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


def _configuracoes():
    return QSettings("Portaria", "PortariaDigital")


def tema_salvo():
    nome = _configuracoes().value(_CHAVE, "claro")
    return nome if nome in TEMAS else "claro"


def salvar_tema(nome):
    if nome in TEMAS:
        _configuracoes().setValue(_CHAVE, nome)


_MODELO = Template("""
QWidget {
    background-color: $fundo;
    color: $texto;
}
QMainWindow, QTabWidget::pane {
    background-color: $fundo;
}
QTabWidget::pane {
    border: 1px solid $borda;
}
QTabBar::tab {
    background: $superficie;
    color: $texto_suave;
    border: 1px solid $borda;
    padding: 6px 14px;
}
QTabBar::tab:selected {
    color: $texto;
    border-bottom: 2px solid $primaria;
}
QMenuBar, QMenu {
    background-color: $superficie;
    color: $texto;
}
QMenuBar::item:selected, QMenu::item:selected {
    background-color: $selecao;
    color: $selecao_texto;
}
QLineEdit, QComboBox, QDateEdit {
    background-color: $superficie;
    color: $texto;
    border: 1px solid $borda;
    border-radius: 4px;
    padding: 4px 6px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid $primaria;
}
QLineEdit:read-only {
    color: $texto_suave;
}
QComboBox QAbstractItemView {
    background-color: $superficie;
    color: $texto;
    selection-background-color: $selecao;
    selection-color: $selecao_texto;
}
QTableWidget {
    background-color: $superficie;
    alternate-background-color: $zebra;
    color: $texto;
    gridline-color: $borda;
    border: 1px solid $borda;
    selection-background-color: $selecao;
    selection-color: $selecao_texto;
}
QHeaderView::section {
    background-color: $fundo;
    color: $texto;
    border: none;
    border-bottom: 1px solid $borda;
    padding: 6px;
    font-weight: bold;
}
QPushButton {
    background-color: $superficie;
    color: $texto;
    border: 1px solid $borda;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    border-color: $primaria;
}
QPushButton:focus {
    border: 2px solid $primaria;
}
QPushButton[variante="primario"] {
    background-color: $primaria;
    color: $primaria_texto;
    border: 1px solid $primaria;
}
QPushButton[variante="primario"]:hover {
    background-color: $primaria_hover;
}
QPushButton[variante="perigo"] {
    background-color: $perigo;
    color: $perigo_texto;
    border: 1px solid $perigo;
}
QPushButton[variante="perigo"]:hover {
    background-color: $perigo_hover;
}
QPushButton[variante="secundario"] {
    background-color: $superficie;
    color: $texto;
    border: 2px solid $primaria;
}
QPushButton[variante="secundario"]:hover {
    background-color: $selecao;
    color: $selecao_texto;
}
QPushButton:disabled, QPushButton[variante="secundario"]:disabled {
    background-color: $fundo;
    color: $texto_suave;
    border: 1px dashed $borda;
}
QLabel {
    background: transparent;
}
QLabel#mensagem {
    color: $texto_suave;
}
QLabel#aviso {
    background-color: $aviso_fundo;
    color: $aviso_texto;
    padding: 6px;
    border-radius: 4px;
}
QStatusBar {
    background-color: $superficie;
    color: $texto_suave;
}
QMessageBox, QDialog {
    background-color: $fundo;
}
""")


def gerar_folha(nome):
    return _MODELO.substitute(TEMAS.get(nome, TEMAS["claro"]))