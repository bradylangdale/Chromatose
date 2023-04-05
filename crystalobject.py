from direct.interval.MetaInterval import Sequence
from direct.showbase.DirectObject import DirectObject
from panda3d.bullet import BulletConvexHullShape, BulletRigidBodyNode
from panda3d.core import Vec3, LPoint3


class CrystalObject(DirectObject):

    def __init__(self, position=Vec3(0, 0, 0), model='models/box.egg', scale=Vec3(0.25, 0.25, 0.25),
                 name='default'):
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
        node.addShape(shape)
        node.setMass(0.01)
        self.np = base.render.attachNewNode(node)
        self.np.setPos(position)
        base.world.attachRigidBody(node)
        crystalRotate = self.model.hprInterval(10, LPoint3(360, 0, 0))
        crystalUp = self.model.posInterval(1, LPoint3(0, 0, 1))
        crystalDown = self.model.posInterval(1, LPoint3(0, 0, 0))
        crystalMovement = Sequence(crystalUp, crystalDown)
        crystalRotate.loop()
        crystalMovement.loop()
        self.model.reparentTo(self.np)

        self.playerNode = base.render.findAllMatches("**/*Player")[0]
        self.maxSpeed = 30

        self.lifetime = 500

        self.add_task(self.track_lifetime, 'track_crystal')
        self.add_task(self.move_to_player, 'go_to_player')

    def track_lifetime(self, task):
        self.lifetime -= 0.25

        if self.lifetime < 0:
            self.np.node().removeAllChildren()
            base.world.remove(self.np.node())
            self.removeAllTasks()
            return task.done

        return task.cont

    def move_to_player(self, task):
        if self.lifetime < 0:
            return task.done

        direction = self.playerNode.getPos() - self.np.getPos()
        idealVelocity = direction.normalized() * self.maxSpeed
        accel = idealVelocity - self.np.node().getLinearVelocity()

        self.np.node().applyCentralForce(accel)

        return task.cont
