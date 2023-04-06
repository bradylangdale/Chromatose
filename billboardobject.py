from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from panda3d.core import TextureStage, CardMaker, Vec3, TransparencyAttrib, Texture, NodePath, PNMImage
from direct.showbase.DirectObject import DirectObject
from panda3d.bullet import BulletRigidBodyNode, BulletCapsuleShape

from crystalobject import CrystalObject
from pathfinder import Pathfinder
from resourcepath import resource_path


class BillBoardObject(DirectObject):

    def __init__(self, texture, position=Vec3(0, 0, 1), scale=1, drop=None, pathfinder=None):
        DirectObject.__init__(self)
        self.position = position
        self.scale = scale
        # Load Texture
        self.texture = texture
        self.tex_width = self.texture.getXSize()
        self.tex_height = self.texture.getYSize()
        self.aspect_ratio = self.tex_width / self.tex_height

        # Create Card, set texture, and make it a billboard
        self.card = CardMaker('Billboard')
        self.card.setFrame(-self.aspect_ratio * self.scale, self.aspect_ratio * self.scale, -self.scale, self.scale)
        self.BillboardNP = base.render.attachNewNode(self.card.generate())
        self.BillboardNP.setTexture(self.texture)
        self.BillboardNP.setTransparency(TransparencyAttrib.MAlpha)
        self.BillboardNP.setBillboardAxis()
        self.BillboardNP.setShaderAuto()

        # Add Physics
        self.card_physics_node = BulletRigidBodyNode('Billboard')
        self.card_physics_node.setMass(0.01)
        shape = BulletCapsuleShape(self.scale / 2, self.scale * self.aspect_ratio, 2)
        self.card_physics_node.addShape(shape)
        base.world.attachRigidBody(self.card_physics_node)
        self.card_physics_np = base.render.attachNewNode(self.card_physics_node)
        self.card_physics_np.setPos(position)
        self.BillboardNP.reparentTo(self.card_physics_np)

        # Make item upright
        self.card_physics_node.setAngularFactor(Vec3(0, 0, 1))
        self.card_physics_node.setLinearSleepThreshold(0)

        self.health = 1
        self.maxSpeed = 18
        self.lifetime = 1

        self.dropPath = resource_path('Assets/assets/Bullet/Bullet.bam')
        self.dropName = 'default'
        if drop == 'red':
            self.dropPath = resource_path('Assets/assets/RedCrystal/red.bam')
            self.dropName = 'red_crystal'
        elif drop == 'green':
            self.dropPath = resource_path('Assets/assets/GreenCrystal/green.bam')
            self.dropName = 'green_crystal'
        elif drop == 'blue':
            self.dropPath = resource_path('Assets/assets/BlueCrystal/Blue.bam')
            self.dropName = 'blue_crystal'

        self.playerNode = base.render.findAllMatches("**/*Player")[0]

        if pathfinder is None:
            self.pathfinder = Pathfinder()
            self.pathfinder.loadMap(resource_path('NavMeshes/defaultnavmesh.json'))
        else:
            self.pathfinder = pathfinder

        self.nav_offset = Vec3(50, 50, 3)
        self.path = self.pathfinder.getPath(start=self.card_physics_np.getPos() + self.nav_offset, end=self.playerNode.getPos() + self.nav_offset)
        self.current_node = 0
        self.target = self.playerNode.getPos()

        self.path_lifetime = 5

        self.add_task(self.collision_check, "collision_check")
        self.add_task(self.move_toward, 'pathfind')
        self.add_task(self.track_lifetime, "track_lifetime")

    def collision_check(self, task):
        if self.health < 0:
            pos = self.card_physics_np.getPos()
            CrystalObject(pos, self.dropPath, name=self.dropName)

            self.removeEnemy()

            return task.done

        else:
            check = base.world.contactTest(self.card_physics_node)
            for contact in check.getContacts():
                if contact.getNode1().getName().find('Bullet') != -1:
                    self.health -= 0.25

        return task.cont

    def track_lifetime(self, task):
        if self.lifetime < 0:
            self.health = -0.1
            return task.done

        if self.card_physics_node.getLinearVelocity().length() < 0.1:
            self.lifetime -= 0.01

        return task.cont

    def move_toward(self, task):
        if self.health < 0 or self.card_physics_node is None:
            if self.health < 0:
                pos = self.card_physics_np.getPos()
                CrystalObject(pos, self.dropPath, name=self.dropName)

            self.removeEnemy()
            return task.done

        direction = self.target - self.card_physics_np.getPos()
        direction.z = 0
        idealVelocity = direction.normalized() * self.maxSpeed
        accel = idealVelocity - self.card_physics_node.getLinearVelocity()
        accel.z = 0

        self.card_physics_node.applyCentralForce(accel * 0.2)

        self.path_lifetime -= 0.1

        if self.path is not None and (self.current_node + 1) < len(self.path) and direction.length() < 1.5:
            self.current_node += 1
            self.target = self.path[self.current_node]
            self.target = Vec3(self.target[0], self.target[1], 3) - self.nav_offset

        if self.path is None or self.path_lifetime < 0:
            result = base.world.rayTestClosest(self.card_physics_np.getPos(), self.playerNode.getPos())
            if (result.hasHit() and result.getNode().getName() == 'Player') or not result.hasHit():
                self.target = self.playerNode.getPos()
            else:
                try:
                    self.path = self.pathfinder.getPath(start=self.card_physics_np.getPos() + self.nav_offset,
                                                        end=self.playerNode.getPos() + self.nav_offset)
                except:
                    self.path = None

                if self.path is not None:
                    self.current_node = 0
                    self.target = self.path[self.current_node]
                    self.target = Vec3(self.target[0], self.target[1], 3) - self.nav_offset

                    self.path_lifetime = 5
                else:
                    self.target = self.playerNode.getPos()

        return task.cont

    def removeEnemy(self):
        self.removeAllTasks()
        self.ignoreAll()

        if self.card_physics_node is not None:
            self.card_physics_node.removeAllChildren()
            base.world.remove(self.card_physics_node)
