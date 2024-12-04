# -*- coding: utf-8 -*-
# Copyright 2022 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import List

import bpy
from ..m17n import _


class AddCenterOfGravityObject(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.add_center_of_gravity_object'
    bl_label = _('Add Center of Gravity')
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(name=_('Radius'), default=0.1, min=0.0, precision=4, unit='LENGTH')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode == 'POSE' and len(context.selected_pose_bones) > 0

    def execute(self, context: bpy.types.Context):
        armature_object: bpy.types.Object = context.active_object
        selected_pose_bones: List[bpy.types.PoseBone] = context.selected_pose_bones

        center_object: bpy.types.Object = bpy.data.objects.new('EMPTY', None)
        center_object.name = 'CenterOfGravity'
        center_object.empty_display_type = 'PLAIN_AXES'
        center_object.empty_display_size = self.radius
        center_object.show_in_front = True
        context.view_layer.active_layer_collection.collection.objects.link(center_object)

        total_bone_length = sum([b.length for b in selected_pose_bones])

        for pose_bone in selected_pose_bones:
            constraint: bpy.types.CopyLocationConstraint = center_object.constraints.new('COPY_LOCATION')
            constraint.name = f'CenterOfGravity.{pose_bone.name}'
            constraint.target = armature_object
            constraint.subtarget = pose_bone.name
            constraint.head_tail = 0.5
            constraint.use_offset = True
            constraint.influence = pose_bone.length / total_bone_length

        floor_object: bpy.types.Object = bpy.data.objects.new('EMPTY', None)
        floor_object.name = 'CenterOfGravityOnFloor'
        floor_object.parent = center_object
        floor_object.empty_display_type = 'SPHERE'
        floor_object.empty_display_size = self.radius
        floor_object.show_in_front = True
        context.view_layer.active_layer_collection.collection.objects.link(floor_object)

        constraint: bpy.types.CopyLocationConstraint = floor_object.constraints.new('COPY_LOCATION')
        constraint.target = armature_object
        constraint.use_x = False
        constraint.use_y = False
        constraint.use_z = True

        return {'FINISHED'}
