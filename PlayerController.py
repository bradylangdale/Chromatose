from math import sin, pi, cos

from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.bullet import BulletCharacterControllerNode, BulletCapsuleShape, ZUp
from panda3d.core import NodePath, BitMask32, Vec3


class PlayerController(DirectObject):
    def __init__(self, camera: NodePath, win, world, worldNP):
        DirectObject.__init__(self)
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
        forwards = Vec3(cos((90 + self.camera.getH()) / 180 * pi), sin((90 + self.camera.getH()) / 180 * pi),
                        0).normalized()
        right = Vec3(cos(self.camera.getH() / 180 * pi), sin(self.camera.getH() / 180 * pi), 0).normalized()
        speed = Vec3(0, 0, 0)

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

        self.playerNode.setLinearMovement(speed, True)

        return Task.cont

    def scale(self, s, v):
        return Vec3(s * v.x, s * v.y, s * v.z)
