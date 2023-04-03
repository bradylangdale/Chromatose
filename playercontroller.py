import os
import sys
from math import sin, pi, cos, copysign
from random import randint

from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from panda3d.bullet import BulletCapsuleShape, ZUp, BulletRigidBodyNode, BulletConvexHullShape
from panda3d.core import NodePath, BitMask32, Vec3, WindowProperties, AudioSound
from direct.gui.DirectGui import DGG
from verticalbar import UISlider

from bulletmanager import BulletManager


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = '/' + os.path.join(base_path, relative_path).replace('\\', '/').replace('C:', 'c')
    return path


class PlayerController(DirectObject):
    def __init__(self, camera: NodePath, win, position=Vec3(0, 0, 0)):
        DirectObject.__init__(self)
        self.camera = camera
        self.win = win

        self.currentState = {"forward": False, "backward": False, "left": False,
                             "right": False, 'jump': False, 'm-left': False, 'm-right': False}
        self.accept("w", self.toggle_key_state, ["forward", True])
        self.accept("w-up", self.toggle_key_state, ["forward", False])
        self.accept("s", self.toggle_key_state, ["backward", True])
        self.accept("s-up", self.toggle_key_state, ["backward", False])
        self.accept("a", self.toggle_key_state, ["left", True])
        self.accept("a-up", self.toggle_key_state, ["left", False])
        self.accept("d", self.toggle_key_state, ["right", True])
        self.accept("d-up", self.toggle_key_state, ["right", False])
        self.accept('space', self.toggle_key_state, ['jump', True])
        self.accept('mouse1', self.toggle_key_state, ['m-left', True])
        self.accept('mouse1-up', self.toggle_key_state, ['m-left', False])
        self.accept('mouse3', self.toggle_key_state, ['m-right', True])
        self.accept('mouse3-up', self.toggle_key_state, ['m-right', False])
        self.accept('f', self.toggle_fullscreen)
        self.add_task(self.move, "move")
        self.add_task(self.rotate, "rotate")
        self.add_task(self.item_pickup, 'item_pickup')
        self.add_task(self.handle_mouse, 'mouse')

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

        self.gun = base.loader.loadModel('Assets/assets/Gun/Gun.bam')
        self.gun.setTwoSided(False, 1)
        self.gun.setScale(0.02, 0.02, 0.02)
        self.gun.flattenLight()
        self.gun.clear_model_nodes()

        self.shield = base.loader.loadModel('Assets/assets/Shield/Shield.bam')
        #self.shield.setTwoSided(False, 1)
        self.shield.flattenLight()
        self.shield.clear_model_nodes()
        self.shield.reparentTo(self.playerRBNode)
        self.shield.setH(90)
        self.shield.setPos(0, 0, 0)
        self.shieldRotate = self.shield.hprInterval(10, Vec3(-360, 0, 0))
        self.shieldRotate.loop()
        self.shield.setScale(0.001, 0.001, 0.001)

        self.r = 1.0
        self.g = 1.0
        self.b = 1.0

        self.canJump = True
        self.fullscreen = False

        # Loading sound effects
        self.redChime = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/redChime.mp3"))
        self.greenChime = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/greenChime.mp3"))
        self.blueChime = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/blueChime.mp3"))

        self.footsteps = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/footsteps.mp3"))
        self.footsteps.setLoop(True)

        self.jumpEffect = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/jumpEffect.mp3"))

        self.windEffect = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/wind.mp3"))
        self.windEffect.setLoop(True)

        self.smallHeartbeat = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/smallHeartbeat.mp3"))
        self.smallHeartbeat.setLoop(True)

        self.bigHeartbeat = base.loader.loadSfx(resource_path("Assets/assets/Sound/Effects/bigHeartbeat.mp3"))
        self.bigHeartbeat.setLoop(True)

        # bullet manager
        self.bullets = BulletManager()

        # Pause
        self.paused = True
                
        # cooldowns & states
        self.jumping = False
        self.jumpCD = 0
        self.shootCD = 0
        self.shieldDeployed = False

        # Color meters
        scale_factor = min(base.win.getXSize(), base.win.getYSize()) / 1000
        self.blueMeter = self.create_meter((0, 0, 1, 0.8), (-0.95 * scale_factor - 0.55, 0, 0), scale_factor)
        self.redMeter = self.create_meter((1, 0, 0, 0.8), (-0.85 * scale_factor - 0.55, 0, 0), scale_factor)
        self.greenMeter = self.create_meter((0, 1, 0, 0.8), (-0.75 * scale_factor - 0.55, 0, 0), scale_factor)
        self.r = 0
        self.b = 0
        self.g = 0
        self.greenMeter['value'] = 0
        self.redMeter['value'] = 0
        self.blueMeter['value'] = 0

        self.player_camera_pos = self.camera.getPos()
        self.player_camera_hpr = self.camera.getHpr()


    def setPos(self, vec3):
        self.playerRBNode.setPos(vec3)

    def toggle_key_state(self, key, value):
        self.currentState[key] = value

    def handle_mouse(self, task):
        if self.currentState['m-left'] and self.shootCD < 0 and self.g > 0:
            # get bullet spawn position from gun position
            position = base.render.getRelativePoint(self.camera, (0.7, 2.25, -0.35))

            # cast ray forward to find target point
            forwards = base.camera.getQuat().getForward()
            pFrom = base.render.getRelativePoint(self.camera, self.camera.getPos())
            pTo = pFrom + (forwards * 100)

            # make sure the bullet goes toward the crosshair else default forward
            impulse = forwards
            result = base.world.rayTestClosest(pFrom, pTo)
            if result.hasHit():
                impulse = result.getHitPos() - position
                impulse.normalize()

            self.bullets.spawn(position, impulse * 0.5)
            self.shootCD = 1
            self.g -= 0.025

        if self.currentState['m-right'] and not self.shieldDeployed and self.b > 0:
            expand = self.shield.scaleInterval(0.2, Vec3(1.5, 1.5, 1.5))
            expand.start()
            self.shieldDeployed = True
        elif self.shieldDeployed:
            shrink = self.shield.scaleInterval(0.2, Vec3(0.001, 0.001, 0.001))
            shrink.start()
            self.shieldDeployed = False

        if self.shootCD >= 0:
            self.shootCD -= 0.05

        if self.shieldDeployed and self.b > 0:
            self.b -= 0.005

        return Task.cont

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

        self.player_camera_pos = self.camera.getPos()
        self.player_camera_hpr = self.camera.getHpr()
        return Task.cont

    def move(self, task):
        if self.paused:
            self.windEffect.stop()
            self.footsteps.stop()
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

        if self.jumpCD >= 0:
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
        self.player_camera_pos = self.camera.getPos()
        self.player_camera_hpr = self.camera.getHpr()
        return Task.cont

    def item_pickup(self, task):
        contact = False

        check = base.world.contactTest(self.playerRB)
        for contact in check.getContacts():
            point = contact.getManifoldPoint()

            if 'red_crystal' in contact.getNode1().getName() and self.r < 1:
                self.redChime.play()
                self.r += 0.1
                self.redMeter['value'] = self.r
                contact.getNode1().removeAllChildren()
                base.world.remove(contact.getNode1())

            elif 'green_crystal' in contact.getNode1().getName() and self.g < 1:
                self.greenChime.play()
                self.g += 0.1
                self.greenMeter['value'] = self.g
                contact.getNode1().removeAllChildren()
                base.world.remove(contact.getNode1())

            elif 'blue_crystal' in contact.getNode1().getName() and self.b < 1:
                self.blueChime.play()
                self.b += 0.1
                self.blueMeter['value'] = self.b
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

    def create_meter(self, fg_color, pos, scale_factor):
        multiplier = 1
        meter = UISlider(
            allowprogressBar= True,
            frameSize=(-0.17*scale_factor*multiplier,0.17*scale_factor*multiplier,-0.5*scale_factor*multiplier,0.5*scale_factor*multiplier),
            pos=pos,
            value=0.6,
            orientation=DGG.VERTICAL,
            relief=DGG.RAISED,
            progressBar_frameColor=fg_color,
            thumb_frameSize=(0,0,0,0),
            thumb_frameColor=(1,1,1, 0),
        )

        return meter

    def set_player_view(self):
        self.camera.setPos(self.player_camera_pos)
        self.camera.setHpr(self.player_camera_hpr)
        self.gun.reparentTo(self.camera)
        self.gun.setH(90)
        self.gun.setPos(0.7, 0.5, -0.35)


