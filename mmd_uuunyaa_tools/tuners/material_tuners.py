# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

# pylint: disable=too-many-lines

from ..editors.nodes import MaterialEditor
from ..m17n import _
from ..tuners import TunerABC, TunerRegistry
from ..tuners.material_adjusters import (SubsurfaceAdjuster,
                                                         WetAdjuster)


class MaterialTunerABC(TunerABC, MaterialEditor):
    pass


class ResetMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_RESET'

    @classmethod
    def get_name(cls) -> str:
        return _('Reset')

    def execute(self):
        self.reset()
        shader_node = self.find_mmd_shader_node()
        if shader_node is None:
            shader_node = self.find_principled_shader_node()

        if shader_node is None:
            return

        self.edit(self.get_output_node(), {
            'Surface': shader_node.outputs[0],
        }, force=True)


class TransparentMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_TRANSPARENT'

    @classmethod
    def get_name(cls) -> str:
        return _('Transparent')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_transparent_bsdf_node(), properties={'location': self.grid_to_position(-2, -0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'HASHED',
            'shadow_method': 'HASHED',
            'show_transparent_back': False,
            'use_screen_refraction': True,
        })


class EyeHighlightMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_EYE_HIGHLIGHT'

    @classmethod
    def get_name(cls) -> str:
        return _('Eye Highlight')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shadowless_bsdf_node(), {
                'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFFFFFF),
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Emission': self.hex_to_rgba(0x999999),
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class EyeWhiteMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_EYE_WHITE'

    @classmethod
    def get_name(cls) -> str:
        return _('Eye White')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shadowless_bsdf_node(), {
                'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFFFFFF),
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Emission': self.hex_to_rgba(0x666666),
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class EyeIrisMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_EYE_IRIS'

    @classmethod
    def get_name(cls) -> str:
        return _('Eye Iris')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x00001E),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.500,
                'Clearcoat': 1.000,
                'Clearcoat Roughness': 0.030,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class EyeLashMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_EYE_LASH'

    @classmethod
    def get_name(cls) -> str:
        return _('Eye Lash')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x122837),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 1.000,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class HairMatteMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_HAIR_MATTE'

    @classmethod
    def get_name(cls) -> str:
        return _('Hair Matte')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x698E9A),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.600,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class SkinMucosaMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_SKIN_MUCOSA'

    @classmethod
    def get_name(cls) -> str:
        return _('Skin Mucosa')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        node_skin_bump = self.edit(self.get_skin_bump_node(), {
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
            'Scale': 1.000,
            'Strength': 1.000,
        }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame})

        node_skin_color_adjust = self.edit(self.get_skin_color_adjust_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFE7170),
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_skin_color_adjust.outputs['Color'],
                'Subsurface':  0.200,
                'Subsurface Color': self.hex_to_rgba(0xE40000),
                'Specular': 0.500,
                'Roughness': 0.600,
                'Clearcoat': 0.500,
                'Clearcoat Roughness': 0.600,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': node_skin_bump.outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.edit(SubsurfaceAdjuster(self.material).attach(), {
            'Max': 0.400
        })

        node_adjuster = self.edit(WetAdjuster(self.material).attach(), {
        })

        self.edit(self.get_shader_node(), {
            'Clearcoat': node_adjuster.outputs['Specular'],
            'Clearcoat Roughness': node_adjuster.outputs['Roughness'],
        })


class SkinBumpMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_SKIN_BUMP'

    @classmethod
    def get_name(cls) -> str:
        return _('Skin Bump')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        node_skin_bump = self.edit(self.get_skin_bump_node(), {
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
            'Scale': 1.000,
            'Strength': 1.000,
        }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame})

        node_skin_color_adjust = self.edit(self.get_skin_color_adjust_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xEEAA99),
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_skin_color_adjust.outputs['Color'],
                'Subsurface':  0.050,
                'Subsurface Color': self.hex_to_rgba(0xE40000),
                'Specular': 0.500,
                'Roughness': 0.700,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': node_skin_bump.outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.edit(SubsurfaceAdjuster(self.material).attach(), {
            'Max': 0.100
        })


class MetalNobleMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_METAL_NOBLE'

    @classmethod
    def get_name(cls) -> str:
        return _('Metal Noble')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFFC356),
                'Subsurface': 0.001,
                'Metallic': 1.000,
                'Roughness': 0.000,
                'IOR': 0.500,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class MetalBaseMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_METAL_BASE'

    @classmethod
    def get_name(cls) -> str:
        return _('Metal Base')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x8E9194),
                'Subsurface': 0.001,
                'Metallic': 1.000,
                'Roughness': 0.400,
                'IOR': 2.500,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class StoneGemMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_STONE_GEM'

    @classmethod
    def get_name(cls) -> str:
        return _('Stone Gem')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_gem_bsdf_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x7E8FD4),
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'IOR': 2.000,
                'Transmission': 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'OPAQUE',
            'shadow_method': 'OPAQUE',
            'use_screen_refraction': True,
        })


class FabricBumpMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_BUMP'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Bump')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x999999),
                'Subsurface': 0.001,
                'Specular': 0.130,
                'Roughness': 1.000,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': self.edit(self.get_fabric_bump_node(), {
                    'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
                    'Scale': 1.000,
                    'Strength': 1.000,
                }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame}).outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class FabricWaveMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_WAVE'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Wave')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x999999),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 1.000,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': self.edit(self.get_wave_bump_node(), {
                    'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
                    'Scale': 100.000,
                    'Angle': 0.000,
                    'Fac': 0.500,
                    'Strength': 1.000,
                }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame}).outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class FabricCottonMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_COTTON'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Cotton')

    translation_properties = [
        _('Color'),
        _('Alpha'),
        _('Vector'),
        _('Impurity'),
        _('Scale'),
        _('Angle'),
        _('Strength'),
        _('Hole Alpha'),
        _('Gaps'),
        _('Warp'),
        _('Woof'),
        _('Distortion'),
        _('Fibers'),
        _('Fuzziness'),
        _('Errors'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        node_fabric_woven_texture = self.edit(self.get_fabric_woven_texture_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x999999),
            'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
            'Impurity': 0.200,
            'Scale': 10.000,
            'Angle': 0.000,
            'Strength': 0.350,
            'Hole Alpha': 0.000,
            'Gaps': 0.200,
            'Warp': 1.000,
            'Woof': 1.000,
            'Distortion': 1.000,
            'Fibers': 1.000,
            'Fuzziness': 0.500,
            'Errors': 0.000,
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_fabric_woven_texture.outputs['Color'],
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 1.000,
                'Sheen': 1.000,
                'Sheen Tint': 1.000,
                'IOR': 1.450,
                'Alpha': node_fabric_woven_texture.outputs['Alpha'],
                'Normal': node_fabric_woven_texture.outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'BLEND',
            'shadow_method': 'OPAQUE',
            'show_transparent_back': False,
            'use_screen_refraction': True,
        })


class FabricSilkMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_SILK'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Silk')

    translation_properties = [
        _('Color'),
        _('Alpha'),
        _('Vector'),
        _('Impurity'),
        _('Scale'),
        _('Angle'),
        _('Strength'),
        _('Hole Alpha'),
        _('Gaps'),
        _('Warp'),
        _('Woof'),
        _('Distortion'),
        _('Fibers'),
        _('Fuzziness'),
        _('Errors'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        node_fabric_woven_texture = self.edit(self.get_fabric_woven_texture_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x999999),
            'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
            'Impurity': 0.100,
            'Scale': 100.000,
            'Angle': 0.000,
            'Strength': 0.300,
            'Hole Alpha': 0.000,
            'Gaps': 0.300,
            'Warp': 1.000,
            'Woof': 1.000,
            'Distortion': 0.000,
            'Fibers': 0.200,
            'Fuzziness': 0.100,
            'Errors': 0.000,
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_fabric_woven_texture.outputs['Color'],
                'Subsurface': 0.001,
                'Specular': 1.000,
                'Roughness': 0.200,
                'Sheen': 1.000,
                'Sheen Tint': 1.000,
                'IOR': 1.450,
                'Alpha': node_fabric_woven_texture.outputs['Alpha'],
                'Normal': node_fabric_woven_texture.outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'BLEND',
            'shadow_method': 'OPAQUE',
            'show_transparent_back': False,
            'use_screen_refraction': True,
        })


class FabricKnitMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_KNIT'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Knit')

    translation_properties = [
        _('Color'),
        _('Alpha'),
        _('Hole Alpha'),
        _('Vector'),
        _('Random Hue'),
        _('Scale'),
        _('X Compression'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        knit_texture = self.edit(self.get_knit_texture_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFFBAAE),
            'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            'Hole Alpha': 0.000,
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
            'Random Hue': 0.500,
            'Scale': 30.000,
            'X Compression': 1.500,
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': knit_texture.outputs['Color'],
                'Specular': 0.200,
                'Roughness': 0.800,
                'IOR': 1.450,
                'Alpha': knit_texture.outputs['Alpha'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
            'Displacement': knit_texture.outputs['Displacement'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class FabricLeatherMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_FABRIC_LEATHER'

    @classmethod
    def get_name(cls) -> str:
        return _('Fabric Leather')

    translation_properties = [
        _('Primary Color'),
        _('Secondary Color'),
        _('Roughness'),
        _('Old/New'),
        _('Scale'),
        _('Strength'),
        _('Tartiary Detail'),
        _('Vector'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        leather_texture = self.edit(self.get_leather_texture_node(), {
            'Primary Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x000000),
            'Secondary Color': self.hex_to_rgba(0x333333),
            'Roughness': 0.450,
            'Old/New': 4.000,
            'Scale': 100.000,
            'Strength': 0.150,
            'Tartiary Detail': 2.000,
            'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': leather_texture.outputs['Color'],
                'Subsurface': 0.001,
                'Specular': 0.200,
                'Roughness': leather_texture.outputs['Roughness'],
                'Sheen': 0.300,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': leather_texture.outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class PlasticGlossMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_PLASTIC_GLOSS'

    @classmethod
    def get_name(cls) -> str:
        return _('Plastic Gloss')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x666666),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.100,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class PlasticBumpMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_PLASTIC_BUMP'

    @classmethod
    def get_name(cls) -> str:
        return _('Plastic Bump')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x666666),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.100,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
                'Normal': self.edit(self.get_magic_bump_node(), {
                    'Scale': 10.000,
                    'Angle': 0.000,
                    'Strength': 0.200,
                    'Vector': self.edit(self.get_tex_uv(), properties={}).outputs['Base UV'],
                }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame}).outputs['Normal'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class PlasticMatteMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_PLASTIC_MATTE'

    @classmethod
    def get_name(cls) -> str:
        return _('Plastic Matte')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x666666),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.700,
                'IOR': 1.450,
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class PlasticEmissionMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_PLASTIC_EMISSION'

    @classmethod
    def get_name(cls) -> str:
        return _('Plastic Emission')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': self.hex_to_rgba(0x000000),
                'Subsurface': 0.001,
                'Specular': 0.500,
                'Roughness': 0.700,
                'IOR': 1.450,
                'Emission': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFF6666),
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class LiquidWaterMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_LIQUID_WATER'

    @classmethod
    def get_name(cls) -> str:
        return _('Liquid Water')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_liquid_bsdf_node(), {
                'Roughness': 0.000,
                'IOR': 1.333,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'HASHED',
            'shadow_method': 'HASHED',
            'use_screen_refraction': True,
        })


class LiquidCloudyMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_LIQUID_CLOUDY'

    @classmethod
    def get_name(cls) -> str:
        return _('Liquid Cloudy')

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_mix_shader_node(), {
                'Fac': 0.300,
                1: self.edit(self.get_liquid_bsdf_node(), {
                    'Roughness': 0.000,
                    'IOR': 1.333,
                }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame}).outputs['BSDF'],
                2: self.edit(self.get_shader_node(), {
                    'Base Color': self.hex_to_rgba(0xE7E7E7),
                    'Specular': 1.000,
                    'Roughness': 0.000,
                    'Clearcoat': 1.000,
                    'IOR': 1.450,
                }, {'location': self.grid_to_position(-2, -4), 'parent': node_frame}).outputs['BSDF'],
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['Shader'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)

        self.set_material_properties({
            'blend_method': 'HASHED',
            'shadow_method': 'HASHED',
            'use_screen_refraction': True,
        })


class ArtisticWatercolorMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_ARTISTIC_WATERCOLOR'

    @classmethod
    def get_name(cls) -> str:
        return _('Artistic Watercolor')

    translation_properties = [
        _('Color'),
        _('Scale'),
        _('Background Scale'),
        _('Bleed Strength'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        node_watercolor_texture = self.edit(self.get_watercolor_texture_node(), {
            'Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0xFFCCCC),
            'Scale': 2.000,
            'Background Scale': 3.000,
            'Bleed Strength': 1.000,
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': self.hex_to_rgba(0x000000),
                'Specular': 0.000,
                'Emission': node_watercolor_texture.outputs['Color'],
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


class ToonShaderMaterialTuner(MaterialTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_TOON_SHADER'

    @classmethod
    def get_name(cls) -> str:
        return _('Toon Shader')

    translation_properties = [
        _('Base Color'),
        _('Highlight Color'),
        _('Shadow Color'),
        _('Rim Light Strength'),
    ]

    def execute(self):
        self.reset()
        node_frame = self.get_node_frame(self.get_name())
        node_diffuse_color = self.edit(self.get_diffuse_color_node(), properties={})
        node_toon_shader_texture = self.edit(self.get_toon_shader_texture_node(), {
            'Base Color': node_diffuse_color.outputs['Color'] if node_diffuse_color else self.hex_to_rgba(0x99CCCC),
            'Roughness': 1.000,
            'Highlight Color': (0.5, 0.5, 0.5, 1.0),
            'Shadow Color': (0.5, 0.5, 0.5, 1.0),
            'Rim Light Strength': 0.500,
        }, {'location': self.grid_to_position(-2, +0), 'parent': node_frame})

        self.edit(self.get_output_node(), {
            'Surface': self.edit(self.get_shader_node(), {
                'Base Color': self.hex_to_rgba(0x000000),
                'Specular': 0.000,
                'Roughness': 0.000,
                'Emission': node_toon_shader_texture.outputs['Color'],
                'Alpha': node_diffuse_color.outputs['Alpha'] if node_diffuse_color else 1.000,
            }, {'location': self.grid_to_position(+0, +0), 'parent': node_frame}).outputs['BSDF'],
        }, {'location': self.grid_to_position(+3, +0)}, force=True)


TUNERS = TunerRegistry(
    (0, ResetMaterialTuner),
    (1, TransparentMaterialTuner),
    (2, EyeHighlightMaterialTuner),
    (3, EyeWhiteMaterialTuner),
    (4, EyeIrisMaterialTuner),
    (5, EyeLashMaterialTuner),
    (6, HairMatteMaterialTuner),
    (7, SkinMucosaMaterialTuner),
    (8, SkinBumpMaterialTuner),
    (21, FabricCottonMaterialTuner),
    (22, FabricSilkMaterialTuner),
    (9, FabricBumpMaterialTuner),
    (10, FabricWaveMaterialTuner),
    (11, FabricKnitMaterialTuner),
    (12, FabricLeatherMaterialTuner),
    (17, PlasticGlossMaterialTuner),
    (13, PlasticMatteMaterialTuner),
    (14, PlasticEmissionMaterialTuner),
    (23, PlasticBumpMaterialTuner),
    (18, MetalNobleMaterialTuner),
    (19, MetalBaseMaterialTuner),
    (20, StoneGemMaterialTuner),
    (15, LiquidWaterMaterialTuner),
    (16, LiquidCloudyMaterialTuner),
    (24, ArtisticWatercolorMaterialTuner),
    (25, ToonShaderMaterialTuner),
)
