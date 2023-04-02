from math import sin, pi, cos, copysign

from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from panda3d.bullet import BulletCapsuleShape, ZUp, BulletRigidBodyNode
from panda3d.core import NodePath, BitMask32, Vec3, WindowProperties, AudioSound


class PlayerController(DirectObject):
    def __init__(self, camera: NodePath, win, position=Vec3(0, 0, 0)):
        DirectObject.__init__(self)
        self.camera = camera
        self.win = win

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
        self.accept('f', self.toggle_fullscreen)
        self.add_task(self.move, "move")
        self.add_task(self.rotate, "rotate")
        self.add_task(self.item_pickup, 'item_pickup')

        # Add Physics
        height = 3
        radius = 0.4
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)
        self.playerRB = BulletRigidBodyNode('Billboard')
        self.playerRB.setMass(0.1)
        self.playerRB.addShape(shape)
        base.world.attachRigidBody(self.playerRB)
        self.playerRBNode = base.render.attachNewNode(self.playerRB)
        self.playerRBNode.setPos(position)
        self.playerRBNode.setCollideMask(BitMask32.allOn())
        self.camera.reparentTo(self.playerRBNode)
        self.camera.setPos(0, 0, 1)

        # Make item upright
        self.playerRB.setAngularFactor(Vec3(0, 0, 0))
        self.playerRB.setFriction(0.7)
        self.playerRB.setLinearSleepThreshold(0)
        self.playerRB.setLinearDamping(0.3)

        self.lastPos = self.playerRBNode.getPos()

        self.gun = base.loader.loadModel('Assets/assets/Gun/Gun.bam')
        self.gun.setTwoSided(False, 1)
        self.gun.setScale(0.02, 0.02, 0.02)
        self.gun.flattenLight()
        self.gun.clear_model_nodes()
        self.gun.reparentTo(self.camera)
        self.gun.setH(90)
        self.gun.setPos(0.7, 0.5, -0.35)

        self.r = 1.0
        self.g = 1.0
        self.b = 1.0
        self.canJump = True
        self.fullscreen = False

        # Loading sound effects
        self.redChime = base.loader.loadSfx("Assets/assets/Sound/Effects/redChime.mp3")
        self.greenChime = base.loader.loadSfx("Assets/assets/Sound/Effects/greenChime.mp3")
        self.blueChime = base.loader.loadSfx("Assets/assets/Sound/Effects/blueChime.mp3")

        self.footsteps = base.loader.loadSfx("Assets/assets/Sound/Effects/footsteps.mp3")
        self.footsteps.setLoop(True)

        self.jumpEffect = base.loader.loadSfx("Assets/assets/Sound/Effects/jumpEffect.mp3")

        self.windEffect = base.loader.loadSfx("Assets/assets/Sound/Effects/wind.mp3")
        self.windEffect.setLoop(True)

        self.smallHeartbeat = base.loader.loadSfx("Assets/assets/Sound/Effects/smallHeartbeat.mp3")
        self.smallHeartbeat.setLoop(True)

        self.bigHeartbeat = base.loader.loadSfx("Assets/assets/Sound/Effects/bigHeartbeat.mp3")
        self.bigHeartbeat.setLoop(True)

        # Pause
        self.paused = False
        self.jumping = False
        self.jumpCD = 0

    def setPos(self, vec3):
        self.playerRBNode.setPos(vec3)

    def toggle_move_state(self, key, value):
        self.currentState[key] = value

    def rotate(self, task):
        if self.paused:
            return Task.cont
        mouse_sens = 0.05
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2):
            self.camera.setH(self.camera.getH() - (x - self.win.getXSize() / 2) * mouse_sens)
            self.camera.setP(self.camera.getP() - (y - self.win.getYSize() / 2) * mouse_sens)
        return Task.cont

    def move(self, task):
        if self.paused:
            return Task.cont
        forwards = Vec3(cos((90 + self.camera.getH()) / 180 * pi), sin((90 + self.camera.getH()) / 180 * pi),
                        0)
        right = Vec3(cos(self.camera.getH() / 180 * pi), sin(self.camera.getH() / 180 * pi), 0)
        speed = Vec3(0, 0, 0)
        current_speed = self.playerRB.getLinearVelocity()
        current_forward = self.signedMag(Vec3(current_speed.x * forwards.x, current_speed.y * forwards.y, 0))
        current_right = self.signedMag(Vec3(current_speed.x * right.x, current_speed.y * right.y, 0))

        contact = False

        check = base.world.contactTest(self.playerRB)
        for collider in check.getContacts():
            point = collider.getManifoldPoint()
            if point.getLocalPointA().z < -0.5:
                contact = True

                if not 'Walls' in collider.getNode1().getName() and self.jumpCD < 0:
                    self.canJump = True

        if self.currentState["forward"] and 15 > current_forward:
            speed += self.scale(3.0, forwards)
        if self.currentState["backward"] and -15 < current_forward:
            speed -= self.scale(3.0, forwards)
        if self.currentState["left"] and -15 < current_right:
            speed -= self.scale(3.0, right)
        if self.currentState["right"] and 15 > current_right:
            speed += self.scale(3.0, right)
        if self.currentState['jump']:
            if self.canJump:
                self.jumpEffect.play()
                self.canJump = False
                self.jumping = True
                self.currentState['jump'] = False
                speed.setZ(70)
                self.jumpCD = 1
            elif not self.canJump:
                self.currentState['jump'] = False

        if self.jumping and current_speed.z < 0.1:
            speed.setZ(70)
            self.jumpCD = 1
        else:
            self.jumping = False

        if self.jumpCD > 0:
            self.jumpCD -= 0.05

        if speed.length() > 0:
            self.playerRB.applyCentralForce(speed)
            self.playerRB.setLinearDamping(0.3)
            self.playerRB.setFriction(0.7)
        elif contact:
            self.playerRB.setLinearDamping(0.9)
            self.playerRB.setFriction(0.9)
        else:
            self.playerRB.setLinearDamping(0.3)
            self.playerRB.setFriction(0.3)

        dt = globalClock.getDt()
        self.vel = Vec3((self.playerRBNode.getX() - self.lastPos.x) / dt,
                        (self.playerRBNode.getY() - self.lastPos.y) / dt,
                        (self.playerRBNode.getZ() - self.lastPos.z) / dt)

        self.lastPos = self.playerRBNode.getPos()

        # Playing movement and status sounds
        if contact and self.currentState["forward"] or self.currentState["backward"] or self.currentState["left"] or \
                self.currentState["right"]:
            if self.footsteps.status() != AudioSound.PLAYING:
                self.footsteps.play()
        else:
            self.footsteps.stop()

        if not contact and self.windEffect.status() != AudioSound.PLAYING:
            self.windEffect.play()
        elif contact:
            self.windEffect.stop()

        if self.r < 0.1:
            self.smallHeartbeat.stop()
            if self.bigHeartbeat.status() != AudioSound.PLAYING:
                self.bigHeartbeat.play()
        elif self.r < 0.3:
            self.bigHeartbeat.stop()
            if self.smallHeartbeat.status() != AudioSound.PLAYING:
                self.smallHeartbeat.play()
        else:
            self.smallHeartbeat.stop()
            self.bigHeartbeat.stop()

        return Task.cont

    def item_pickup(self, task):
        contact = False

        check = base.world.contactTest(self.playerRB)
        for contact in check.getContacts():
            point = contact.getManifoldPoint()

            if 'red_crystal' in contact.getNode1().getName():
                self.redChime.play()
                self.r += 0.1
                contact.getNode1().removeAllChildren()
                base.world.remove(contact.getNode1())

            elif 'green_crystal' in contact.getNode1().getName():
                self.greenChime.play()
                self.g += 0.1
                contact.getNode1().removeAllChildren()
                base.world.remove(contact.getNode1())

            elif 'blue_crystal' in contact.getNode1().getName():
                self.blueChime.play()
                self.b += 0.1
                contact.getNode1().removeAllChildren()
                base.world.remove(contact.getNode1())

        return Task.cont

    def scale(self, s, v):
        return Vec3(s * v.x, s * v.y, s * v.z)

    def signedMag(self, vec):
        return copysign(1, vec.x + vec.y) * vec.length()

    def toggle_fullscreen(self):
        if not self.fullscreen:
            props = WindowProperties()
            props.setFullscreen(1)
            props.setSize(1920, 1080)
            base.win.requestProperties(props)
            self.fullscreen = True
        else:
            props = WindowProperties()
            props.setFullscreen(0)
            props.setSize(640, 480)
            base.win.requestProperties(props)
            self.fullscreen = False
