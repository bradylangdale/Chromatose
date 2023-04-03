import math
import random

from direct.interval.MetaInterval import Sequence, Parallel
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.filter.CommonFilters import CommonFilters
from panda3d.core import WindowProperties, Vec3, AntialiasAttrib, AmbientLight, LVector4, LPoint3, Spotlight, \
    loadPrcFile
from direct.gui.DirectGui import *
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletDebugNode, BulletTriangleMesh, \
    BulletTriangleMeshShape, BulletPlaneShape, BulletConvexHullShape

from crystalobject import CrystalObject
from interactableobject import InteractableObject
from pipeline import CustomPipeline
from playercontroller import PlayerController
from billboardobject import BillBoardObject
from pausemenu import PauseMenu

from enemyspawner import EnemySpawner
from resourcepath import resource_path
from startscreen import StartScreen
from math import sin, cos, radians

loadPrcFile(resource_path('Config.prc'))
loadPrcFile(resource_path('Confauto.prc'))

DEBUG = False


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.filters = CommonFilters(self.win, self.cam)
        base.setBackgroundColor(0.04, 0.04, 0.04)

        self.pipeline = CustomPipeline(manager=self.filters.manager)
        self.pipeline.enable_shadows = True

        # set the camera's lens to the one we just created
        self.cam.node().getLens().setFov(120)
        self.cam.node().getLens().setNearFar(0.1, 10000)
        self.cam.setAntialias(AntialiasAttrib.MAuto)

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
        self.player = PlayerController(self.camera, self.win)

        self.player.setPos(self.camera.getPos() - Vec3(0, 20, 0))

        # Load Map Mesh
        mScale = 4
        self.floor = self.loader.loadModel(resource_path("Assets/assets/Mapv2/Floor/floor.bam"))
        self.floor.setTwoSided(False, 1)
        self.floor.setScale(mScale, mScale, mScale)
        self.floor.clear_model_nodes()
        self.floor.flatten_strong()
        self.floor.reparentTo(self.render)

        self.colorPlane = self.loader.loadModel(resource_path("Assets/assets/Mapv2/ColorPlane/colorplane.bam"))
        self.colorPlane.setTwoSided(False, 1)
        self.colorPlane.setScale(mScale, mScale, mScale)
        self.colorPlane.clear_model_nodes()
        self.colorPlane.flatten_strong()
        self.colorPlane.setShaderAuto()
        colorRotate = self.colorPlane.hprInterval(50, LPoint3(360, 0, 0))
        colorMove1 = self.colorPlane.posInterval(10, LPoint3(0, -15, 0))
        colorMove2 = self.colorPlane.posInterval(10, LPoint3(-15, 0, 0))
        colorMove3 = self.colorPlane.posInterval(10, LPoint3(0, 15, 0))
        colorMove4 = self.colorPlane.posInterval(10, LPoint3(15, 0, 0))
        colorMove5 = self.colorPlane.posInterval(10, LPoint3(0, 0, 0))
        colorMovement = Sequence(colorMove1, colorMove2, colorMove3, colorMove4, colorMove5)
        self.colorAnimation = Parallel(colorMovement, colorRotate)
        self.colorAnimation.loop()
        self.colorPlane.reparentTo(self.render)

        self.walls = self.loader.loadModel(resource_path("Assets/assets/Mapv2/Walls/wall.bam"))
        self.walls.setTwoSided(False, 1)
        self.walls.setScale(mScale, mScale, mScale)
        self.walls.clear_model_nodes()
        self.walls.flatten_strong()
        geom = self.walls.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        node = BulletRigidBodyNode('Walls')
        node.addShape(shape)
        self.np = self.render.attachNewNode(node)
        self.world.attachRigidBody(node)
        self.walls.reparentTo(self.np)

        self.pillar_model = self.loader.loadModel(resource_path("Assets/assets/Mapv2/Pillar/pillar.bam"))
        self.pillar_model.setTwoSided(False, 1)
        self.pillar_model.setScale(mScale, mScale, mScale)
        self.pillar_model.clear_model_nodes()
        self.pillar_model.flatten_strong()
        geom = self.pillar_model.findAllMatches('**/+GeomNode')[0].node().getGeom(0)
        shape = BulletConvexHullShape()
        shape.addGeom(geom)
        node = BulletRigidBodyNode('Pillar')
        node.addShape(shape)

        self.pillars = []
        pillar_offset = Vec3(-26, 28.33, 2.1)

        # pillar 1
        rb = node.make_copy()
        self.pillars.append(self.render.attachNewNode(rb))
        self.pillars[-1].setPos(0, 0, 0)
        self.world.attachRigidBody(rb)
        self.pillar_model.copyTo(self.pillars[-1])

        # pillar 2
        rb = node.make_copy()
        self.pillars.append(self.render.attachNewNode(rb))
        self.pillars[-1].setPos(Vec3(26, 28.33, 2.1) - pillar_offset)
        self.world.attachRigidBody(rb)
        self.pillar_model.copyTo(self.pillars[-1])

        # pillar 3
        rb = node.make_copy()
        self.pillars.append(self.render.attachNewNode(rb))
        self.pillars[-1].setPos(Vec3(26, -28.33, 2.1) - pillar_offset)
        self.world.attachRigidBody(rb)
        self.pillar_model.copyTo(self.pillars[-1])

        # pillar 4
        rb = node.make_copy()
        self.pillars.append(self.render.attachNewNode(rb))
        self.pillars[-1].setPos(Vec3(-26, -28.33, 2.1) - pillar_offset)
        self.world.attachRigidBody(rb)
        self.pillar_model.copyTo(self.pillars[-1])

        # pillar 5
        rb = node.make_copy()
        self.pillars.append(self.render.attachNewNode(rb))
        self.pillars[-1].setPos(Vec3(0, 0, 2.1) - pillar_offset)
        self.world.attachRigidBody(rb)
        self.pillar_model.copyTo(self.pillars[-1])

        # Plane (should keep things from falling through)
        shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -0.4)
        self.world.attachRigidBody(node)

        # Add Billboard Enemies
        self.enemiesLimit = 10
        self.enemies = []
        self.enemySpawners = []
        self.enemySpawners.append(EnemySpawner(Vec3(-36.5, -35.4, 2.1), "random", 2))
        self.enemySpawners.append(EnemySpawner(Vec3(36.5, -35.4, 2.1), "random", 2))
        self.enemySpawners.append(EnemySpawner(Vec3(-36.5, 35.4, 2.1), "random", 2))
        self.enemySpawners.append(EnemySpawner(Vec3(36.5, 35.4, 2.1), "random", 2))
        self.enemySpawners.append(EnemySpawner(Vec3(43, 0, 2.1), "random", 2))
        self.enemySpawners.append(EnemySpawner(Vec3(-43, 0, 2.1), "random", 2))

        self.light = self.render.attachNewNode(Spotlight("Sun"))
        self.light.node().setScene(self.render)
        self.light.node().setShadowCaster(True, 4096, 4096)
        self.light.node().setColor((1, 1, 1, 1))
        # self.light.node().showFrustum()
        self.light.node().getLens().setFov(90)
        self.light.node().getLens().setNearFar(1, 10000)
        self.light.setPos(-15, -15, 100)
        self.light.lookAt(0, 15, 0)
        self.render.setLight(self.light)

        self.alight = self.render.attachNewNode(AmbientLight("Ambient"))
        self.alight.node().setColor(LVector4(0.2, 0.2, 0.2, 1))
        self.render.setLight(self.alight)

        # Important! Enable the shader generator.
        self.filters.setSrgbEncode()
        self.filters.setHighDynamicRange()
        self.filters.setGammaAdjust(1.4)
        self.filters.setExposureAdjust(0.5)
        self.filters.setBloom((0.4, 0.4, 0.8, 0.2), desat=0.1, mintrigger=0.01, intensity=0.5, size='medium')

        # loading and playing music
        mysteryMusic = base.loader.loadSfx(resource_path("Assets/assets/Sound/Music/mystery.mp3"))
        mysteryMusic.setLoop(True)
        mysteryMusic.setVolume(0.1)
        mysteryMusic.play()

        self.add_task(self.update, 'update')

        # Start Screen
        self.pauseMenu = PauseMenu(self)
        self.pauseMenu.lock_keys_mouse()
        self.game_started = False
        self.start_screen = StartScreen(self.aspect2d, self.start_game)
        self.taskMgr.add(self.rotate_wait_screen_camera, "rotate_wait_screen_camera")

    def reset(self):
        self.player.playerRBNode.setPos(random.uniform(-10, 10), random.uniform(-10, 10), 2)
        self.player.r = 0.5
        self.player.g = 0.5
        self.player.b = 0.5
        self.player.score = 0
        self.player.scoreLabel.setText('Score: 0')

        for crystal in self.render.findAllMatches("**/*crystal"):
            crystal.node().removeAllChildren()
            self.world.remove(crystal.node())

        for bullet in self.render.findAllMatches("**/*Bullet"):
            bullet.node().removeAllChildren()
            self.world.remove(bullet.node())

        for enemy in self.enemies:
            enemy.card_physics_node.removeAllChildren()
            self.world.remove(enemy.card_physics_node)
        self.enemies.clear()

    # Update
    def update(self, task):
        if self.pauseMenu.paused or not self.game_started:
            return task.cont
        if self.player.r < 0:
            self.pauseMenu.display_score(self.player.score)
            self.reset()
            return task.cont
        dt = globalClock.getDt()
        self.world.doPhysics(dt)

        ''' This a neat effect but idk if we want it
        colorMag = Vec3(self.player.r, self.player.g, self.player.b).length()
        amount = self.interpolate(0.9, 0, colorMag/1.8)
        amount = min(max(0, amount), 1)
        self.filters.setCartoonInk(amount, color=[1, 1, 1, 1])
        '''

        # self.updateColors(self.colorPlane, [-3, -5, -1.5], [1, 1, 1])  # use with directional
        self.updateColors(self.colorPlane, [0, 0, 0], [1, 1, 1])  # use with spotlight
        self.updateColors(self.walls, [-140, -110, -90], [1, 1, 1])
        self.updateColors(self.player.gun, [-6, -6, -6], [256, 256, 256])

        for pillar in self.pillars:
            self.updateColors(pillar, [-6, -6, -6], [1, 1, 1])

        self.player.shield.setColorScale(self.player.r, self.player.g, self.player.b, 1.0)

        # for crystals in self.crystals:
        #    crystals.np.setColorScale(self.player.r, self.player.g, self.player.b, 1.0)

        self.updateEnemies()

        for enemySpawner in self.enemySpawners:
            if len(self.enemies) < int(self.enemiesLimit + math.sqrt(self.player.score)):
                enemy = enemySpawner.update(dt)
                if enemy is not None:
                    self.enemies.append(enemy)

        return task.cont

    def updateEnemies(self):
        # Making enemies go to player
        new_enemies = []
        playerPos = self.player.playerRBNode.getPos()
        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.move_toward(playerPos)
                new_enemies.append(enemy)
            else:
                self.player.score += 1
                self.player.scoreLabel.setText('Score: ' + str(self.player.score))

        self.enemies = new_enemies

    def updateColors(self, model, start, end):
        model.setColorScale(self.interpolate(start[0], end[0], min(max(0, self.player.r), 1)),
                            self.interpolate(start[1], end[1], min(max(0, self.player.g), 1)),
                            self.interpolate(start[2], end[2], min(max(0, self.player.b), 1)),
                            1.0)

    def interpolate(self, start, end, percent):
        return ((end - start) * percent) + start

    def start_game(self):
        self.crosshair = OnscreenText(text='+', pos=(0, 0), scale=0.1, fg=(1, 1, 1, 1))
        self.player.set_player_view()
        self.game_started = True
        self.start_screen.hide()
        self.start_screen.__KillImage__()
        self.pauseMenu.release_keys_mouse()

        self.player.r = 0.5
        self.player.g = 0.5
        self.player.b = 0.5

        self.player.redMeter.show()
        self.player.greenMeter.show()
        self.player.blueMeter.show()
        self.player.scoreLabel.setText('Score: 0')

    def rotate_wait_screen_camera(self, task):
        if not self.game_started:
            orbit_radius = 45
            orbit_center = LPoint3(0, 20, 0)
            orbit_speed = 10
            eval_angle = 30

            # Compute the new angle in degrees
            angle_deg = (task.time * orbit_speed) % 360
            angle_rad = radians(angle_deg)
            eval_rad = radians(eval_angle)

            # Convert polar coordinates to Cartesian coordinates
            x = orbit_center.x + orbit_radius * cos(angle_rad) * cos(eval_rad)
            y = orbit_center.y + orbit_radius * sin(angle_rad) * cos(eval_rad)
            z = orbit_center.z + orbit_radius * sin(eval_rad)

            # Update the wait screen camera's position and orientation
            self.camera.setPos(x, y, z)
            self.camera.lookAt(orbit_center)
            return task.cont
        else:
            return task.done


app = MyApp()
props = WindowProperties()
app.win.requestProperties(props)
app.run()
