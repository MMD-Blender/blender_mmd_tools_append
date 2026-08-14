# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import bpy

from ..editors.nodes import MaterialEditor
from ..tuners import lighting_tuners, material_adjusters, material_tuners
from ..tuners.geometry_nodes_tuners import TUNERS, GeometryNodesUtilities


class TuneLighting(bpy.types.Operator):
    bl_idname = "mmd_tools_append.tune_lighting"
    bl_label = "Tune Lighting"
    bl_options = {"REGISTER", "UNDO"}

    lighting: bpy.props.EnumProperty(
        items=lighting_tuners.TUNERS.to_enum_property_items(),
    )

    @classmethod
    def poll(cls, _):
        return True

    def execute(self, context):
        lighting_tuners.TUNERS[self.lighting](context.collection).execute()
        return {"FINISHED"}


class FreezeLighting(bpy.types.Operator):
    bl_idname = "mmd_tools_append.freeze_lighting"
    bl_label = "Freeze Lighting"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return lighting_tuners.LightingUtilities(context.collection).find_active_lighting() is not None

    def execute(self, context):
        utilities = lighting_tuners.LightingUtilities(context.collection)
        lighting = utilities.find_active_lighting()
        utilities.object_marker.unmark(lighting, depth=1)
        context.collection.mmd_tools_append_lighting.thumbnails = lighting_tuners.ResetLightingTuner.get_id()
        return {"FINISHED"}


class TuneMaterial(bpy.types.Operator):
    bl_idname = "mmd_tools_append.tune_material"
    bl_label = "Tune Material"
    bl_options = {"REGISTER", "UNDO"}

    material: bpy.props.EnumProperty(
        items=material_tuners.TUNERS.to_enum_property_items(),
    )

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_tuners.TUNERS[self.material](context.object.active_material).execute()
        return {"FINISHED"}


class CopyTuneMaterialSettings(bpy.types.Operator):
    bl_idname = "mmd_tools_append.copy_tune_material_settings"
    bl_label = "Copy Append Material"
    bl_description = "Apply current Append material to materials of the selected objects"
    bl_options = {"REGISTER", "UNDO"}

    to_active: bpy.props.BoolProperty(name="Apply to active object", description="Apply Append material to materials in active object", default=False)
    to_selection: bpy.props.BoolProperty(name="Apply to selection", description="Apply Append material to materials in selected object", default=False)

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        active = context.object.active_material
        targets = set(context.selected_objects)
        if context.active_object:
            targets.add(context.active_object)

        for obj in targets:
            if obj == context.active_object and not self.to_active:
                continue

            if obj != context.active_object and not self.to_selection:
                continue

            for i in obj.material_slots:
                # usual checks
                if not i.material or i.material == active:
                    continue
                if not i.material.use_nodes:
                    i.material.use_nodes = True

                mat = i.material
                material_tuners.TUNERS[active.mmd_tools_append_material.thumbnails](mat).execute()

                # disable update to keep active material
                mat.mmd_tools_append_material.update = False
                mat.mmd_tools_append_material.thumbnails = active.mmd_tools_append_material.thumbnails
                mat.mmd_tools_append_material.update = True

                # copy values from active material
                mat_editor = MaterialEditor(mat)
                mat_editor.copy_node_group_inputs(active)

        return {"FINISHED"}


class AttachMaterialAdjuster(bpy.types.Operator):
    bl_idname = "mmd_tools_append.attach_material_adjuster"
    bl_label = "Attach Material Adjuster"
    bl_options = {"REGISTER", "UNDO"}

    adjuster_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_adjusters.ADJUSTERS[self.adjuster_name](context.object.active_material).attach()
        return {"FINISHED"}


class DetachMaterialAdjuster(bpy.types.Operator):
    bl_idname = "mmd_tools_append.detach_material_adjuster"
    bl_label = "Detach Material Adjuster"
    bl_options = {"REGISTER", "UNDO"}

    adjuster_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def execute(self, context):
        material_adjusters.ADJUSTERS[self.adjuster_name](context.object.active_material).detach_and_clean()
        return {"FINISHED"}


class TuneGeometryNodes(bpy.types.Operator):
    bl_idname = "mmd_tools_append.tune_geometry_nodes"
    bl_label = "Tune Geometry Nodes"
    bl_options = {"REGISTER", "UNDO"}

    geometry_nodes: bpy.props.EnumProperty(
        items=TUNERS.to_enum_property_items(),
    )

    @classmethod
    def poll(cls, context):
        geometry_node_tree = GeometryNodesUtilities.find_geometry_node_tree(context.active_object)
        return geometry_node_tree is not None

    def execute(self, context):
        TUNERS[self.geometry_nodes](GeometryNodesUtilities.find_geometry_node_tree(context.active_object)).execute()
        return {"FINISHED"}
