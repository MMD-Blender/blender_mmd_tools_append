# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import bpy
from ...converters.armatures import (AutoRigArmatureObject,
                                                    ControlType,
                                                    MMDRigifyArmatureObject)
from ...m17n import _


class MMDRigifyPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_mmd_rigify'
    bl_label = _('UuuNyaa MMD Rigify')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_context = ''

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        if not MMDRigifyArmatureObject.is_rigify_armature_object(active_object):
            return False

        return True

    def draw(self, context: bpy.types.Context):
        # pylint: disable=too-many-locals
        active_object = context.active_object
        pose_bones = active_object.pose.bones

        rigify_armature_object = MMDRigifyArmatureObject(active_object)
        bind_mmd_rigify = rigify_armature_object.datapaths[ControlType.BIND_MMD_UUUNYAA]
        eye_mmd_rigify = rigify_armature_object.datapaths[ControlType.EYE_MMD_UUUNYAA]
        leg_l_mmd_rigify = rigify_armature_object.datapaths[ControlType.LEG_L_MMD_UUUNYAA]
        leg_r_mmd_rigify = rigify_armature_object.datapaths[ControlType.LEG_R_MMD_UUUNYAA]
        toe_l_mmd_rigify = rigify_armature_object.datapaths[ControlType.TOE_L_MMD_UUUNYAA]
        toe_r_mmd_rigify = rigify_armature_object.datapaths[ControlType.TOE_R_MMD_UUUNYAA]
        arm_l_ik_fk = rigify_armature_object.datapaths[ControlType.ARM_L_IK_FK]
        arm_r_ik_fk = rigify_armature_object.datapaths[ControlType.ARM_R_IK_FK]
        leg_l_ik_fk = rigify_armature_object.datapaths[ControlType.LEG_L_IK_FK]
        leg_r_ik_fk = rigify_armature_object.datapaths[ControlType.LEG_R_IK_FK]

        layout = self.layout
        col = layout.column()

        is_mmd_integrated_object: bool = MMDRigifyArmatureObject.is_mmd_integrated_object(active_object)

        col.label(text=_('MMD-Rigify:'))
        if not is_mmd_integrated_object:
            col.label(text=_('Integrated armature is not selected.'))
        else:
            col.prop(pose_bones[bind_mmd_rigify.bone_name], bind_mmd_rigify.prop_data_path, text=_('Bind'), slider=True)
            col.prop(pose_bones[eye_mmd_rigify.bone_name], eye_mmd_rigify.prop_data_path, text=_('Eyes'), slider=True)
            row = col.row()
            row.prop(pose_bones[leg_l_mmd_rigify.bone_name], leg_l_mmd_rigify.prop_data_path, text=_('Leg.L'), slider=True)
            row.prop(pose_bones[leg_r_mmd_rigify.bone_name], leg_r_mmd_rigify.prop_data_path, text=_('Leg.R'), slider=True)
            row = col.row()
            row.prop(pose_bones[toe_l_mmd_rigify.bone_name], toe_l_mmd_rigify.prop_data_path, text=_('Toe.L'), slider=True)
            row.prop(pose_bones[toe_r_mmd_rigify.bone_name], toe_r_mmd_rigify.prop_data_path, text=_('Toe.R'), slider=True)

        col.label(text=_('IK-FK:'))
        row = col.row()
        row.prop(pose_bones[arm_l_ik_fk.bone_name], arm_l_ik_fk.prop_data_path, text=_('Arm.L'), slider=True)
        row.prop(pose_bones[arm_r_ik_fk.bone_name], arm_r_ik_fk.prop_data_path, text=_('Arm.R'), slider=True)
        row = col.row()
        row.prop(pose_bones[leg_l_ik_fk.bone_name], leg_l_ik_fk.prop_data_path, text=_('Leg.L'), slider=True)
        row.prop(pose_bones[leg_r_ik_fk.bone_name], leg_r_ik_fk.prop_data_path, text=_('Leg.R'), slider=True)

        if not is_mmd_integrated_object:
            return

        col.label(text=_('MMD Layers:'))
        row = col.row()
        row.prop(active_object.data, 'layers', index=24, toggle=True, text=_('Main'))

        row = col.row()
        row.prop(active_object.data, 'layers', index=25, toggle=True, text=_('Others'))

        row = col.row()
        row.prop(active_object.data, 'layers', index=26, toggle=True, text=_('Shadow'))

        row = col.row()
        row.prop(active_object.data, 'layers', index=27, toggle=True, text=_('Dummy'))


class AutoRigPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_mmd_autorig'
    bl_label = _('UuuNyaa MMD AutoRig')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_context = ''

    @classmethod
    def poll(cls, context):
        return AutoRigArmatureObject.is_autorig_armature_object(context.active_object)

    def draw(self, context: bpy.types.Context):
        # pylint: disable=too-many-locals
        active_object = context.active_object
        pose_bones = context.active_object.pose.bones

        autorig_armature_object = AutoRigArmatureObject(active_object)
        eye_mmd_autorig = autorig_armature_object.datapaths[ControlType.EYE_MMD_UUUNYAA]
        leg_l_mmd_autorig = autorig_armature_object.datapaths[ControlType.LEG_L_MMD_UUUNYAA]
        leg_r_mmd_autorig = autorig_armature_object.datapaths[ControlType.LEG_R_MMD_UUUNYAA]
        arm_l_ik_fk = autorig_armature_object.datapaths[ControlType.ARM_L_IK_FK]
        arm_r_ik_fk = autorig_armature_object.datapaths[ControlType.ARM_R_IK_FK]
        leg_l_ik_fk = autorig_armature_object.datapaths[ControlType.LEG_L_IK_FK]
        leg_r_ik_fk = autorig_armature_object.datapaths[ControlType.LEG_R_IK_FK]

        layout = self.layout
        col = layout.column()

        col.label(text=_('MMD-AutoRig:'))

        prop_storage_bone = pose_bones[AutoRigArmatureObject.prop_storage_bone_name]
        if AutoRigArmatureObject.prop_name_mmd_uuunyaa_bind_mmd_autorig not in prop_storage_bone:
            col.label(text=_('Integrated armature is not selected.'))
        else:
            col.prop(pose_bones[eye_mmd_autorig.bone_name], eye_mmd_autorig.prop_data_path, text=_('Eyes'), slider=True)
            row = col.row()
            row.prop(pose_bones[leg_l_mmd_autorig.bone_name], leg_l_mmd_autorig.prop_data_path, text=_('Leg.L'), slider=True)
            row.prop(pose_bones[leg_r_mmd_autorig.bone_name], leg_r_mmd_autorig.prop_data_path, text=_('Leg.R'), slider=True)

        col.label(text=_('IK-FK:'))
        row = col.row()
        row.prop(pose_bones[arm_l_ik_fk.bone_name], arm_l_ik_fk.prop_data_path, text=_('Arm.L'), slider=True)
        row.prop(pose_bones[arm_r_ik_fk.bone_name], arm_r_ik_fk.prop_data_path, text=_('Arm.R'), slider=True)
        row = col.row()
        row.prop(pose_bones[leg_l_ik_fk.bone_name], leg_l_ik_fk.prop_data_path, text=_('Leg.L'), slider=True)
        row.prop(pose_bones[leg_r_ik_fk.bone_name], leg_r_ik_fk.prop_data_path, text=_('Leg.R'), slider=True)

        col.label(text=_('Layers:'))
        row = col.row()
        row.prop(context.active_object.data, 'layers', index=0, toggle=True, text=_('Main'))

        row = col.row()
        row.prop(context.active_object.data, 'layers', index=1, toggle=True, text=_('Sub'))

        row = col.row()
        row.prop(context.active_object.data, 'layers', index=8, toggle=True, text=_('Spine'))

        row = col.row()
        row.prop(context.active_object.data, 'layers', index=10, toggle=True, text=_('Limbs'))
