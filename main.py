from PyQt6 import uic
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QApplication

from renderer import Renderer


class UI(QWidget):

    def __init__(self):
        super().__init__()

        # load the ui file with uic module
        uic.loadUi('main.ui', self)
        self.renderer = self.findChild(Renderer, 'rendererWidget')

        self.draw_timer = QTimer()
        self.draw_timer.timeout.connect(self.renderScreen)

        self.draw_timer.start(16)

    def renderScreen(self):
        self.renderer.update()


app = QApplication([])
window = UI()
window.show()
app.exec()