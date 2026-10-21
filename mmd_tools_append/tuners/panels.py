# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.


import bpy
from bpy.app.translations import pgettext as _
from bpy.app.translations import pgettext_iface as iface_

from ..editors.geometry_nodes import GeometryEditor
from ..editors.nodes import MaterialEditor
from ..tuners.geometry_nodes_tuners import GeometryNodesUtilities
from ..tuners.lighting_tuners import LightingUtilities
from ..tuners.material_adjusters import (
    EmissionAdjuster,
    GlitterAdjuster,
    MaterialAdjusterUtilities,
    WetAdjuster,
)
from ..tuners.operators import AttachMaterialAdjuster, CopyTuneMaterialSettings, DetachMaterialAdjuster, FreezeLighting
from ..utilities import is_mmd_tools_installed


class SkyPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_sky_panel"
    bl_label = "MMD Append Sky"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.scene.world is not None

    _translation_properties = [
        _("Light Strength"),
        _("Image Strength"),
    ]

    def draw(self, context: bpy.types.Context):
        world: bpy.types.World = context.scene.world

        utilities = MaterialEditor(world)

        layout = self.layout

        node_frame = utilities.find_node_frame()
        if node_frame is None:
            layout.label(text="MMD Append World not found.")
            return

        scene_has_irradiance_volumes = self._scene_has_irradiance_volumes()
        if not scene_has_irradiance_volumes:
            layout.label(text="IrradianceVolume not found. Please add it.", icon="ERROR")

        utilities.draw_setting_shader_node_properties(layout, utilities.list_nodes(node_frame=node_frame))

        col = layout.column(align=True)
        col.label(text="for Eevee lighting, check Render Properties.")

        if not scene_has_irradiance_volumes:
            return

        col.operator("scene.light_cache_bake", text="Bake Indirect Lighting", icon="RENDER_STILL")

    @staticmethod
    def _scene_has_irradiance_volumes():
        obj: bpy.types.Object
        for obj in bpy.data.objects:
            if obj.type != "LIGHT_PROBE":
                continue

            light_probe = obj.data
            if light_probe.type in {"GRID", "VOLUME"}:
                return True

        return False


class LightingPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_lighting_panel"
    bl_label = "MMD Append Lighting"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        mmd_tools_append_lighting = context.collection.mmd_tools_append_lighting

        layout = self.layout
        col = layout.column(align=True)

        # Previews
        row = col.row()
        row.template_icon_view(mmd_tools_append_lighting, "thumbnails", show_labels=True)

        # Lighting Name
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.label(text=row.enum_item_name(mmd_tools_append_lighting, "thumbnails", mmd_tools_append_lighting.thumbnails))

        utilities = LightingUtilities(context.collection)
        lighting = utilities.find_active_lighting()
        if lighting is None:
            return

        layout.prop(lighting, "location")
        layout.prop(lighting, "rotation_euler")
        layout.prop(lighting, "scale")

        row = layout.row(align=False)
        row.operator(FreezeLighting.bl_idname)


class MaterialPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_material_panel"
    bl_label = "MMD Append Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_mmd_tools_installed() and obj.active_material and obj.mmd_type == "NONE"

    def draw(self, context):
        material = context.active_object.active_material
        mmd_tools_append_material = bpy.context.material.mmd_tools_append_material

        layout = self.layout
        col = layout.column(align=True)

        # Previews
        row = col.row()
        row.template_icon_view(mmd_tools_append_material, "thumbnails", show_labels=True)

        # Material Name
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.label(text=row.enum_item_name(mmd_tools_append_material, "thumbnails", mmd_tools_append_material.thumbnails))

        col = layout.column(align=True)
        col.label(text="Batch Operation:")
        grid = col.grid_flow(row_major=True)

        op = grid.row(align=True).operator(CopyTuneMaterialSettings.bl_idname, text="Copy to Active", icon="DUPLICATE")
        op.to_active = True
        op.to_selection = False

        op = grid.row(align=True).operator(CopyTuneMaterialSettings.bl_idname, text="Copy to Selected", icon="DUPLICATE")
        op.to_active = False
        op.to_selection = True

        utilities = MaterialEditor(material)
        node_frame = utilities.find_node_frame()
        if node_frame is None:
            return

        utilities.draw_setting_shader_node_properties(layout, utilities.list_nodes(node_type=bpy.types.ShaderNodeGroup, node_frame=node_frame))


class MaterialAdjusterPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_material_adjuster_panel"
    bl_label = "MMD Append Material Adjuster"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def draw(self, context):
        active_object = context.active_object
        material = active_object.active_material

        layout = self.layout

        global_toon_sphere = active_object.mmd_tools_append_global_toon_sphere
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Global Toon/Sphere Adjuster")
        col.prop(global_toon_sphere, "toon_fac")
        col.prop(global_toon_sphere, "sphere_fac")

        col = layout.column(align=True)
        utilities = MaterialAdjusterUtilities(material)
        if not utilities.check_attachable():
            col.label(
                text=iface_("{material_name} is unsupported. Select other material to be output from Principled BSDF.").format(material_name=material.name),
                icon="ERROR",
            )
            return

        grid = col.grid_flow(row_major=True, columns=2)

        def draw_operator(layout, class_, text, icon):
            if utilities.check_attached(class_.get_name()):
                layout.operator(DetachMaterialAdjuster.bl_idname, text=text, icon="X").adjuster_name = class_.get_name()
            else:
                layout.operator(AttachMaterialAdjuster.bl_idname, text=text, icon=icon).adjuster_name = class_.get_name()

        draw_operator(grid, WetAdjuster, text="Wet", icon="MOD_FLUIDSIM")
        draw_operator(grid, GlitterAdjuster, text="Glitter", icon="PMARKER_ACT")
        draw_operator(grid, EmissionAdjuster, text="Emission", icon="LIGHT")

        node_frame = utilities.find_adjusters_node_frame()
        if node_frame is None:
            return

        utilities.draw_setting_shader_node_properties(layout, utilities.list_nodes(node_type=bpy.types.ShaderNodeGroup, node_frame=node_frame))


class GeometryNodesPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_geometry_nodes_panel"
    bl_label = "MMD Append Geometry Nodes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        active_object: bpy.types.Object = context.active_object
        if active_object.type != "MESH":
            return False

        return GeometryNodesUtilities.find_geometry_node_modifier(active_object) is not None

    def draw(self, context: bpy.types.Context):
        active_object: bpy.types.Object = context.active_object

        modifier = GeometryNodesUtilities.find_geometry_node_modifier(active_object)
        geometry_node_tree: bpy.types.GeometryNodeTree = modifier.node_group
        mmd_tools_append_geometry_nodes = geometry_node_tree.mmd_tools_append_geometry_nodes

        layout = self.layout
        col = layout.column(align=True)

        # Previews
        row = col.row()
        row.template_icon_view(mmd_tools_append_geometry_nodes, "thumbnails", show_labels=True)

        # Modifier Name
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.label(text=row.enum_item_name(mmd_tools_append_geometry_nodes, "thumbnails", mmd_tools_append_geometry_nodes.thumbnails))

        utilities = GeometryEditor(geometry_node_tree)
        node_frame = utilities.find_node_frame()
        if node_frame is None:
            return

        utilities.draw_setting_shader_node_properties(layout, utilities.list_nodes(node_type=bpy.types.GeometryNodeGroup, node_frame=node_frame))
