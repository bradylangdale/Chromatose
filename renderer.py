from OpenGL.GL import *
from OpenGL.raw.GLU import gluPerspective
from PyQt6.QtOpenGLWidgets import QOpenGLWidget


class Renderer(QOpenGLWidget):

    def __init__(self, parent):
        super(Renderer, self).__init__(parent=parent)

        self.aspect = 0.5

        self.verticies = (
            (1, -1, -1),
            (1, 1, -1),
            (-1, 1, -1),
            (-1, -1, -1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, -1, 1),
            (-1, 1, 1)
        )

        self.edges = (
            (0, 1),
            (0, 3),
            (0, 4),
            (2, 1),
            (2, 3),
            (2, 7),
            (6, 3),
            (6, 4),
            (6, 7),
            (5, 1),
            (5, 4),
            (5, 7)
        )

        self.colors = (
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (0, 1, 0),
            (1, 1, 1),
            (0, 1, 1),
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 0, 0),
            (1, 1, 1),
            (0, 1, 1),
        )

        self.surfaces = (
            (0, 1, 2, 3),
            (3, 2, 7, 6),
            (6, 7, 5, 4),
            (4, 5, 1, 0),
            (1, 5, 7, 2),
            (4, 0, 3, 6)
        )

    def initializeGL(self) -> None:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)

        gluPerspective(45, self.aspect, 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)

    def paintGL(self) -> None:
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1, 1, 1)
        # glLoadIdentity()

        glRotatef(1, 3, 1, 1)
        self.Cube()
        # glScalef(self.cameraScale, self.cameraScale, 0)
        # glTranslatef(-self.cameraPosition[0], -self.cameraPosition[1], 0)

    def resizeGL(self, w, h) -> None:
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self.aspect = w / h
        gluPerspective(45, self.aspect, 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def Cube(self):
        glBegin(GL_QUADS)
        for surface in self.surfaces:
            x = 0
            for vertex in surface:
                x += 1
                glColor3fv(self.colors[x])
                glVertex3fv(self.verticies[vertex])
        glEnd()

        glBegin(GL_LINES)
        for edge in self.edges:
            for vertex in edge:
                glVertex3fv(self.verticies[vertex])
        glEnd()
