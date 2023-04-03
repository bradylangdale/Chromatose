from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenImage
from panda3d.core import WindowProperties, TransparencyAttrib

class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.paused = False
        self.pause_menu_frame = None
        self.game.accept('escape', self.toggle_pause)

    def show_pause_menu(self):
        self.pause_menu_frame = DirectFrame(frameSize=(-0.5, 0.5, -0.5, 0.5), frameColor=(0.5, 0.5, 0.5, 0.8))
        
        self.image = OnscreenImage(image='Assets/assets/Text/Chromatose.png', scale=(0.480, 1, 0.180/2), pos=(0, 0, 0.4))
        self.image.setTransparency(TransparencyAttrib.MAlpha)
        
        resume_button = DirectButton(text="Resume", scale=0.1, pos=(0, 0, 0.2), command=self.toggle_pause)
        options_button = DirectButton(text="Options", scale=0.1, pos=(0, 0, 0), command=self.show_options)
        exit_button = DirectButton(text="Exit", scale=0.1, pos=(0, 0, -0.2), command=self.game.userExit)

        resume_button.reparentTo(self.pause_menu_frame)
        options_button.reparentTo(self.pause_menu_frame)
        exit_button.reparentTo(self.pause_menu_frame)

    def hide_pause_menu(self):
        self.pause_menu_frame.destroy()
        self.image.destroy()
        
    def lock_keys_mouse(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        self.game.win.requestProperties(props)
        self.game.player.paused = True

    def release_keys_mouse(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        self.game.win.requestProperties(props)
        self.game.player.paused = False

    def toggle_pause(self):
        if not self.game.game_started:
            return
        self.paused = not self.paused
        if self.paused:
            self.show_pause_menu()
            self.lock_keys_mouse()
        else:
            self.hide_pause_menu()
            self.release_keys_mouse()

    def show_options(self):
        pass
