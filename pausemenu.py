from direct.gui.DirectGui import DirectButton, DirectFrame
from panda3d.core import WindowProperties

class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.paused = False
        self.pause_menu_frame = None
        self.game.accept('escape', self.toggle_pause)

    def show_pause_menu(self):
        self.pause_menu_frame = DirectFrame(frameSize=(-0.5, 0.5, -0.5, 0.5), frameColor=(0.5, 0.5, 0.5, 0.8))

        resume_button = DirectButton(text="Resume", scale=0.1, pos=(0, 0, 0.2), command=self.toggle_pause)
        options_button = DirectButton(text="Options", scale=0.1, pos=(0, 0, 0), command=self.show_options)
        exit_button = DirectButton(text="Exit", scale=0.1, pos=(0, 0, -0.2), command=self.game.userExit)

        resume_button.reparentTo(self.pause_menu_frame)
        options_button.reparentTo(self.pause_menu_frame)
        exit_button.reparentTo(self.pause_menu_frame)

    def hide_pause_menu(self):
        self.pause_menu_frame.destroy()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_pause_menu()
            props = WindowProperties()
            props.setCursorHidden(False)
            self.game.win.requestProperties(props)
            self.game.player.paused = True
        else:
            self.hide_pause_menu()
            props = WindowProperties()
            props.setCursorHidden(True)
            self.game.win.requestProperties(props)
            self.game.player.paused = False

    def show_options(self):
        pass
