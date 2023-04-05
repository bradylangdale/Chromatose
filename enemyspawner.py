from random import randint

from panda3d.core import Vec3
from direct.gui.DirectGui import *

from billboardobject import BillBoardObject
from pathfinder import Pathfinder
from resourcepath import resource_path


class EnemySpawner():
    def __init__(self, location: Vec3, type: str, cooldown: float):
        self.location = location
        self.type = type

        if type == 'red':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/RedEnemy/base.png'))
        elif type == 'green':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/GreenEnemy/base.png'))
        elif type == 'blue':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/BlueEnemy/base.png'))
        elif type == 'random':
            self.tex = []
            self.tex.append(base.loader.loadTexture(resource_path('Assets/assets/RedEnemy/base.png')))
            self.tex.append(base.loader.loadTexture(resource_path('Assets/assets/GreenEnemy/base.png')))
            self.tex.append(base.loader.loadTexture(resource_path('Assets/assets/BlueEnemy/base.png')))

        self.pathfinder = Pathfinder()
        self.pathfinder.loadMap(resource_path('NavMeshes/defaultnavmesh.json'))

        self.cooldown = cooldown
        self.elapsed = 0

    def update(self, delta):
        self.elapsed += delta
        if self.elapsed >= self.cooldown:
            self.elapsed = 0
            if self.type != 'random':
                return BillBoardObject(self.tex, self.location, scale=1.5, drop=self.type, pathfinder=self.pathfinder)
            else:
                types = ['red', 'green', 'blue']
                return BillBoardObject(self.tex[randint(0, 2)], self.location, scale=1.5, drop=types[randint(0, 2)], pathfinder=self.pathfinder)
