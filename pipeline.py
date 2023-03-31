import math
import os

import panda3d.core as p3d
import simplepbr

from direct.filter.FilterManager import FilterManager


class CustomPipeline:

    def __init__(self, *, render_node=None, window=None, camera_node=None, taskmgr=None, msaa_samples=4, max_lights=8,
                 use_normal_maps=False, use_emission_maps=True, exposure=1.0, enable_shadows=False, enable_fog=False,
                 use_occlusion_maps=False, use_330=None, use_hardware_skinning=None, sdr_lut=None, sdr_lut_factor=1.0,
                 manager=None):

        if render_node is None:
            render_node = base.render

        if window is None:
            window = base.win

        if camera_node is None:
            camera_node = base.cam

        if taskmgr is None:
            taskmgr = base.task_mgr

        self._shader_ready = False
        self.render_node = render_node
        self.window = window
        self.camera_node = camera_node
        self.max_lights = max_lights
        self.use_normal_maps = use_normal_maps
        self.use_emission_maps = use_emission_maps
        self.enable_shadows = enable_shadows
        self.enable_fog = enable_fog
        self.exposure = exposure
        self.msaa_samples = msaa_samples
        self.use_occlusion_maps = use_occlusion_maps
        self.sdr_lut = sdr_lut
        self.sdr_lut_factor = sdr_lut_factor

        self._set_use_330(use_330)
        self.enable_hardware_skinning = use_hardware_skinning if use_hardware_skinning is not None else self.use_330

        # Create a FilterManager instance
        if manager is None:
            self.manager = FilterManager(window, camera_node)
        else:
            self.manager = manager

        # Do not force power-of-two textures
        p3d.Texture.set_textures_power_2(p3d.ATS_none)

        # Make sure we have AA for if/when MSAA is enabled
        self.render_node.set_antialias(p3d.AntialiasAttrib.M_auto)

        # PBR Shader
        self._recompile_pbr()

        # Tonemapping
        self._setup_tonemapping()

        # Do updates based on scene changes
        taskmgr.add(self._update, 'simplepbr update')

        self._shader_ready = True

    def _set_use_330(self, use_330):
        if use_330 is not None:
            self.use_330 = use_330
        else:
            self.use_330 = False

            cvar = p3d.ConfigVariableInt('gl-version')
            gl_version = [
                cvar.get_word(i)
                for i in range(cvar.get_num_words())
            ]
            if len(gl_version) >= 2 and gl_version[0] >= 3 and gl_version[1] >= 2:
                # Not exactly accurate, but setting this variable to '3 2' is common for disabling
                # the fixed-function pipeline and 3.2 support likely means 3.3 support as well.
                self.use_330 = True

    def __setattr__(self, name, value):
        if hasattr(self, name):
            prev_value = getattr(self, name)
        else:
            prev_value = None
        super().__setattr__(name, value)
        if not self._shader_ready:
            return

        pbr_vars = [
            'max_lights',
            'use_normal_maps',
            'use_emission_maps',
            'enable_shadows',
            'enable_fog',
            'use_occlusion_maps',
        ]

        def resetup_tonemap():
            # Destroy previous buffers so we can re-create
            self.manager.cleanup()

            # Create a new FilterManager instance
            self.manager = FilterManager(self.window, self.camera_node)
            self._setup_tonemapping()

        if name in pbr_vars and prev_value != value:
            self._recompile_pbr()
        elif name == 'exposure':
            self.tonemap_quad.set_shader_input('exposure', self.exposure)
        elif name == 'msaa_samples':
            self._setup_tonemapping()
        elif name == 'render_node' and prev_value != value:
            self._recompile_pbr()
        elif name in ('camera_node', 'window') and prev_value != value:
            resetup_tonemap()
        elif name == 'use_330' and prev_value != value:
            self._set_use_330(value)
            self._recompile_pbr()
            resetup_tonemap()

    def _recompile_pbr(self):
        pbr_defines = {
            'MAX_LIGHTS': self.max_lights,
        }
        if self.use_normal_maps:
            pbr_defines['USE_NORMAL_MAP'] = ''
        if self.use_emission_maps:
            pbr_defines['USE_EMISSION_MAP'] = ''
        if self.enable_shadows:
            pbr_defines['ENABLE_SHADOWS'] = ''
        if self.enable_fog:
            pbr_defines['ENABLE_FOG'] = ''
        if self.use_occlusion_maps:
            pbr_defines['USE_OCCLUSION_MAP'] = ''
        if self.use_330:
            pbr_defines['USE_330'] = ''
        if self.enable_hardware_skinning:
            pbr_defines['ENABLE_SKINNING'] = ''

        pbr_vert_str = simplepbr._load_shader_str('simplepbr.vert', pbr_defines)
        pbr_frag_str = simplepbr._load_shader_str('simplepbr.frag', pbr_defines)
        pbrshader = p3d.Shader.make(
            p3d.Shader.SL_GLSL,
            vertex=pbr_vert_str,
            fragment=pbr_frag_str,
        )
        attr = p3d.ShaderAttrib.make(pbrshader)
        if self.enable_hardware_skinning:
            attr = attr.set_flag(p3d.ShaderAttrib.F_hardware_skinning, True)
        self.render_node.set_attrib(attr)

    def _setup_tonemapping(self):
        if self._shader_ready:
            # Destroy previous buffers so we can re-create
            self.manager.cleanup()

            # Fix shadow buffers after FilterManager.cleanup()
            for caster in self.get_all_casters():
                sbuff_size = caster.get_shadow_buffer_size()
                caster.set_shadow_buffer_size((0, 0))
                caster.set_shadow_buffer_size(sbuff_size)

        fbprops = p3d.FrameBufferProperties()
        fbprops.float_color = True
        fbprops.set_rgba_bits(16, 16, 16, 16)
        fbprops.set_depth_bits(24)
        fbprops.set_multisamples(self.msaa_samples)
        scene_tex = p3d.Texture()
        scene_tex.set_format(p3d.Texture.F_rgba16)
        scene_tex.set_component_type(p3d.Texture.T_float)
        self.tonemap_quad = self.manager.render_scene_into(colortex=scene_tex, fbprops=fbprops)

        defines = {}
        if self.use_330:
            defines['USE_330'] = ''

        post_vert_str = simplepbr._load_shader_str('post.vert', defines)
        post_frag_str = simplepbr._load_shader_str('tonemap.frag', defines)
        tonemap_shader = p3d.Shader.make(
            p3d.Shader.SL_GLSL,
            vertex=post_vert_str,
            fragment=post_frag_str,
        )
        self.tonemap_quad.set_shader(tonemap_shader)
        self.tonemap_quad.set_shader_input('tex', scene_tex)
        self.tonemap_quad.set_shader_input('exposure', self.exposure)

    def get_all_casters(self):
        engine = p3d.GraphicsEngine.get_global_ptr()
        cameras = [
            dispregion.camera
            for win in engine.windows
            for dispregion in win.active_display_regions
        ]

        return [
            i.node()
            for i in cameras
            if hasattr(i.node(), 'is_shadow_caster') and i.node().is_shadow_caster()
        ]

    def _update(self, task):
        # Use a simpler, faster shader for shadows
        for caster in self.get_all_casters():
            state = caster.get_initial_state()
            if not state.has_attrib(p3d.ShaderAttrib):
                defines = {}
                if self.use_330:
                    defines['USE_330'] = ''
                if self.enable_hardware_skinning:
                    defines['ENABLE_SKINNING'] = ''
                shader = p3d.Shader.make(
                    p3d.Shader.SL_GLSL,
                    vertex=simplepbr._load_shader_str('shadow.vert', defines),
                    fragment=simplepbr._load_shader_str('shadow.frag', defines)
                )
                attr = p3d.ShaderAttrib.make(shader)
                if self.enable_hardware_skinning:
                    attr = attr.set_flag(p3d.ShaderAttrib.F_hardware_skinning, True)
                state = state.add_attrib(attr, 1)
                caster.set_initial_state(state)

        return task.cont

    def verify_shaders(self):
        gsg = self.window.gsg

        def check_node_shader(np):
            shader = p3d.Shader(np.get_shader())
            shader.prepare_now(gsg.prepared_objects, gsg)
            assert shader.is_prepared(gsg.prepared_objects)
            assert not shader.get_error_flag()

        check_node_shader(self.render_node)
        check_node_shader(self.tonemap_quad)
