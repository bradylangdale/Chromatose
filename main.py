import random

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.filter.CommonFilters import CommonFilters
from panda3d.core import WindowProperties, Vec3, AntialiasAttrib, Spotlight, AmbientLight, LVector4, LPoint3
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletDebugNode, BulletTriangleMesh, BulletTriangleMeshShape, BulletPlaneShape

from interactableobject import InteractableObject
from pipeline import CustomPipeline
from playercontroller import PlayerController
from billboardobject import BillBoardObject

DEBUG = False


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        filters = CommonFilters(self.win, self.cam)
        base.setBackgroundColor(0, 0, 0)

        self.pipeline = CustomPipeline(manager=filters.manager)
        self.pipeline.enable_shadows = True

        # set the camera's lens to the one we just created
        self.cam.node().getLens().setFov(120)
        self.cam.node().getLens().setNearFar(0.1, 10000)
        self.cam.setAntialias(AntialiasAttrib.MAuto)

        self.crosshair = OnscreenText(text='+', pos=(0, 0), scale=0.1, fg=(1, 1, 1, 1))

        # World
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.worldNP = self.render.attachNewNode(BulletRigidBodyNode('World'))

        if DEBUG:
            debugNode = BulletDebugNode('Debug')
            debugNode.showWireframe(True)
            debugNode.showConstraints(True)
            debugNode.showBoundingBoxes(False)
            debugNode.showNormals(False)
            debugNP = self.render.attachNewNode(debugNode)
            debugNP.show()
            self.world.setDebugNode(debugNP.node())

        # Disable the camera trackball controls.
        self.disableMouse()
        self.player = PlayerController(self.camera, self.win)

        self.player.setPos(self.camera.getPos() - Vec3(0, 20, 0))

        # Load Map Mesh
        self.scene = self.loader.loadModel("Assets/assets/Map/Map2.glb")
        self.scene.setTwoSided(False, 1)
        self.scene.clear_model_nodes()
        self.scene.flatten_strong()
        geom = self.scene.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        self.np = self.render.attachNewNode(node)
        self.world.attachRigidBody(node)
        self.scene.reparentTo(self.np)

        # Plane (should keep things from falling through)
        shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -1.1)
        self.world.attachRigidBody(node)

        self.objects = []
        for i in range(10):
            object = InteractableObject(self, self.world, self.worldNP,
                                        Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(0, 20)),
                                        'Assets/assets/Gun/Gun.bam',
                                        scale=Vec3(0.02, 0.02, 0.02))
            self.objects.append(object)

        self.crystals = []
        for i in range(100):
            object = InteractableObject(self, self.world, self.worldNP,
                                        Vec3(random.uniform(-10, 10), random.uniform(-10, 10),
                                             random.uniform(0, 20)),
                                        'Assets/assets/BlueCrystal/Blue.bam',
                                        name='blue_crystal')
            self.crystals.append(object)

            object = InteractableObject(self, self.world, self.worldNP,
                                        Vec3(random.uniform(-10, 10), random.uniform(-10, 10),
                                             random.uniform(0, 20)),
                                        'Assets/assets/RedCrystal/red.bam',
                                        name='red_crystal')
            self.crystals.append(object)

            object = InteractableObject(self, self.world, self.worldNP,
                                        Vec3(random.uniform(-10, 10), random.uniform(-10, 10),
                                             random.uniform(0, 20)),
                                        'Assets/assets/GreenCrystal/green.bam',
                                        name='green_crystal')
            self.crystals.append(object)

        self.add_task(self.update, 'update')

        # Add Billboard Enemy
        self.billboard_enemy = BillBoardObject("sprite.png", Vec3(0, 0, 8), scale=1.5)
        self.billboard_enemy = BillBoardObject("sprite.png", Vec3(2, 0, 10), scale=3)
        self.billboard_enemy = BillBoardObject("sprite.png", Vec3(2, 0, 10), scale=5)

        self.light = self.render.attachNewNode(Spotlight("Spot"))
        self.light.node().setScene(self.render)
        self.light.node().setShadowCaster(True, 4096, 4096)
        self.light.node().setColor((1.5, 1.5, 1.5, 1))
        #self.light.node().showFrustum()
        self.light.node().getLens().setFov(45)
        self.light.node().getLens().setNearFar(1, 10000)
        self.light.setPos(0, -50, 50)
        self.light.lookAt(0, 10, 0)
        self.render.setLight(self.light)

        self.alight = self.render.attachNewNode(AmbientLight("Ambient"))
        self.alight.node().setColor(LVector4(0.2, 0.2, 0.2, 1))
        self.render.setLight(self.alight)

        # Important! Enable the shader generator.
        filters.setCartoonInk(2)
        filters.setSrgbEncode()
        filters.setHighDynamicRange()

    # Update
    def update(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)

        self.scene.setColorScale(self.player.r, self.player.g, self.player.b, 1.0)
        self.player.gun.setColorScale(self.player.r, self.player.g, self.player.b, 1.0)
        for object in self.objects:
            object.np.setColorScale(self.player.r, self.player.g, self.player.b, 1.0)

        return task.cont


app = MyApp()
props = WindowProperties()
props.setCursorHidden(True)
app.win.requestProperties(props)
app.run()
