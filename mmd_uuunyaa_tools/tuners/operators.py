# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import bpy
from ..m17n import _
from ..tuners import (lighting_tuners, material_adjusters,
                                      material_tuners)


class TuneLighting(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.tune_lighting'
    bl_label = _('Tune Lighting')
    bl_options = {'REGISTER', 'UNDO'}

    lighting: bpy.props.EnumProperty(
        items=lighting_tuners.TUNERS.to_enum_property_items(),
    )

    @classmethod
    def poll(cls, _):
        return True

    def execute(self, context):
        lighting_tuners.TUNERS[self.lighting](context.collection).execute()
        return {'FINISHED'}


class FreezeLighting(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.freeze_lighting'
    bl_label = _('Freeze Lighting')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return lighting_tuners.LightingUtilities(context.collection).find_active_lighting() is not None

    def execute(self, context):
        utilities = lighting_tuners.LightingUtilities(context.collection)
        lighting = utilities.find_active_lighting()
        utilities.object_marker.unmark(lighting, depth=1)
        context.collection.mmd_uuunyaa_tools_lighting.thumbnails = lighting_tuners.ResetLightingTuner.get_id()
        return {'FINISHED'}


class TuneMaterial(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.tune_material'
    bl_label = _('Tune Material')
    bl_options = {'REGISTER', 'UNDO'}

    material: bpy.props.EnumProperty(
        items=material_tuners.TUNERS.to_enum_property_items(),
    )

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_tuners.TUNERS[self.material](context.object.active_material).execute()
        return {'FINISHED'}


class AttachMaterialAdjuster(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.attach_material_adjuster'
    bl_label = _('Attach Material Adjuster')
    bl_options = {'REGISTER', 'UNDO'}

    adjuster_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_adjusters.ADJUSTERS[self.adjuster_name](context.object.active_material).attach()
        return {'FINISHED'}


class DetachMaterialAdjuster(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.detach_material_adjuster'
    bl_label = _('Detach Material Adjuster')
    bl_options = {'REGISTER', 'UNDO'}

    adjuster_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_adjusters.ADJUSTERS[self.adjuster_name](context.object.active_material).detach_and_clean()
        return {'FINISHED'}


try:
    from ..tuners.geometry_nodes_tuners import (
        TUNERS, GeometryNodesUtilities)

    class TuneGeometryNodes(bpy.types.Operator):
        bl_idname = 'mmd_uuunyaa_tools.tune_geometry_nodes'
        bl_label = _('Tune Geometry Nodes')
        bl_options = {'REGISTER', 'UNDO'}

        geometry_nodes: bpy.props.EnumProperty(
            items=TUNERS.to_enum_property_items(),
        )

        @classmethod
        def poll(cls, context):
            geometry_node_tree = GeometryNodesUtilities.find_geometry_node_tree(context.active_object)
            return geometry_node_tree is not None

        def execute(self, context):
            TUNERS[self.geometry_nodes](
                GeometryNodesUtilities.find_geometry_node_tree(context.active_object)
            ).execute()
            return {'FINISHED'}
except ImportError:
    print('[WARN] Geometry Nodes do not exist. Ignore it.')
