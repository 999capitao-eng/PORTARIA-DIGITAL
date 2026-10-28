"""Laboratório de estilo: rode, observe e altere os valores."""

import sys

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

ESTILOS = {
    "Sem estilo": "",
    "Só border-radius": "border-radius: 12px;",
    "Cantos, fundo e cor": (
        "border-radius: 12px; background-color: #0b5ed7; color: white; padding: 8px 16px;"
    ),
    "Contorno": "border-radius: 12px; border: 2px solid #0b5ed7; padding: 8px 16px;",
    "Pílula com gradiente": (
        "border-radius: 18px; min-height: 36px; color: white; font-weight: bold;"
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0b5ed7, stop:1 #6f42c1);"
    ),
    "Tracejado e quadrado": "border: 2px dashed #b42318; border-radius: 0px; padding: 8px 16px;",
}

app = QApplication(sys.argv)
app.setStyle("Fusion")

janela = QWidget()
janela.setWindowTitle("Laboratório de estilo")
layout = QVBoxLayout(janela)
for texto, estilo in ESTILOS.items():
    botao = QPushButton(texto)
    botao.setStyleSheet(estilo)
    layout.addWidget(botao)

janela.resize(360, 320)
janela.show()
sys.exit(app.exec())