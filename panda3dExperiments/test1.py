from direct.showbase.ShowBase import ShowBase

class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.scene = self.loader.loadModel("Assets/assets/Map/Map.gltf")

app = MyApp()
app.run()