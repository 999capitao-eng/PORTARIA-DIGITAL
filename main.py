import logging
import sys

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from portaria.db import conectar, preparar_banco
from portaria.ui.janela_principal import JanelaPrincipal
from portaria.ui.tema import gerar_folha, tema_salvo

def main():
    logging.basicConfig(
        filename="portaria.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    conn = conectar()
    preparar_banco(conn)

    app = QApplication(sys.argv)

    # Botões padrão do Qt (Salvar, Cancelar, Sim, Não) em português
    tradutor = QTranslator(app)
    pasta_traducoes = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if tradutor.load(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil),
                     "qtbase", "_", pasta_traducoes):
        app.installTranslator(tradutor)

    app.setStyle("Fusion")  # mesma aparência em Windows, Linux e macOS
    app.setStyleSheet(gerar_folha(tema_salvo()))  # tema escolhido na última execução

    janela = JanelaPrincipal(conn)
    janela.show()
    codigo = app.exec()
    conn.close()
    return codigo

if __name__ == "__main__":
    sys.exit(main())