from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenImage
from panda3d.core import TextNode, TransparencyAttrib

class StartScreen(DirectFrame):
    def __init__(self, parent, start_callback):
        super().__init__(parent=parent, frameSize=(-1, 1, -1, 1), frameColor=(0, 0, 0, 1))

        #self.title = OnscreenText(text='Chromatose', scale=0.1, pos=(0, 0.3), fg=(1, 1, 1, 1), parent=self, align=TextNode.A_center)
        self.image = OnscreenImage(image='Assets/assets/Text/ChromatoseLight.png', scale=(0.480*2, 1, 0.180), pos=(0, 0, 0.6))
        self.image.setTransparency(TransparencyAttrib.MAlpha)

        self.start_button = DirectButton(text='Start', scale=0.1, pos=(0, 0, -0.3), command=start_callback, parent=self)

    def __KillImage__(self):
        self.image.destroy()