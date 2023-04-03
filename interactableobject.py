from direct.showbase.DirectObject import DirectObject
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape
from panda3d.core import Vec3


class InteractableObject(DirectObject):

    def __init__(self, position=Vec3(0, 0, 0), model='models/box.egg', scale=Vec3(1, 1, 1), name='default'):
        DirectObject.__init__(self)

        self.model = base.loader.loadModel(model)
        self.model.setScale(scale.x, scale.y, scale.z)
        self.model.setPos(-self.model.getBounds().getCenter())
        self.model.setTwoSided(False, 1)
        self.model.flattenLight()
        self.model.clear_model_nodes()
        geom = self.model.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        node = BulletRigidBodyNode(name)
        node.setMass(0.01)
        node.addShape(shape)
        self.np = base.render.attachNewNode(node)
        self.np.setPos(position)
        base.world.attachRigidBody(node)
        self.model.copyTo(self.np)
