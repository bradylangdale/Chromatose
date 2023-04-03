from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenImage
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import WindowProperties, TransparencyAttrib

from resourcepath import resource_path


class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.paused = False
        self.pause_menu_frame = None
        self.retry_menu_frame = None
        self.game.accept('escape', self.toggle_pause)
        self.font = base.loader.loadFont(resource_path('Assets/assets/font/bedstead.otf'))

    def show_pause_menu(self):
        self.pause_menu_frame = DirectFrame(frameSize=(-0.425, 0.425, 0.3, 0.8), frameColor=(0, 0, 0, 0.8))

        self.resume_button = DirectButton(text="Resume", scale=0.1, pos=(0, 0, 0.5125), text_fg=(1, 1, 1, 1),
                                          command=self.toggle_pause, text_font=self.font, relief=None)
        self.exit_button = DirectButton(text="Exit", scale=0.1, pos=(0, 0, 0.3625), text_fg=(1, 1, 1, 1),
                                        command=self.game.userExit, text_font=self.font, relief=None)

        self.image = OnscreenImage(image=resource_path('Assets/assets/Text/ChromatoseLight.png'),
                                   scale=(0.480, 1, 0.09),
                                   pos=(0, 0, 0.7))
        self.image.setTransparency(TransparencyAttrib.MAlpha)

        self.resume_button.reparentTo(self.pause_menu_frame)
        self.exit_button.reparentTo(self.pause_menu_frame)

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

    def display_score(self, score):
        self.paused = True
        self.lock_keys_mouse()

        self.retry_menu_frame = DirectFrame(frameSize=(-0.6, 0.6, 0.0625, 0.8), frameColor=(0, 0, 0, 0.8))

        self.high_score_label = DirectLabel(text='Final Score: ' + str(score), scale=0.1, pos=(0, 0, 0.5125),
                                            text_fg=(1, 1, 1, 1), text_font=self.font, relief=None)

        self.retry_button = DirectButton(text="Retry", scale=0.1, pos=(0, 0, 0.3625), text_fg=(1, 1, 1, 1),
                                         command=self.hide_score_display, text_font=self.font, relief=None)
        self.exit_button = DirectButton(text="Exit", scale=0.1, pos=(0, 0, 0.2125), text_fg=(1, 1, 1, 1),
                                        command=self.game.userExit, text_font=self.font, relief=None)

        self.image = OnscreenImage(image=resource_path('Assets/assets/Text/ChromatoseLight.png'),
                                   scale=(0.480, 1, 0.09),
                                   pos=(0, 0, 0.7))
        self.image.setTransparency(TransparencyAttrib.MAlpha)

        self.high_score_label.reparentTo(self.retry_menu_frame)
        self.retry_button.reparentTo(self.retry_menu_frame)
        self.exit_button.reparentTo(self.retry_menu_frame)

    def hide_score_display(self):
        self.paused = False
        self.release_keys_mouse()
        self.retry_menu_frame.destroy()
        self.image.destroy()
