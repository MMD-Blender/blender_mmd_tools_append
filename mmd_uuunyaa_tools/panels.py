# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import bpy

from .checkers.operators import CheckEeveeRenderingPerformance
from .converters.armatures.operators import (
    MMDArmatureAddMetarig, MMDAutoRigApplyMMDRestPose, MMDAutoRigConvert,
    MMDRigifyApplyMMDRestPose, MMDRigifyConvert, MMDRigifyIntegrateFocusOnMMD,
    MMDRigifyIntegrateFocusOnRigify)
from .converters.physics.cloth import (
    ConvertRigidBodyToClothOperator, RemoveMeshCloth, SelectClothMesh)
from .converters.physics.cloth_bone import \
    StretchBoneToVertexOperator
from .converters.physics.cloth_pyramid import (
    AddPyramidMeshByBreastBoneOperator, AssignPyramidWeightsOperator,
    ConvertPyramidMeshToClothOperator)
from .converters.physics.collision import (
    RemoveMeshCollision, SelectCollisionMesh)
from .editors.operators import (PaintSelectedFacesOperator, RestoreSegmentationColorPaletteOperator, SetupSegmentationColorPaletteOperator, AutoSegmentationOperator,
                                                 SetupRenderEngineForEevee,
                                                 SetupRenderEngineForToonEevee,
                                                 SetupRenderEngineForWorkbench)
from .generators.physics import AddCenterOfGravityObject
from .m17n import _
from .utilities import import_mmd_tools

mmd_tools = import_mmd_tools()


class OperatorPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_operator_panel'
    bl_label = _('UuuNyaa Operator')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MMD'
    bl_context = ''

    def draw(self, _context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text=_('Render:'), icon='SCENE_DATA')
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(SetupRenderEngineForEevee.bl_idname, icon='SCENE')
        grid.row(align=True).operator(SetupRenderEngineForWorkbench.bl_idname, icon='SCENE')
        grid.row(align=True).operator(SetupRenderEngineForToonEevee.bl_idname, icon='SCENE')
        grid.row(align=True).operator(CheckEeveeRenderingPerformance.bl_idname, icon='MOD_TIME')

        col = layout.column(align=True)
        col.label(text=_('MMD to Rigify:'), icon='OUTLINER_OB_ARMATURE')
        grid = col.grid_flow(row_major=True, align=True)
        row = grid.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.operator(MMDArmatureAddMetarig.bl_idname, text=_('Add Metarig'), icon='ADD').is_clean_armature = True
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator(MMDArmatureAddMetarig.bl_idname, text=_(''), icon='WINDOW')

        row = grid.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.operator(MMDRigifyIntegrateFocusOnMMD.bl_idname, icon='GROUP_BONE').is_join_armatures = True
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator(MMDRigifyIntegrateFocusOnMMD.bl_idname, text=_(''), icon='WINDOW')

        row = grid.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.operator(MMDRigifyIntegrateFocusOnRigify.bl_idname, icon='GROUP_BONE').is_join_armatures = True
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator(MMDRigifyIntegrateFocusOnRigify.bl_idname, text=_(''), icon='WINDOW')

        col = layout.column(align=True)
        col.label(text=_('Rigify to MMD:'), icon='OUTLINER_OB_ARMATURE')
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(MMDRigifyConvert.bl_idname, text=_('Convert to MMD compatible'), icon='ARMATURE_DATA')
        grid.row(align=True).operator(MMDRigifyApplyMMDRestPose.bl_idname, text=_('Apply MMD Rest Pose'))

        col.label(text=_('(Experimental) Auto-Rig to MMD:'), icon='OUTLINER_OB_ARMATURE')
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(MMDAutoRigConvert.bl_idname, text=_('Convert to MMD compatible'), icon='ARMATURE_DATA')
        grid.row(align=True).operator(MMDAutoRigApplyMMDRestPose.bl_idname, text=_('Apply MMD Rest Pose'))


class UuuNyaaPhysicsPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_physics'
    bl_label = _('UuuNyaa Physics')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MMD'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text=_('Relevant Selection:'), icon='RESTRICT_SELECT_OFF')
        grid = col.grid_flow(row_major=True)
        row = grid.row(align=True)
        row.label(text=_('Collision Mesh'), icon='MOD_PHYSICS')
        row.operator(SelectCollisionMesh.bl_idname, text=_(''), icon='RESTRICT_SELECT_OFF')
        row.operator(RemoveMeshCollision.bl_idname, text=_(''), icon='TRASH')

        mmd_root_object = mmd_tools.core.model.Model.findRoot(context.active_object)
        if mmd_root_object is None:
            col = layout.column(align=True)
            col.label(text=_('MMD Model is not selected.'), icon='ERROR')
        else:
            mmd_root = mmd_root_object.mmd_root

            row = grid.row(align=True)
            row.label(text=_('Rigid Body'), icon='RIGID_BODY')
            row.operator_context = 'EXEC_DEFAULT'
            operator = row.operator('mmd_tools.rigid_body_select', text=_(''), icon='RESTRICT_SELECT_OFF')
            operator.properties = set(['collision_group_number', 'shape'])
            row.operator_context = 'INVOKE_DEFAULT'
            row.prop(mmd_root, 'show_rigid_bodies', toggle=True, icon_only=True, icon='HIDE_OFF' if mmd_root.show_rigid_bodies else 'HIDE_ON')
            row.operator('rigidbody.objects_remove', text=_(''), icon='TRASH')

            row = grid.row(align=True)
            row.label(text=_('Cloth Mesh'), icon='MOD_CLOTH')
            row.operator(SelectClothMesh.bl_idname, text=_(''), icon='RESTRICT_SELECT_OFF')
            row.prop(mmd_root_object, 'mmd_uuunyaa_tools_show_cloths', toggle=True, icon_only=True, icon='HIDE_OFF' if mmd_root_object.mmd_uuunyaa_tools_show_cloths else 'HIDE_ON')
            row.operator(RemoveMeshCloth.bl_idname, text=_(''), icon='TRASH')

            col = layout.column(align=True)
            col.label(text=_('Converter:'), icon='SHADERFX')

            row = col.row(align=True)
            row.operator_context = 'EXEC_DEFAULT'
            row.operator(ConvertRigidBodyToClothOperator.bl_idname, text=_('Rigid Body to Cloth'), icon='MATCLOTH')
            row.operator_context = 'INVOKE_DEFAULT'
            row.operator(ConvertRigidBodyToClothOperator.bl_idname, text=_(''), icon='WINDOW')

        col = layout.column(align=True)
        col.label(text=_('Pyramid Cloth:'), icon='MESH_CONE')
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(AddPyramidMeshByBreastBoneOperator.bl_idname, text=_('Add Pyramid'), icon='CONE')
        grid.row(align=True).operator(ConvertPyramidMeshToClothOperator.bl_idname, text=_('Pyramid to Cloth'), icon='MOD_CLOTH')
        grid.row(align=True).operator(AssignPyramidWeightsOperator.bl_idname, text=_('Repaint Weight'), icon='WPAINT_HLT')

        col = layout.column(align=True)
        col.label(text=_('Misc:'), icon='BLENDER')
        grid = col.grid_flow(row_major=True)
        grid.row(align=True).operator(StretchBoneToVertexOperator.bl_idname, text=_('Stretch Bone to Vertex'), icon='CONSTRAINT_BONE')
        grid.row(align=True).operator(AddCenterOfGravityObject.bl_idname, text=_('Add Center of Gravity'), icon='ORIENTATION_CURSOR')

    @staticmethod
    def _toggle_visibility_of_cloths(obj, context):
        mmd_root_object = mmd_tools.core.model.Model.findRoot(obj)
        mmd_model = mmd_tools.core.model.Model(mmd_root_object)
        hide = not mmd_root_object.mmd_uuunyaa_tools_show_cloths

        with mmd_tools.bpyutils.activate_layer_collection(mmd_root_object):
            cloth_object: bpy.types.Object
            for cloth_object in mmd_model.cloths():
                cloth_object.hide = hide

            if hide and context.active_object is None:
                context.view_layer.objects.active = mmd_root_object

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_uuunyaa_tools_show_cloths = bpy.props.BoolProperty(
            default=True,
            update=UuuNyaaPhysicsPanel._toggle_visibility_of_cloths
        )

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_uuunyaa_tools_show_cloths


class UuuNyaaSegmentationPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_segmentation'
    bl_label = _('UuuNyaa Segmentation')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode in {'PAINT_VERTEX', 'EDIT_MESH'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        mmd_uuunyaa_tools_segmentation = context.scene.mmd_uuunyaa_tools_segmentation

        col = layout.column()
        col.prop(mmd_uuunyaa_tools_segmentation, 'segmentation_vertex_color_attribute_name', text=_("Color Layer&AOV Name"))
        if SetupSegmentationColorPaletteOperator.poll(context):
            col.operator(SetupSegmentationColorPaletteOperator.bl_idname, icon='RESTRICT_COLOR_ON')
        else:
            col.operator(RestoreSegmentationColorPaletteOperator.bl_idname, icon='MOD_TINT')
            col.template_palette(context.tool_settings.vertex_paint, 'palette')
            row = col.row(align=True)
            op = row.operator(PaintSelectedFacesOperator.bl_idname, icon='BRUSH_DATA')
            op.segmentation_vertex_color_attribute_name = mmd_uuunyaa_tools_segmentation.segmentation_vertex_color_attribute_name
            op.random_color = False
            op = row.operator(PaintSelectedFacesOperator.bl_idname, text='',  icon='RESTRICT_COLOR_OFF')
            op.segmentation_vertex_color_attribute_name = mmd_uuunyaa_tools_segmentation.segmentation_vertex_color_attribute_name
            op.random_color = True

        col.label(text=_('Auto Segmentation:'), icon='MOD_EXPLODE')
        box = col.box().column(align=True)

        box.label(text=_('Thresholds:'))
        flow = box.grid_flow()
        flow.row(align=True).prop(mmd_uuunyaa_tools_segmentation, 'cost_threshold', text=_("Cost"))
        row = flow.row(align=True)
        row.prop(mmd_uuunyaa_tools_segmentation, 'maximum_area_threshold', text=_("Area Max"))
        row.prop(mmd_uuunyaa_tools_segmentation, 'minimum_area_threshold', text=_("Min"))

        box.label(text=_('Cost Factors:'))
        flow = box.grid_flow()
        row = flow.row(align=True)
        row.row().prop(mmd_uuunyaa_tools_segmentation, 'face_angle_cost_factor', text=_("Face Angle"))
        row.row().prop(mmd_uuunyaa_tools_segmentation, 'perimeter_cost_factor', text=_("Perimeter"))
        row.row().prop(mmd_uuunyaa_tools_segmentation, 'material_change_cost_factor', text=_("Material Change"))

        row = flow.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text=_('Edge '))
        row.prop(mmd_uuunyaa_tools_segmentation, 'edge_sharp_cost_factor', text=_("Sharp"))
        row.prop(mmd_uuunyaa_tools_segmentation, 'edge_seam_cost_factor', text=_("Seam"))

        row = flow.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text=_('Vertex Group '))
        row.prop(mmd_uuunyaa_tools_segmentation, 'vertex_group_weight_cost_factor', text=_("Weight"))
        row.prop(mmd_uuunyaa_tools_segmentation, 'vertex_group_change_cost_factor', text=_("Change"))

        box.label(text=_('Other Parameters:'))
        flow = box.grid_flow()
        flow.row().prop(mmd_uuunyaa_tools_segmentation, 'edge_length_factor')
        flow.row().prop(mmd_uuunyaa_tools_segmentation, 'segmentation_vertex_color_random_seed', text=_("Color Random Seed"))

        op = col.operator(AutoSegmentationOperator.bl_idname, text=_("Execute Auto Segmentation"), icon='BRUSH_DATA')
        op.cost_threshold = mmd_uuunyaa_tools_segmentation.cost_threshold
        op.maximum_area_threshold = mmd_uuunyaa_tools_segmentation.maximum_area_threshold
        op.minimum_area_threshold = mmd_uuunyaa_tools_segmentation.minimum_area_threshold
        op.face_angle_cost_factor = mmd_uuunyaa_tools_segmentation.face_angle_cost_factor
        op.perimeter_cost_factor = mmd_uuunyaa_tools_segmentation.perimeter_cost_factor
        op.material_change_cost_factor = mmd_uuunyaa_tools_segmentation.material_change_cost_factor
        op.edge_sharp_cost_factor = mmd_uuunyaa_tools_segmentation.edge_sharp_cost_factor
        op.edge_seam_cost_factor = mmd_uuunyaa_tools_segmentation.edge_seam_cost_factor
        op.vertex_group_weight_cost_factor = mmd_uuunyaa_tools_segmentation.vertex_group_weight_cost_factor
        op.vertex_group_change_cost_factor = mmd_uuunyaa_tools_segmentation.vertex_group_change_cost_factor
        op.edge_length_factor = mmd_uuunyaa_tools_segmentation.edge_length_factor
        op.segmentation_vertex_color_random_seed = mmd_uuunyaa_tools_segmentation.segmentation_vertex_color_random_seed
        op.segmentation_vertex_color_attribute_name = mmd_uuunyaa_tools_segmentation.segmentation_vertex_color_attribute_name

        # tool_settings.vertex_paint.brush.color


class SegmentationPropertyGroup(bpy.types.PropertyGroup):
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

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Scene.mmd_uuunyaa_tools_segmentation = bpy.props.PointerProperty(type=SegmentationPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Scene.mmd_uuunyaa_tools_segmentation
