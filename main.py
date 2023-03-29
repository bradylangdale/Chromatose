import random
from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from panda3d.core import Point3, WindowProperties, NodePath, Vec3, BitMask32, PerspectiveLens
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletBoxShape, BulletDebugNode, \
    BulletCapsuleShape, ZUp, BulletCharacterControllerNode


class CameraController(DirectObject):
    def __init__(self, camera: NodePath, win, world, worldNP):
        super().__init__()
        self.camera = camera
        self.win = win
        self.world = world
        self.worldNP = worldNP

        self.currentState = {"forward": False, "backward": False, "left": False, "right": False, 'jump': False}
        self.accept("w", self.toggle_move_state, ["forward", True])
        self.accept("w-up", self.toggle_move_state, ["forward", False])
        self.accept("s", self.toggle_move_state, ["backward", True])
        self.accept("s-up", self.toggle_move_state, ["backward", False])
        self.accept("a", self.toggle_move_state, ["left", True])
        self.accept("a-up", self.toggle_move_state, ["left", False])
        self.accept("d", self.toggle_move_state, ["right", True])
        self.accept("d-up", self.toggle_move_state, ["right", False])
        self.accept('space', self.toggle_move_state, ['jump', True])
        self.add_task(self.move, "move")
        self.add_task(self.rotate, "rotate")

        height = 1.75
        radius = 0.4
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)

        self.playerNode = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.playerNP = self.worldNP.attachNewNode(self.playerNode)
        self.playerNP.setPos(-2, 0, 14)
        self.playerNP.setH(45)
        self.camera.reparentTo(self.playerNP)
        self.camera.setPos(0, 0, 1)
        self.playerNP.setCollideMask(BitMask32.allOn())
        self.playerNode.setMaxJumpHeight(8.0)
        self.playerNode.setJumpSpeed(6.0)

        self.world.attachCharacter(self.playerNP.node())

    def setPos(self, vec3):
        self.playerNP.setPos(vec3)

    def toggle_move_state(self, key, value):
        self.currentState[key] = value

    def rotate(self, task):
        mouse_sens = 0.05
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2):
            self.playerNP.setH(self.playerNP.getH() - (x - self.win.getXSize() / 2) * mouse_sens)
            self.camera.setP(self.camera.getP() - (y - self.win.getYSize() / 2) * mouse_sens)
        return Task.cont

    def move(self, task):
        current_walking = False
        forwards = Vec3(cos((90 + self.camera.getH()) / 180 * pi), sin((90 + self.camera.getH()) / 180 * pi), 0).normalized()
        right = Vec3(cos(self.camera.getH() / 180 * pi), sin(self.camera.getH() / 180 * pi), 0).normalized()
        speed = Vec3(0, 0, 0)
        #omega = 0.0


        if self.currentState["forward"]:
            speed.setY(self.scale(10.0, forwards).length())
        if self.currentState["backward"]:
            speed.setY(-self.scale(10.0, forwards).length())
        if self.currentState["left"]:
            speed.setX(-self.scale(10.0, right).length())
        if self.currentState["right"]:
            speed.setX(self.scale(10.0, right).length())
        if self.currentState['jump']:
            self.playerNode.doJump()
            self.currentState['jump'] = False

        #self.playerNode.setAngularMovement(omega)
        self.playerNode.setLinearMovement(speed, True)

        return Task.cont

    def scale(self, s, v):
        return Vec3(s * v.x, s * v.y, s * v.z)


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
        self.cameraController = CameraController(self.camera, self.win, self.world, self.worldNP)

        self.cameraController.setPos(self.camera.getPos() - Vec3(0, 20, 0))

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
