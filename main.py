import random

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, Vec3
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletBoxShape, BulletDebugNode

from PlayerController import PlayerController


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # set the camera's lens to the one we just created
        self.cam.node().getLens().setFov(90)

        # Load the environment model.
        self.scene = self.loader.loadModel("Assets/assets/Map/Map.bam")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(1, 1, 1)
        self.scene.setPos(0, 0, 0)

        self.crosshair = OnscreenText(text='+', pos=(0, 0), scale=0.1)

        debugNode = BulletDebugNode('Debug')
        debugNode.showWireframe(True)
        debugNode.showConstraints(True)
        debugNode.showBoundingBoxes(False)
        debugNode.showNormals(False)
        debugNP = self.render.attachNewNode(debugNode)
        debugNP.show()

        # World
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.world.setDebugNode(debugNP.node())
        self.worldNP = self.render.attachNewNode(BulletRigidBodyNode('World'))

        # Disable the camera trackball controls.
        self.disableMouse()
        self.player = PlayerController(self.camera, self.win, self.world, self.worldNP)

        self.player.setPos(self.camera.getPos() - Vec3(0, 20, 0))

        # Plane
        shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -1)
        self.world.attachRigidBody(node)

        self.model = self.loader.loadModel('models/box.egg')
        self.model.setPos(-0.5, -0.5, -0.5)
        self.model.flattenLight()
        for i in range(0, 500):
           self.add_box(i)

        self.add_task(self.update, 'update')

    # Update
    def update(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    def add_box(self, i):
        # Box
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        node = BulletRigidBodyNode('Box')
        node.setMass(1000.0)
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(random.uniform(-10, 10), random.uniform(-10, 10), 1+(i * 0.1))
        self.world.attachRigidBody(node)
        self.model.copyTo(np)


app = MyApp()
props = WindowProperties()
props.setCursorHidden(True)
app.win.requestProperties(props)
app.run()
