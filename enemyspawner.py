from panda3d.core import Vec3
from direct.gui.DirectGui import *

from billboardobject import BillBoardObject
from resourcepath import resource_path

class EnemySpawner():
    def __init__(self, enemies: list, location: Vec3, type: str, cooldown: float, enemyCap: int):
        self.enemies = enemies
        self.location = location
        self.type = type
        
        if type == 'red':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/RedEnemy/base.png'))
        elif type == 'green':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/GreenEnemy/base.png'))
        elif type == 'blue':
            self.tex = base.loader.loadTexture(resource_path('Assets/assets/BlueEnemy/base.png'))
        self.cooldown = cooldown
        self.elapsed = 0
        self.enemyCap = enemyCap
    
    def update(self, delta):
        self.elapsed += delta
        if self.elapsed >= self.cooldown and len(self.enemies) < self.enemyCap:
            self.elapsed = 0
            self.enemies.append(BillBoardObject(self.tex, self.location, scale=1.5))