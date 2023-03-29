import random

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, Vec3
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletDebugNode, \
    BulletTriangleMesh, BulletTriangleMeshShape

from interactableobject import InteractableObject
from playercontroller import PlayerController

DEBUG = False


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
        self.player = PlayerController(self.camera, self.win, self.world, self.worldNP)

        self.player.setPos(self.camera.getPos() - Vec3(0, 20, 0))

        # Load Map Mesh
        self.scene.clear_model_nodes()
        self.scene.flatten_strong()
        geom = self.scene.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        self.world.attachRigidBody(node)

        for i in range(50):
            InteractableObject(self, self.world, self.worldNP,
                               Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(0, 20)),
                               'Assets/assets/Gun/Gun.gltf',
                               scale=Vec3(0.02, 0.02, 0.02))

        self.add_task(self.update, 'update')

    # Update
    def update(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont


app = MyApp()
props = WindowProperties()
props.setCursorHidden(True)
app.win.requestProperties(props)
app.run()
