__all__ = ['UISlider']

from panda3d.core import Vec4
from direct.gui.DirectGui import DGG, DirectButton, DirectSlider


class UISlider(DirectSlider):
    """
    UISlider -- a widget which represents a slider that the
    user can pull left and right to represent a continuous value.
    """

    def __init__(self, parent=None, **kw):
        optiondefs = (
            ('allowprogressBar', False, self.__progressBar),
        )

        self.orientation = None
        self.progressBar = None
        if kw.get('orientation') == DGG.VERTICAL:
            # These are the default options for a vertical layout.
            optiondefs += (
                ('frameSize', (-0.08, 0.08, -1, 1), None),
                ('frameVisibleScale', (0.25, 1), None),
            )
        else:
            # These are the default options for a horizontal layout.
            optiondefs += (
                ('frameSize', (-1, 1, -0.08, 0.08), None),
                ('frameVisibleScale', (1, 0.25), None),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)

        # Initialize superclasses
        DirectSlider.__init__(self, parent)

        self.progressBar = self.createcomponent("progressBar", (), None,
                                                DirectButton, (self,),
                                                borderWidth=self['borderWidth'],
                                                state=DGG.DISABLED,
                                                sortOrder=-1,
                                                frameColor=(1.0, 1.0, 1.0, 1.0))

        # Call option initialization functions
        self.initialiseoptions(UISlider)

    def __progressBar(self):
        if self.progressBar is not None:
            if self['allowprogressBar'] is True:
                self.progressBar.show()
                self.__updProgressBar()
            else:
                self.progressBar.hide()

    def __updProgressBar(self):
        if self['allowprogressBar'] is True:
            fs = self['frameSize']
            sc = self.getScale()
            vfs = self['frameVisibleScale']
            if self.guiItem.has_frame():
                self.guiItem.recompute()
            tpos = self.thumb.getPos(self)

            r = self['range']
            if self['orientation'] == DGG.HORIZONTAL:
                pos = self.thumb.getPos()
                a = tpos[0]
                b = tpos[0]
                if r[0] > r[1]:
                    a = fs[1]
                else:
                    b = fs[0]
                self.progressBar['frameSize'] = (b, a, fs[2], fs[3])
                self.progressBar.setSz(vfs[1])
                self.progressBar.setSx(vfs[0])
            else:  # VERTICAL
                a = tpos[2]
                b = tpos[2]
                if r[0] > r[1]:
                    b = fs[3]
                else:
                    a = fs[2]
                self.progressBar['frameSize'] = (fs[0], fs[1], a, b)
                self.progressBar.setSx(vfs[0])
                self.progressBar.setSz(vfs[1])
            # center progressbar
            self.progressBar.setPos(0, 0, 0)
            if self.guiItem.has_frame():
                afs = Vec4(self.progressBar.guiItem.getFrame())
                bfs = Vec4(self.guiItem.getFrame())
                afs.setX(.5 * (afs[0] + afs[1]))
                afs.setZ(.5 * (afs[2] + afs[3]))
                bfs.setX(.5 * (bfs[0] + bfs[1]))
                bfs.setZ(.5 * (bfs[2] + bfs[3]))
                if self['orientation'] == DGG.VERTICAL:
                    self.progressBar.setX(self, bfs[0] - (afs[0]) * self.progressBar.getSx(self))
                if self['orientation'] == DGG.HORIZONTAL:
                    self.progressBar.setZ(self, bfs[2] - (afs[2]) * self.progressBar.getSz(self))

    # override
    def setOrientation(self):
        if self.orientation is None:
            self.orientation = self['orientation']
        if self.orientation != self['orientation']:
            self.orientation = self['orientation']
            vfs = self['frameVisibleScale']
            self['frameVisibleScale'] = (vfs[1], vfs[0])
            if self.progressBar is not None and not self.progressBar.isHidden():
                pbfs = self.progressBar.guiItem.getFrame()
                self.progressBar['frameSize'] = (pbfs[2], pbfs[3], pbfs[0], pbfs[1])
            tf = self.thumb['frameSize']
            self.thumb['frameSize'] = (tf[2], tf[3], tf[0], tf[1])
        super().setOrientation()

    # override
    def destroy(self):
        if (hasattr(self, 'progressBar')):
            self.progressBar.destroy()
            del self.progressBar
        super().destroy()

    # override
    def commandFunc(self):
        super().commandFunc()
        self.__updProgressBar()

    # override
    def setFrameSize(self, fClearFrame=0):
        super().setFrameSize(fClearFrame=fClearFrame)
        self.__updProgressBar()