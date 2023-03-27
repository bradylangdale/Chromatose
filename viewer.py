"""A pyglet-based interactive 3D scene viewer.
"""
import copy
import os
import sys
from threading import Thread, RLock
import time
from trimesh.transformations import quaternion_multiply
import imageio
import numpy as np
import OpenGL
from pyrender import Node, DirectionalLight, PerspectiveCamera, IntrinsicsCamera, OrthographicCamera, Renderer
from pyrender.constants import DEFAULT_Z_FAR, DEFAULT_Z_NEAR, DEFAULT_SCENE_SCALE, TARGET_OPEN_GL_MAJOR, \
    TARGET_OPEN_GL_MINOR, MIN_OPEN_GL_MAJOR, MIN_OPEN_GL_MINOR, RenderFlags

import pyglet
from pyglet import clock

from camera_controller import CameraController

pyglet.options['shadow_window'] = False


class CustomViewer(pyglet.window.Window):

    def __init__(self, scene, **kwargs):
        self._scene = scene
        self._viewport_size = (640, 480)
        self._render_lock = RLock()
        self._is_active = False
        self._should_close = False
        self._run_in_thread = True
        self._auto_start = True

        self._default_render_flags = {
            'flip_wireframe': False,
            'all_wireframe': False,
            'all_solid': False,
            'shadows': False,
            'vertex_normals': False,
            'face_normals': False,
            'cull_faces': True,
            'point_size': 1.0,
        }
        self._default_viewer_flags = {
            'mouse_pressed': False,
            'rotate': False,
            'rotate_rate': np.pi / 3.0,
            'rotate_axis': np.array([0.0, 0.0, 0.0]),
            'view_center': None,
            'record': False,
            'use_raymond_lighting': True,
            'use_direct_lighting': False,
            'lighting_intensity': 3.0,
            'use_perspective_cam': True,
            'save_directory': None,
            'window_title': 'Scene Viewer',
            'refresh_rate': 30.0,
            'fullscreen': False,
            'show_world_axis': False,
            'show_mesh_axes': False,
            'caption': None
        }
        self._render_flags = self._default_render_flags.copy()
        self._viewer_flags = self._default_viewer_flags.copy()
        self._viewer_flags['rotate_axis'] = (
            self._default_viewer_flags['rotate_axis'].copy()
        )

        for key in kwargs:
            if key in self.render_flags:
                self._render_flags[key] = kwargs[key]
            elif key in self.viewer_flags:
                self._viewer_flags[key] = kwargs[key]

        # TODO MAC OS BUG FOR SHADOWS
        if sys.platform == 'darwin':
            self._render_flags['shadows'] = False

        self._registered_keys = {}

        #######################################################################
        # Save internal settings
        #######################################################################

        # Set up raymond lights and direct lights
        self._raymond_lights = self._create_raymond_lights()
        self._direct_light = self._create_direct_light()

        #######################################################################
        # Set up camera node
        #######################################################################
        self._camera_node = None
        self._prior_main_camera_node = None
        self._default_camera_pose = None
        self._default_persp_cam = None
        self._default_orth_cam = None
        self._cam_control = None
        self._saved_frames = []

        # Extract main camera from scene and set up our mirrored copy
        znear = None
        zfar = None
        if scene.main_camera_node is not None:
            n = scene.main_camera_node
            camera = copy.copy(n.camera)
            if isinstance(camera, (PerspectiveCamera, IntrinsicsCamera)):
                self._default_persp_cam = camera
                znear = camera.znear
                zfar = camera.zfar
            elif isinstance(camera, OrthographicCamera):
                self._default_orth_cam = camera
                znear = camera.znear
                zfar = camera.zfar
            self._default_camera_pose = scene.get_pose(scene.main_camera_node)
            self._prior_main_camera_node = n

        # Set defaults as needed
        zfar = max(scene.scale * 10.0, DEFAULT_Z_FAR)

        if scene.scale == 0:
            znear = DEFAULT_Z_NEAR
        else:
            znear = min(scene.scale / 10.0, DEFAULT_Z_NEAR)

        self._default_persp_cam = PerspectiveCamera(
            yfov=np.pi / 3.0, znear=znear, zfar=zfar
        )

        self._default_camera_pose = self._compute_initial_camera_pose()

        # Pick camera
        if self.viewer_flags['use_perspective_cam']:
            camera = self._default_persp_cam
        else:
            camera = self._default_orth_cam

        self._camera_node = Node(
            matrix=self._default_camera_pose, camera=camera
        )
        scene.add_node(self._camera_node)
        scene.main_camera_node = self._camera_node
        self._reset_view()

        #######################################################################
        # Initialize OpenGL context and renderer
        #######################################################################
        self._renderer = Renderer(
            self._viewport_size[0], self._viewport_size[1],
            self.render_flags['point_size']
        )
        self._is_active = True

        self._thread = Thread(target=self._init_and_start_app)
        self._thread.start()

    def start(self):
        self._init_and_start_app()

    @property
    def scene(self):
        """:class:`.Scene` : The scene being visualized.
        """
        return self._scene

    @property
    def viewport_size(self):
        """(2,) int : The width and height of the viewing window.
        """
        return self._viewport_size

    @property
    def render_lock(self):
        """:class:`threading.RLock` : If acquired, prevents the viewer from
        rendering until released.

        Run :meth:`.Viewer.render_lock.acquire` before making updates to
        the scene in a different thread, and run
        :meth:`.Viewer.render_lock.release` once you're done to let the viewer
        continue.
        """
        return self._render_lock

    @property
    def is_active(self):
        """bool : `True` if the viewer is active, or `False` if it has
        been closed.
        """
        return self._is_active

    @property
    def run_in_thread(self):
        """bool : Whether the viewer was run in a separate thread.
        """
        return self._run_in_thread

    @property
    def render_flags(self):
        """dict : Flags for controlling the renderer's behavior.

        - ``flip_wireframe``: `bool`, If `True`, all objects will have their
          wireframe modes flipped from what their material indicates.
          Defaults to `False`.
        - ``all_wireframe``: `bool`, If `True`, all objects will be rendered
          in wireframe mode. Defaults to `False`.
        - ``all_solid``: `bool`, If `True`, all objects will be rendered in
          solid mode. Defaults to `False`.
        - ``shadows``: `bool`, If `True`, shadows will be rendered.
          Defaults to `False`.
        - ``vertex_normals``: `bool`, If `True`, vertex normals will be
          rendered as blue lines. Defaults to `False`.
        - ``face_normals``: `bool`, If `True`, face normals will be rendered as
          blue lines. Defaults to `False`.
        - ``cull_faces``: `bool`, If `True`, backfaces will be culled.
          Defaults to `True`.
        - ``point_size`` : float, The point size in pixels. Defaults to 1px.

        """
        return self._render_flags

    @render_flags.setter
    def render_flags(self, value):
        self._render_flags = value

    @property
    def viewer_flags(self):
        """dict : Flags for controlling the viewer's behavior.

        The valid keys for ``viewer_flags`` are as follows:

        - ``rotate``: `bool`, If `True`, the scene's camera will rotate
          about an axis. Defaults to `False`.
        - ``rotate_rate``: `float`, The rate of rotation in radians per second.
          Defaults to `PI / 3.0`.
        - ``rotate_axis``: `(3,) float`, The axis in world coordinates to
          rotate about. Defaults to ``[0,0,1]``.
        - ``view_center``: `(3,) float`, The position to rotate the scene
          about. Defaults to the scene's centroid.
        - ``use_raymond_lighting``: `bool`, If `True`, an additional set of
          three directional lights that move with the camera will be added to
          the scene. Defaults to `False`.
        - ``use_direct_lighting``: `bool`, If `True`, an additional directional
          light that moves with the camera and points out of it will be
          added to the scene. Defaults to `False`.
        - ``lighting_intensity``: `float`, The overall intensity of the
          viewer's additional lights (when they're in use). Defaults to 3.0.
        - ``use_perspective_cam``: `bool`, If `True`, a perspective camera will
          be used. Otherwise, an orthographic camera is used. Defaults to
          `True`.
        - ``save_directory``: `str`, A directory to open the file dialogs in.
          Defaults to `None`.
        - ``window_title``: `str`, A title for the viewer's application window.
          Defaults to `"Scene Viewer"`.
        - ``refresh_rate``: `float`, A refresh rate for rendering, in Hertz.
          Defaults to `30.0`.
        - ``fullscreen``: `bool`, Whether to make viewer fullscreen.
          Defaults to `False`.
        - ``show_world_axis``: `bool`, Whether to show the world axis.
          Defaults to `False`.
        - ``show_mesh_axes``: `bool`, Whether to show the individual mesh axes.
          Defaults to `False`.
        - ``caption``: `list of dict`, Text caption(s) to display on
          the viewer. Defaults to `None`.

        """
        return self._viewer_flags

    @viewer_flags.setter
    def viewer_flags(self, value):
        self._viewer_flags = value

    @property
    def registered_keys(self):
        """dict : Map from ASCII key character to a handler function.

        This is a map from ASCII key characters to tuples containing:

        - A function to be called whenever the key is pressed,
          whose first argument will be the viewer itself.
        - (Optionally) A list of additional positional arguments
          to be passed to the function.
        - (Optionally) A dict of keyword arguments to be passed
          to the function.

        """
        return self._registered_keys

    @registered_keys.setter
    def registered_keys(self, value):
        self._registered_keys = value

    def close_external(self):
        """Close the viewer from another thread.

        This function will wait for the actual close, so you immediately
        manipulate the scene afterwards.
        """
        self._should_close = True
        while self.is_active:
            time.sleep(1.0 / self.viewer_flags['refresh_rate'])

    def save_gif(self, filename=None):
        """Save the stored GIF frames to a file.

        To use this asynchronously, run the viewer with the ``record``
        flag and the ``run_in_thread`` flags set.
        Kill the viewer after your desired time with
        :meth:`.Viewer.close_external`, and then call :meth:`.Viewer.save_gif`.

        Parameters
        ----------
        filename : str
            The file to save the GIF to. If not specified,
            a file dialog will be opened to ask the user where
            to save the GIF file.
        """
        if filename is None:
            filename = self._get_save_filename(['gif', 'all'])
        if filename is not None:
            self.viewer_flags['save_directory'] = os.path.dirname(filename)
            imageio.mimwrite(filename, self._saved_frames,
                             fps=self.viewer_flags['refresh_rate'],
                             palettesize=128, subrectangles=True)
        self._saved_frames = []

    def on_close(self):
        """Exit the event loop when the window is closed.
        """
        # Remove our camera and restore the prior one
        if self._camera_node is not None:
            self.scene.remove_node(self._camera_node)
        if self._prior_main_camera_node is not None:
            self.scene.main_camera_node = self._prior_main_camera_node

        # Delete any lighting nodes that we've attached
        if self.viewer_flags['use_raymond_lighting']:
            for n in self._raymond_lights:
                if self.scene.has_node(n):
                    self.scene.remove_node(n)
        if self.viewer_flags['use_direct_lighting']:
            if self.scene.has_node(self._direct_light):
                self.scene.remove_node(self._direct_light)

        # Delete renderer
        if self._renderer is not None:
            self._renderer.delete()
        self._renderer = None

        # Force clean-up of OpenGL context data
        try:
            OpenGL.contextdata.cleanupContext()
            self.close()
        except Exception:
            pass
        finally:
            self._is_active = False
            super(CustomViewer, self).on_close()
            pyglet.app.exit()

    def on_draw(self):
        """Redraw the scene into the viewing window.
        """
        if self._renderer is None:
            return

        if self.run_in_thread or not self._auto_start:
            self.render_lock.acquire()

        # Make OpenGL context current
        self.switch_to()

        # Render the scene
        self.clear()
        self._render()

        if self.run_in_thread or not self._auto_start:
            self.render_lock.release()

    def on_resize(self, width, height):
        """Resize the camera and CameraController when the window is resized.
        """
        if self._renderer is None:
            return

        self._viewport_size = (width, height)
        self._cam_control.resize(self._viewport_size)
        self._renderer.viewport_width = self._viewport_size[0]
        self._renderer.viewport_height = self._viewport_size[1]
        self.on_draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Record an initial mouse press.
        """
        self._cam_control.set_state(CameraController.STATE_ROTATE)
        if buttons == pyglet.window.mouse.LEFT:
            ctrl = (modifiers & pyglet.window.key.MOD_CTRL)
            shift = (modifiers & pyglet.window.key.MOD_SHIFT)
            if (ctrl and shift):
                self._cam_control.set_state(CameraController.STATE_ZOOM)
            elif ctrl:
                self._cam_control.set_state(CameraController.STATE_ROLL)
            elif shift:
                self._cam_control.set_state(CameraController.STATE_PAN)
        elif buttons == pyglet.window.mouse.MIDDLE:
            self._cam_control.set_state(CameraController.STATE_PAN)
        elif buttons == pyglet.window.mouse.RIGHT:
            self._cam_control.set_state(CameraController.STATE_ZOOM)

        self._cam_control.down(np.array([x, y]))

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Record a mouse drag.
        """
        self._cam_control.drag(np.array([x, y]))

    def on_mouse_release(self, x, y, button, modifiers):
        """Record a mouse release.
        """
        pass

    def on_mouse_scroll(self, x, y, dx, dy):
        """Record a mouse scroll.
        """
        self._cam_control.scroll(dy)

    def on_key_press(self, symbol, modifiers):
        """Record a key press.
        """
        # First, check for registered key callbacks
        if symbol in self.registered_keys:
            tup = self.registered_keys[symbol]
            callback = None
            args = []
            kwargs = {}
            if not isinstance(tup, (list, tuple, np.ndarray)):
                callback = tup
            else:
                callback = tup[0]
                if len(tup) == 2:
                    args = tup[1]
                if len(tup) == 3:
                    kwargs = tup[2]
            callback(self, *args, **kwargs)
            return

        # Otherwise, use default key functions

        # F toggles face normals
        if symbol == pyglet.window.key.F:
            self.viewer_flags['fullscreen'] = (
                not self.viewer_flags['fullscreen']
            )
            self.set_fullscreen(self.viewer_flags['fullscreen'])
            self.activate()

        # quits the viewer
        elif symbol == pyglet.window.key.ESCAPE:
            self.on_close()

        elif symbol == pyglet.window.key.W:
            pass
        elif symbol == pyglet.window.key.A:
            pass
        elif symbol == pyglet.window.key.S:
            pass
        elif symbol == pyglet.window.key.D:
            pass

    @staticmethod
    def _time_event(dt, self):
        """The timer callback.
        """
        # Don't run old dead events after we've already closed
        if not self._is_active:
            return

        if self._should_close:
            self.on_close()
        else:
            self.on_draw()

    def _reset_view(self):
        """Reset the view to a good initial state.

        The view is initially along the positive x-axis at a
        sufficient distance from the scene.
        """
        scale = self.scene.scale
        if scale == 0.0:
            scale = DEFAULT_SCENE_SCALE
        #centroid = self.scene.centroid

        #if self.viewer_flags['view_center'] is not None:
        #    centroid = self.viewer_flags['view_center']

        self._camera_node.matrix = self._default_camera_pose
        self._cam_control = CameraController(self._default_camera_pose, self.viewport_size, scale)

    def _render(self):
        """Render the scene into the framebuffer and flip.
        """
        self._camera_node.matrix = self._cam_control.pose.copy()

        self._renderer.render(self.scene, self.flags)

    def _init_and_start_app(self):
        # Try multiple configs starting with target OpenGL version
        # and multisampling and removing these options if exception
        # Note: multisampling not available on all hardware
        from pyglet.gl import Config
        confs = [Config(sample_buffers=1, samples=4,
                        depth_size=24,
                        double_buffer=True,
                        major_version=TARGET_OPEN_GL_MAJOR,
                        minor_version=TARGET_OPEN_GL_MINOR),
                 Config(depth_size=24,
                        double_buffer=True,
                        major_version=TARGET_OPEN_GL_MAJOR,
                        minor_version=TARGET_OPEN_GL_MINOR),
                 Config(sample_buffers=1, samples=4,
                        depth_size=24,
                        double_buffer=True,
                        major_version=MIN_OPEN_GL_MAJOR,
                        minor_version=MIN_OPEN_GL_MINOR),
                 Config(depth_size=24,
                        double_buffer=True,
                        major_version=MIN_OPEN_GL_MAJOR,
                        minor_version=MIN_OPEN_GL_MINOR)]
        for conf in confs:
            try:
                super(CustomViewer, self).__init__(config=conf, resizable=True,
                                             width=self._viewport_size[0],
                                             height=self._viewport_size[1])
                break
            except pyglet.window.NoSuchConfigException:
                pass

        if not self.context:
            raise ValueError('Unable to initialize an OpenGL 3+ context')
        clock.schedule_interval(
            CustomViewer._time_event, 1.0 / 60, self
        )
        self.switch_to()
        self.set_caption('Duck Game')

        # Set lighting
        self._direct_light.light.intensity = 3.0
        for n in self._raymond_lights:
            if self.scene.has_node(n):
                self.scene.remove_node(n)

        if not self.scene.has_node(self._direct_light):
            self.scene.add_node(
                self._direct_light, parent_node=self._camera_node
            )

        self.flags = RenderFlags.SHADOWS_DIRECTIONAL | RenderFlags.SHADOWS_SPOT

        pyglet.app.run()

    def _compute_initial_camera_pose(self):
        #centroid = self.scene.centroid
        #if self.viewer_flags['view_center'] is not None:
        #    centroid = self.viewer_flags['view_center']
        scale = self.scene.scale
        if scale == 0.0:
            scale = DEFAULT_SCENE_SCALE

        s2 = 1.0 / np.sqrt(2.0)
        cp = np.eye(4)
        cp[:3,:3] = np.array([
            [0.0, -s2, s2],
            [1.0, 0.0, 0.0],
            [0.0, s2, s2]
        ])
        hfov = np.pi / 6.0
        dist = scale / (2.0 * np.tan(hfov))
        cp[:3,3] = dist * np.array([1.0, 0.0, 1.0]) #+ centroid

        return cp

    def _create_raymond_lights(self):
        thetas = np.pi * np.array([1.0 / 6.0, 1.0 / 6.0, 1.0 / 6.0])
        phis = np.pi * np.array([0.0, 2.0 / 3.0, 4.0 / 3.0])

        nodes = []

        for phi, theta in zip(phis, thetas):
            xp = np.sin(theta) * np.cos(phi)
            yp = np.sin(theta) * np.sin(phi)
            zp = np.cos(theta)

            z = np.array([xp, yp, zp])
            z = z / np.linalg.norm(z)
            x = np.array([-z[1], z[0], 0.0])
            if np.linalg.norm(x) == 0:
                x = np.array([1.0, 0.0, 0.0])
            x = x / np.linalg.norm(x)
            y = np.cross(z, x)

            matrix = np.eye(4)
            matrix[:3,:3] = np.c_[x,y,z]
            nodes.append(Node(
                light=DirectionalLight(color=np.ones(3), intensity=1.0),
                matrix=matrix
            ))

        return nodes

    def _create_direct_light(self):
        light = DirectionalLight(color=np.ones(3), intensity=1.0)
        n = Node(light=light, matrix=np.eye(4))
        return n
