from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenImage
from panda3d.core import TextNode, TransparencyAttrib

from resourcepath import resource_path


class StartScreen(DirectFrame):
    def __init__(self, parent, start_callback):
        super().__init__(parent=parent, frameSize=(-1, 1, -1, 1), frameColor=(0, 0, 0, 1))

        font = base.loader.loadFont(resource_path('Assets/assets/font/bedstead.otf'))

        self.image = OnscreenImage(image=resource_path('Assets/assets/Text/ChromatoseLight.png'), scale=(0.480*2, 1, 0.180), pos=(0, 0, 0.6))
        self.image.setTransparency(TransparencyAttrib.MAlpha)

        self.start_button = DirectButton(text='Start', scale=0.12, pos=(0, 0, -0.3), text_fg=(1, 1, 1, 1),
                                     command=start_callback, text_font=font, relief=None, parent=self)

    def __KillImage__(self):
        self.image.destroy()