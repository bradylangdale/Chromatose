from direct.task import Task
from panda3d.core import TextureStage, CardMaker, Vec3, TransparencyAttrib, Texture, NodePath, PNMImage
from direct.showbase.DirectObject import DirectObject
from panda3d.bullet import BulletRigidBodyNode, BulletCapsuleShape


class BillBoardObject(DirectObject):

    def __init__(self, texture, position=Vec3(0, 0, 1), scale=1):
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
        shape = BulletCapsuleShape(self.aspect_ratio * self.scale, self.scale * 1.5, 2)
        self.card_physics_node.addShape(shape)
        base.world.attachRigidBody(self.card_physics_node)
        self.card_physics_np = base.render.attachNewNode(self.card_physics_node)
        self.card_physics_np.setPos(position)
        self.BillboardNP.reparentTo(self.card_physics_np)

        # Make item upright
        self.card_physics_node.setAngularFactor(Vec3(0, 0, 1))

        self.health = 1

        self.add_task(self.collision_check, "collision_check")

    def collision_check(self, task):
        check = base.world.contactTest(self.card_physics_node)
        for contact in check.getContacts():
            if contact.getNode1().getName().find('Bullet') != -1:
                self.health -= 0.05

        if self.health < 0:
            self.card_physics_node.removeAllChildren()
            base.world.remove(self.card_physics_node)

        return Task.cont