from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)


        
        self.scene = self.loader.loadModel("Map.bam")
        self.scene.reparentTo(self.render)
        
app = MyApp()
app.run()