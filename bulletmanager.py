import os
import sys
from random import randint

from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.bullet import BulletConvexHullShape, BulletRigidBodyNode
from panda3d.core import Vec3

from resourcepath import resource_path


class BulletManager(DirectObject):

    def __init__(self):

        # load bullet models
        bulletScale = 0.15
        self.redBullet = base.loader.loadModel(resource_path('Assets/assets/RedCrystal/red.bam'))
        self.redBullet.setScale(bulletScale, bulletScale, bulletScale)
        self.redBullet.setPos(-self.redBullet.getBounds().getCenter())
        self.redBullet.setTwoSided(False, 1)
        self.redBullet.flattenLight()
        self.redBullet.clear_model_nodes()
        geom = self.redBullet.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        self.redBulletNP = BulletRigidBodyNode('redBullet')
        self.redBulletNP.setLinearDamping(0)
        self.redBulletNP.setFriction(0.1)
        self.redBulletNP.setMass(0.01)
        self.redBulletNP.addShape(shape)

        bulletScale = 0.3
        self.greenBullet = base.loader.loadModel(resource_path('Assets/assets/GreenCrystal/green.bam'))
        self.greenBullet.setScale(bulletScale, bulletScale, bulletScale)
        self.greenBullet.setPos(-self.greenBullet.getBounds().getCenter())
        self.greenBullet.setTwoSided(False, 1)
        self.greenBullet.flattenLight()
        self.greenBullet.clear_model_nodes()
        geom = self.greenBullet.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        self.greenBulletNP = BulletRigidBodyNode('greenBullet')
        self.greenBulletNP.setLinearDamping(0)
        self.greenBulletNP.setFriction(0.1)
        self.greenBulletNP.setMass(0.01)
        self.greenBulletNP.addShape(shape)

        self.blueBullet = base.loader.loadModel(resource_path('Assets/assets/BlueCrystal/Blue.bam'))
        self.blueBullet.setScale(bulletScale, bulletScale, bulletScale)
        self.blueBullet.setPos(-self.blueBullet.getBounds().getCenter())
        self.blueBullet.setTwoSided(False, 1)
        self.blueBullet.flattenLight()
        self.blueBullet.clear_model_nodes()
        geom = self.blueBullet.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        self.blueBulletNP = BulletRigidBodyNode('blueBullet')
        self.blueBulletNP.setLinearDamping(0)
        self.blueBulletNP.setFriction(0.1)
        self.blueBulletNP.setMass(0.01)
        self.blueBulletNP.addShape(shape)

        self.bulletModels = [self.redBullet, self.blueBullet, self.greenBullet]
        self.bulletNodes = [self.redBulletNP, self.blueBulletNP, self.greenBulletNP]
        self.bullets = []

        self.add_task(self.track_lifetime, 'track_bullets')

    def spawn(self, position, impulse):

        typeOfBullet = randint(0, len(self.bulletModels) - 1)
        rb = self.bulletNodes[typeOfBullet].make_copy()

        self.bullets.append(base.render.attachNewNode(rb))
        self.bullets[-1].setPos(position)

        rb.applyCentralImpulse(impulse)
        base.world.attachRigidBody(rb)
        self.bulletModels[typeOfBullet].copyTo(self.bullets[-1])

    def track_lifetime(self, task):
        if len(self.bullets) == 0:
            return Task.cont

        new_bullets = []
        for bullet in self.bullets:
            speed = bullet.node().getLinearVelocity().length()
            if speed < 1:
                bullet.node().removeAllChildren()
                base.world.remove(bullet.node())
            else:
                new_bullets.append(bullet)

        self.bullets = new_bullets

        return Task.cont