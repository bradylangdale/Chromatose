import random

from direct.showbase.DirectObject import DirectObject
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape
from panda3d.core import Vec3


class InteractableObject(DirectObject):

    def __init__(self, main, world, worldNP, position=Vec3(0, 0, 0), model='models/box.egg', scale=Vec3(0, 0, 0)):
        DirectObject.__init__(self)

        self.world = world
        self.worldNP = worldNP

        self.model = main.loader.loadModel(model)
        self.model.setScale(scale.x, scale.y, scale.z)
        self.model.setPos(-self.model.getBounds().getCenter())
        self.model.flattenLight()
        self.model.clear_model_nodes()
        geom = self.model.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        node = BulletRigidBodyNode()
        node.setMass(1.0)
        node.addShape(shape)
        np = main.render.attachNewNode(node)
        np.setPos(position)
        self.world.attachRigidBody(node)
        self.model.copyTo(np)
