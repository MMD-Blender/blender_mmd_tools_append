# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import math
import sys
import time
from typing import Set

import bmesh
import bpy
from ..editors import segmentation
from ..m17n import _
from ..utilities import (import_mmd_tools,
                                         is_mmd_tools_installed,
                                         label_multiline)


class ConvertMaterialsForEevee(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.convert_materials_for_eevee'
    bl_label = _('Convert Materials for Eevee')
    bl_description = _('Convert materials of selected objects for Eevee.')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            next((x for x in context.selected_objects if x.type == 'MESH'), None)
            and is_mmd_tools_installed()
        )

    def execute(self, context):
        mmd_tools = import_mmd_tools()
        for obj in (x for x in context.selected_objects if x.type == 'MESH'):
            mmd_tools.cycles_converter.convertToCyclesShader(obj, use_principled=True, clean_nodes=True)

        if context.scene.render.engine != 'BLENDER_EEVEE':
            context.scene.render.engine = 'BLENDER_EEVEE'

        return {'FINISHED'}


class SetupRenderEngineForEevee(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.setup_render_engine_for_eevee'
    bl_label = _('Setup Render Engine for Eevee')
    bl_description = _('Setup render engine properties for Eevee.')
    bl_options = {'REGISTER', 'UNDO'}

    use_bloom: bpy.props.BoolProperty(name=_('Use Bloom'), default=True)
    use_motion_blur: bpy.props.BoolProperty(name=_('Use Motion Blur'), default=False)
    film_transparent: bpy.props.BoolProperty(name=_('Use Film Transparent'), default=False)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if context.scene.render.engine != 'BLENDER_EEVEE':
            context.scene.render.engine = 'BLENDER_EEVEE'

        eevee = context.scene.eevee

        # Sampling
        # > Render: 8
        eevee.taa_render_samples = 16
        # > Viewport: 8
        eevee.taa_samples = 16

        # Ambient Occlusion: enable
        eevee.use_gtao = True
        # > Distance: 0.1 m
        eevee.gtao_distance = 0.100

        # Bloom: enable
        eevee.use_bloom = self.use_bloom
        if self.use_bloom:
            # > Threshold: 1.000
            eevee.bloom_threshold = 1.000
            # > Intensity: 0.100
            eevee.bloom_intensity = 0.100

        # Depth of Field
        # > Max Size: 16 px
        eevee.bokeh_max_size = 16.000

        # Screen Space Reflections: enable
        eevee.use_ssr = True
        # > Refrection: enable
        eevee.use_ssr_refraction = True
        # > Edge Fading: 0.000
        eevee.ssr_border_fade = 0.075

        # Motion Blur
        eevee.use_motion_blur = self.use_motion_blur

        # Shadows
        # > Cube Size 1024 px
        eevee.shadow_cube_size = '1024'
        # > Cascade Size 2048 px
        eevee.shadow_cascade_size = '2048'
        # > Soft Shadows: True
        eevee.use_soft_shadows = True

        # Indirect lighting: enable
        # > Irradiance Smoothing: 0.50
        eevee.gi_irradiance_smoothing = 0.50

        # Film > Transparent
        context.scene.render.film_transparent = self.film_transparent

        # Color Management
        # > View Transform: Filmic
        context.scene.view_settings.view_transform = 'Filmic'
        # > Look: High Contrast
        context.scene.view_settings.look = 'High Contrast'

        return {'FINISHED'}


class SetupRenderEngineForToonEevee(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.setup_render_engine_for_toon_eevee'
    bl_label = _('Setup Render Engine for Toon Eevee')
    bl_description = _('Setup render engine properties for Toon Eevee.')
    bl_options = {'REGISTER', 'UNDO'}

    use_bloom: bpy.props.BoolProperty(name=_('Use Bloom'), default=True)
    use_motion_blur: bpy.props.BoolProperty(name=_('Use Motion Blur'), default=False)
    use_soft_shadows: bpy.props.BoolProperty(name=_('Use Soft Shadows'), default=True)
    film_transparent: bpy.props.BoolProperty(name=_('Use Film Transparent'), default=False)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if context.scene.render.engine != 'BLENDER_EEVEE':
            context.scene.render.engine = 'BLENDER_EEVEE'

        eevee = context.scene.eevee

        # Sampling
        # > Render: 8
        eevee.taa_render_samples = 8
        # > Viewport: 8
        eevee.taa_samples = 8

        # Ambient Occlusion: enable
        eevee.use_gtao = True
        # > Distance: 0.1 m
        eevee.gtao_distance = 0.100

        # Bloom: enable
        eevee.use_bloom = self.use_bloom
        if self.use_bloom:
            # > Threshold: 1.000
            eevee.bloom_threshold = 1.000
            # > Intensity: 0.100
            eevee.bloom_intensity = 0.100

        # Depth of Field
        # > Max Size: 16 px
        eevee.bokeh_max_size = 16.000

        # Screen Space Reflections: enable
        eevee.use_ssr = True
        # > Refrection: enable
        eevee.use_ssr_refraction = True
        # > Edge Fading: 0.000
        eevee.ssr_border_fade = 0.075

        # Motion Blur
        eevee.use_motion_blur = self.use_motion_blur

        # Shadows
        # > Cube Size 1024 px
        eevee.shadow_cube_size = '1024'
        # > Cascade Size 2048 px
        eevee.shadow_cascade_size = '2048'
        # > Soft Shadows
        eevee.use_soft_shadows = self.use_soft_shadows

        # Indirect lighting: enable
        # > Irradiance Smoothing: 0.50
        eevee.gi_irradiance_smoothing = 0.50

        # Film > Transparent
        context.scene.render.film_transparent = self.film_transparent

        # Color Management
        # > View Transform: Standard
        context.scene.view_settings.view_transform = 'Standard'
        # > Look: None
        context.scene.view_settings.look = 'None'

        return {'FINISHED'}


class SetupRenderEngineForWorkbench(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.setup_render_engine_for_workbench'
    bl_label = _('Setup Render Engine for Workbench')
    bl_description = _('Setup render engine properties for Workbench.')
    bl_options = {'REGISTER', 'UNDO'}

    use_shadow: bpy.props.BoolProperty(name=_('Use Shadow'), default=True)
    use_dof: bpy.props.BoolProperty(name=_('Use Depth of Field'), default=True)
    film_transparent: bpy.props.BoolProperty(name=_('Use Film Transparent'), default=False)

    @classmethod
    def poll(cls, _context):
        return True

    def execute(self, context: bpy.types.Context):
        if context.scene.render.engine != 'BLENDER_WORKBENCH':
            context.scene.render.engine = 'BLENDER_WORKBENCH'

        shading = context.scene.display.shading

        # Lighting: Flat
        shading.light = 'FLAT'

        # Color: Texture
        shading.color_type = 'TEXTURE'

        # Options
        # > Cavity: enable
        shading.show_cavity = self.use_shadow
        # > Type: World
        shading.cavity_type = 'WORLD'
        # > Ridge: 0.200
        shading.cavity_ridge_factor = 0.200
        # > Valley: 1.000
        shading.cavity_valley_factor = 1.000
        # > Depth of Field: enable
        shading.use_dof = self.use_dof

        # Film > Transparent
        context.scene.render.film_transparent = self.film_transparent

        # Color Management
        # > View Transform: Standard
        context.scene.view_settings.view_transform = 'Standard'
        # > Look: None
        context.scene.view_settings.look = 'None'

        return {'FINISHED'}


class ShowMessageBox(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.show_message_box'
    bl_label = _('Show Message Box')
    bl_options = {'INTERNAL'}

    icon: bpy.props.StringProperty(default='INFO')
    title: bpy.props.StringProperty(default='')
    message: bpy.props.StringProperty(default='')
    width: bpy.props.IntProperty(default=400)

    def execute(self, context):
        self.report({'INFO'}, message=self.message)
        return context.window_manager.invoke_popup(self, width=self.width)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.title, icon=self.icon)
        col = layout.column(align=True)
        label_multiline(col, text=self.message, width=self.width)


class RemoveUnusedVertexGroups(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.remove_unused_vertex_groups'
    bl_label = _('Remove Unused Vertex Groups')
    bl_description = _('Remove unused vertex groups from the active meshes')
    bl_options = {'REGISTER', 'UNDO'}

    weight_threshold: bpy.props.FloatProperty(name=_('Weight Threshold'), default=0.0, min=0.0, max=1.0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        # pylint: disable=too-many-branches
        obj: bpy.types.Object
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            used_vertex_group_indices: Set[int] = set()

            mesh: bpy.types.Mesh = obj.data

            # Used groups from weight paint
            vertex: bpy.types.MeshVertex
            for vertex in mesh.vertices:
                vertex_group: bpy.types.VertexGroupElement
                for vertex_group in vertex.groups:
                    if vertex_group.weight < self.weight_threshold:
                        continue

                    vertex_group_indices = vertex_group.group
                    used_vertex_group_indices.add(vertex_group_indices)

            vertex_groups = obj.vertex_groups

            # Used groups from modifiers
            for modifier in obj.modifiers:
                vertex_group = getattr(modifier, 'vertex_group', None)
                if not vertex_group:
                    continue

                if vertex_group not in vertex_groups:
                    continue

                vertex_group_index = vertex_groups[vertex_group].index
                used_vertex_group_indices.add(vertex_group_index)

            # Used groups from shape keys
            if mesh.shape_keys:
                key_block: bpy.types.ShapeKey
                for key_block in mesh.shape_keys.key_blocks:
                    if not key_block.vertex_group:
                        continue

                    vertex_group = vertex_groups.get(key_block.vertex_group)
                    if not vertex_group:
                        continue

                    used_vertex_group_indices.add(vertex_group.index)

            for vertex_group in list(reversed(vertex_groups)):
                if vertex_group.index in used_vertex_group_indices:
                    continue
                vertex_groups.remove(vertex_group)

        return {'FINISHED'}


class SelectShapeKeyTargetVertices(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_shape_key_target_vertices'
    bl_label = _('Select Shape Key Target Vertices')
    bl_description = _('Select shape key target vertices from the active meshes')
    bl_options = {'REGISTER', 'UNDO'}

    distance_threshold: bpy.props.FloatProperty(name=_('Distance Threshold'), default=0.0, min=0.0)

    @classmethod
    def poll(cls, context):
        if context.mode != 'EDIT_MESH':
            return False

        obj = context.active_object

        if obj is None:
            return False

        return obj.type == 'MESH'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object

        distance_threshold = self.distance_threshold

        obj_mesh: bpy.types.Mesh = obj.data
        shape_keys = obj_mesh.shape_keys
        key_block = shape_keys.key_blocks[obj.active_shape_key_index]
        relative_key_block = key_block.relative_key

        mesh = bmesh.from_edit_mesh(obj_mesh)  # pylint: disable=assignment-from-no-return
        mesh.select_mode |= {'VERT'}
        bmesh_vertices = mesh.verts
        for i, (origin, morph) in enumerate(zip(relative_key_block.data, key_block.data)):
            if (origin.co - morph.co).length > distance_threshold:
                bmesh_vertices[i].select_set(True)

        mesh.select_flush_mode()

        bmesh.update_edit_mesh(obj_mesh)

        return {'FINISHED'}


class RemoveUnusedShapeKeys(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.remove_unused_shape_keys'
    bl_label = _('Remove Unused Shape Keys')
    bl_description = _('Remove unused shape keys from the active meshes')
    bl_options = {'REGISTER', 'UNDO'}

    distance_threshold: bpy.props.FloatProperty(name=_('Distance Threshold'), default=0.0, min=0.0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            used_key_block_names = set()

            distance_threshold = self.distance_threshold

            mesh = obj.data
            shape_keys = mesh.shape_keys
            key_blocks = shape_keys.key_blocks

            for key_block in key_blocks:

                is_used = False

                for origin, morph in zip(mesh.vertices, key_block.data):
                    if (origin.co - morph.co).length > distance_threshold:
                        is_used = True
                        break

                if is_used:
                    used_key_block_names.add(key_block.name)

            # Used shape keys from relative key
            for used_key_block_name in list(used_key_block_names):
                current_key = key_blocks[used_key_block_name]

                while True:
                    relative_key = current_key.relative_key

                    if relative_key.name in used_key_block_names:
                        break

                    used_key_block_names.add(relative_key.name)

                    if current_key.name == relative_key.name:
                        break

                    current_key = relative_key

            for key_block in list(reversed(key_blocks)):
                if key_block.name in used_key_block_names:
                    continue

                # setting the active shapekey
                obj.active_shape_key_index = key_blocks.keys().index(key_block.name)

                # delete it
                bpy.ops.object.shape_key_remove()

        return {'FINISHED'}


class SelectMovedPoseBones(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_moved_pose_bones'
    bl_label = _('Select Moved Pose Bones')
    bl_options = {'REGISTER', 'UNDO'}

    select_rotated: bpy.props.BoolProperty(name=_('Rotated'), default=False)
    select_translated: bpy.props.BoolProperty(name=_('Translated'), default=False)
    select_scaled: bpy.props.BoolProperty(name=_('Scaled'), default=False)

    tolerance: bpy.props.FloatProperty(name=_('Tolerance'), default=1e-07)

    def execute(self, context):
        tolerance = self.tolerance

        def isclose(l: float, r: float) -> bool:
            return math.isclose(l, r, abs_tol=tolerance)

        obj: bpy.types.Object
        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue

            pose_bone: bpy.types.PoseBone
            for pose_bone in obj.pose.bones:
                if not self.select_translated:
                    is_not_translated = True
                else:
                    is_not_translated = isclose(pose_bone.location.x, 0) and isclose(pose_bone.location.y, 0) and isclose(pose_bone.location.z, 0)

                if not self.select_rotated:
                    is_not_rotated = True
                elif pose_bone.rotation_mode == 'QUATERNION':
                    is_not_rotated = isclose(pose_bone.rotation_quaternion.w, 1) and isclose(pose_bone.rotation_quaternion.x, 0) and isclose(pose_bone.rotation_quaternion.y, 0) and isclose(pose_bone.rotation_quaternion.z, 0)
                elif pose_bone.rotation_mode == 'AXIS_ANGLE':
                    is_not_rotated = True
                else:
                    is_not_rotated = isclose(pose_bone.rotation_euler.x, 0) and isclose(pose_bone.rotation_euler.y, 0) and isclose(pose_bone.rotation_euler.z, 0)

                if not self.select_scaled:
                    is_not_scaled = True
                else:
                    is_not_scaled = isclose(pose_bone.scale.x, 1) and isclose(pose_bone.scale.y, 1) and isclose(pose_bone.scale.z, 1)

                if is_not_rotated and is_not_translated and is_not_scaled:
                    continue

                pose_bone.bone.select = True

        return {'FINISHED'}


class AutoSegmentationOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.mesh_auto_segment'
    bl_label = _('Auto Segmentation')
    bl_options = {'REGISTER', 'UNDO'}

    cost_threshold: bpy.props.FloatProperty(name=_('Cost Threshold'), default=2.5, min=0, soft_max=3.0, step=1)

    maximum_area_threshold: bpy.props.FloatProperty(name=_('Maximum Area Threshold'), default=0.500, min=0, soft_max=1.0, precision=3, step=1)
    minimum_area_threshold: bpy.props.FloatProperty(name=_('Minimum Area Threshold'), default=0.001, min=0, soft_max=1.0, precision=3, step=1)

    face_angle_cost_factor: bpy.props.FloatProperty(name=_('Face Angle Cost Factor'), default=1.0, min=0, soft_max=2.0, step=1)
    perimeter_cost_factor: bpy.props.FloatProperty(name=_('Perimeter Cost Factor'), default=0.0, min=0, soft_max=10.0, step=1)
    material_change_cost_factor: bpy.props.FloatProperty(name=_('Material Change Cost Factor'), default=0.3, min=0, soft_max=1.0, step=1)
    edge_sharp_cost_factor: bpy.props.FloatProperty(name=_('Edge Sharp Cost Factor'), default=0.0, min=0, soft_max=1.0, step=1)
    edge_seam_cost_factor: bpy.props.FloatProperty(name=_('Edge Seam Cost Factor'), default=0.0, min=0, soft_max=1.0, step=1)
    vertex_group_weight_cost_factor: bpy.props.FloatProperty(name=_('Vertex Group Weight Cost Factor'), default=0.1, min=0, soft_max=1.0, step=1)
    vertex_group_change_cost_factor: bpy.props.FloatProperty(name=_('Vertex Group Change Cost Factor'), default=0.5, min=0, soft_max=1.0, step=1)

    edge_length_factor: bpy.props.FloatProperty(name=_('Edge Length Factor'), default=1.0, min=0, soft_max=1.0, step=1)

    segmentation_vertex_color_random_seed: bpy.props.IntProperty(name=_('Segmentation Vertex Color Random Seed'), default=0, min=0)
    segmentation_vertex_color_attribute_name: bpy.props.StringProperty(name=_('Segmentation Vertex Color Attribute Name'), default='Segmentation')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.active_object is None:
            return False
        return context.active_object.type == 'MESH'

    def execute(self, context: bpy.types.Context):
        mesh_object = context.active_object

        previous_mode = mesh_object.mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')

            operator_start_secs = time.perf_counter()

            target_bmesh: bmesh.types.BMesh = bmesh.new()
            mesh: bpy.types.Mesh = mesh_object.data
            target_bmesh.from_mesh(mesh, face_normals=False, vertex_normals=False)
            color_layer = segmentation.get_color_layer(target_bmesh, self.segmentation_vertex_color_attribute_name)

            auto_segment_start_secs = time.perf_counter()

            segment_result = segmentation.auto_segment(
                target_bmesh,
                self.cost_threshold,
                self.maximum_area_threshold,
                self.minimum_area_threshold,
                self.edge_length_factor,
                self.face_angle_cost_factor,
                self.perimeter_cost_factor,
                self.vertex_group_weight_cost_factor,
                self.vertex_group_change_cost_factor,
                self.material_change_cost_factor,
                self.edge_sharp_cost_factor,
                self.edge_seam_cost_factor,
                segmentation.get_ignore_vertex_group_indices(mesh_object)
            )

            auto_segment_end_secs = time.perf_counter()

            segments = segment_result.segments

            if len(segments) == 0:
                self.report({'WARNING'}, _("There is no target segment; In Edit Mode, select the faces you want to paint."))
                return {'FINISHED'}

            max_segment_area = sys.float_info.min
            min_segment_area = sys.float_info.max
            total_tri_loops = 0

            for segment in segments:
                segment_area = segment.area
                max_segment_area = max(max_segment_area, segment_area)
                min_segment_area = min(min_segment_area, segment_area)
                total_tri_loops += len(segment.tri_loop0s)

            cost_sorted_segment_contacts = segment_result.remain_segment_contacts
            max_cost_normalized = cost_sorted_segment_contacts[-1].cost_normalized if len(cost_sorted_segment_contacts) > 0 else 0

            segmentation.assign_vertex_colors(
                segments,
                color_layer,
                self.segmentation_vertex_color_random_seed,
            )

            target_bmesh.to_mesh(mesh)

            segmentation.setup_materials(mesh, self.segmentation_vertex_color_attribute_name)
            segmentation.setup_aovs(context.view_layer.aovs, self.segmentation_vertex_color_attribute_name)

            operator_end_secs = time.perf_counter()

            self.report({'INFO'}, f"""contact: {len(cost_sorted_segment_contacts)}, cost last/max: {segment_result.last_merged_cost}/{max_cost_normalized}
segment: {len(segments)}, area min/max: {min_segment_area}/{max_segment_area}
loop: {total_tri_loops}
operation: {operator_end_secs-operator_start_secs} secs, auto_segment {auto_segment_end_secs-auto_segment_start_secs} secs
""")

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {'FINISHED'}


class PaintSelectedFacesOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.mesh_paint_selected_faces'
    bl_label = _('Paint Selected Faces')
    bl_options = {'REGISTER', 'UNDO'}

    random_color: bpy.props.BoolProperty(name=_('Random Color'), default=False)
    segmentation_vertex_color_attribute_name: bpy.props.StringProperty(name=_('Segmentation Vertex Color Attribute Name'), default='Segmentation')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.active_object is None:
            return False
        return context.active_object.type == 'MESH'

    def execute(self, context: bpy.types.Context):
        mesh_object = context.active_object

        previous_mode = mesh_object.mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')

            segment_color = None
            if not self.random_color:
                if context.tool_settings.vertex_paint.palette.colors.active is not None:
                    segment_color = list(context.tool_settings.vertex_paint.palette.colors.active.color) + [1.0]

            segmentation.paint_selected_face_colors(
                mesh_object,
                segment_color,
                self.segmentation_vertex_color_attribute_name
            )

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {'FINISHED'}


SEGMENTATION_COLOR_PALETTE_NAME = 'Segmentation Color Palette'


class SetupSegmentationColorPaletteOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.setup_segmentation_color_palette'
    bl_label = _('Setup Segmentation Color Palette')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.tool_settings.vertex_paint.palette is None:
            return True
        return context.tool_settings.vertex_paint.palette.name != SEGMENTATION_COLOR_PALETTE_NAME

    def execute(self, context: bpy.types.Context):
        palette: bpy.types.Palette = bpy.data.palettes.get(SEGMENTATION_COLOR_PALETTE_NAME)
        if palette is None:
            palette = bpy.data.palettes.new(SEGMENTATION_COLOR_PALETTE_NAME)
            palette_colors = palette.colors
            for color in segmentation.SEGMANTATION_COLORS:
                palette_colors.new().color = color[:3]

        context.tool_settings.vertex_paint.palette = palette

        return {'FINISHED'}


class RestoreSegmentationColorPaletteOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.restore_segmentation_color_palette'
    bl_label = _('Restore Segmentation Color Palette')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.tool_settings.vertex_paint.palette is None:
            return True
        return context.tool_settings.vertex_paint.palette.name == SEGMENTATION_COLOR_PALETTE_NAME

    def execute(self, context: bpy.types.Context):
        palette: bpy.types.Palette = bpy.data.palettes.get(SEGMENTATION_COLOR_PALETTE_NAME)
        palette_colors = palette.colors
        palette_colors.clear()
        for color in segmentation.SEGMANTATION_COLORS:
            palette_colors.new().color = color[:3]

        return {'FINISHED'}
