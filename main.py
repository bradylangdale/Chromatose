import random
from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from panda3d.core import Point3, WindowProperties, NodePath, Vec3
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletBoxShape, BulletDebugNode


class CameraController(DirectObject):
    def __init__(self, camera: NodePath, win):
        super().__init__()
        self.camera = camera
        self.win = win

        self.currentState = {"forward": False, "backward": False, "left": False, "right": False}
        self.accept("w", self.toggle_move_state, ["forward", True])
        self.accept("w-up", self.toggle_move_state, ["forward", False])
        self.accept("s", self.toggle_move_state, ["backward", True])
        self.accept("s-up", self.toggle_move_state, ["backward", False])
        self.accept("a", self.toggle_move_state, ["left", True])
        self.accept("a-up", self.toggle_move_state, ["left", False])
        self.accept("d", self.toggle_move_state, ["right", True])
        self.accept("d-up", self.toggle_move_state, ["right", False])
        self.add_task(self.move, "move")
        self.add_task(self.rotate, "rotate")

    def toggle_move_state(self, key, value):
        self.currentState[key] = value

    def rotate(self, task):
        mouse_sens = 0.05
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        camera = self.camera
        if self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2):
            camera.setH(camera.getH() - (x - self.win.getXSize() / 2) * mouse_sens)
            camera.setP(camera.getP() - (y - self.win.getYSize() / 2) * mouse_sens)
        return Task.cont

    def move(self, task):
        current_walking = False
        forwards = Vec3(cos((90 + self.camera.getH()) / 180 * pi), sin((90 + self.camera.getH()) / 180 * pi), 0) * .1
        right = Vec3(cos(self.camera.getH() / 180 * pi), sin(self.camera.getH() / 180 * pi), 0) * .1
        if self.currentState["forward"]:
            self.camera.setPos(self.camera.getPos() + forwards)
        if self.currentState["backward"]:
            self.camera.setPos(self.camera.getPos() - forwards)
        if self.currentState["left"]:
            self.camera.setPos(self.camera.getPos() - right)
        if self.currentState["right"]:
            self.camera.setPos(self.camera.getPos() + right)

        return Task.cont


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable the camera trackball controls.
        self.disableMouse()
        self.cameraController = CameraController(self.camera, self.win)

        self.cameraController.camera.setPos(self.camera.getPos() - Vec3(0, 20, 0))

        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)

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

        # Plane
        shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -2)
        self.world.attachRigidBody(node)

        self.model = self.loader.loadModel('models/box.egg')
        self.model.setPos(-0.5, -0.5, -0.5)
        self.model.flattenLight()
        for i in range(0, 1000):
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
        node.setMass(1.0)
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(random.uniform(-10, 10), random.uniform(-10, 10), 2+(i * 0.2))
        self.world.attachRigidBody(node)
        self.model.copyTo(np)


app = MyApp()
props = WindowProperties()
props.setCursorHidden(True)
app.win.requestProperties(props)
app.run()
