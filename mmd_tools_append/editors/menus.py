# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import bpy

from ..editors.operators import (
    DissolveWeightBone,
    RemoveUnusedShapeKeys,
    RemoveUnusedVertexGroups,
    SelectMovedPoseBones,
    SelectShapeKeyTargetVertices,
)


class RemoveUnusedVertexGroupsMenu(bpy.types.Menu):
    bl_idname = "VGROUP_MT_mmd_tools_append_remove_unused_vertex_groups"
    bl_label = "MMD Append"

    def draw(self, _):
        pass

    @staticmethod
    def draw_menu(this, _):
        this.layout.operator(RemoveUnusedVertexGroups.bl_idname)

    @staticmethod
    def register():
        bpy.types.MESH_MT_vertex_group_context_menu.append(RemoveUnusedVertexGroupsMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.MESH_MT_vertex_group_context_menu.remove(RemoveUnusedVertexGroupsMenu.draw_menu)


class DissolveWeightBoneMenu(bpy.types.Menu):
    bl_idname = "ARMATURE_MT_mmd_tools_append_dissolve_weight_bone"
    bl_label = "MMD Append"

    def draw(self, _):
        pass

    @staticmethod
    def draw_menu(this, _):
        this.layout.operator(DissolveWeightBone.bl_idname)

    @staticmethod
    def register():
        bpy.types.VIEW3D_MT_edit_armature_delete.append(DissolveWeightBoneMenu.draw_menu)
        bpy.types.VIEW3D_MT_armature_context_menu.append(DissolveWeightBoneMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.VIEW3D_MT_edit_armature_delete.remove(DissolveWeightBoneMenu.draw_menu)
        bpy.types.VIEW3D_MT_armature_context_menu.remove(DissolveWeightBoneMenu.draw_menu)


class SelectShapeKeyTargetVerticesMenu(bpy.types.Menu):
    bl_idname = "SHAPEKEY_MT_mmd_tools_append_select_shape_key_target_vertices"
    bl_label = "MMD Append"

    def draw(self, _):
        pass

    @staticmethod
    def draw_menu(this, _):
        this.layout.operator(SelectShapeKeyTargetVertices.bl_idname)

    @staticmethod
    def register():
        bpy.types.MESH_MT_shape_key_context_menu.append(SelectShapeKeyTargetVerticesMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.MESH_MT_shape_key_context_menu.remove(SelectShapeKeyTargetVerticesMenu.draw_menu)


class RemoveUnusedShapeKeysMenu(bpy.types.Menu):
    bl_idname = "VGROUP_MT_mmd_tools_append_remove_unused_shape_keys"
    bl_label = "MMD Append"

    def draw(self, context):
        pass

    @staticmethod
    def draw_menu(this, _):
        this.layout.operator(RemoveUnusedShapeKeys.bl_idname)

    @staticmethod
    def register():
        bpy.types.MESH_MT_shape_key_context_menu.append(RemoveUnusedShapeKeysMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.MESH_MT_shape_key_context_menu.remove(RemoveUnusedShapeKeysMenu.draw_menu)


class SelectMovedPoseBonesMenu(bpy.types.Menu):
    bl_idname = "POSE_MT_mmd_tools_append_select_moved_pose_bones"
    bl_label = "Select Moved"

    def draw(self, _context):
        layout = self.layout

        operator = layout.operator(SelectMovedPoseBones.bl_idname, text="Moved")
        operator.select_rotated = True
        operator.select_translated = True
        operator.select_scaled = True

        operator = layout.operator(SelectMovedPoseBones.bl_idname, text="Rotated")
        operator.select_rotated = True
        operator.select_translated = False
        operator.select_scaled = False

        operator = layout.operator(SelectMovedPoseBones.bl_idname, text="Translated")
        operator.select_rotated = False
        operator.select_translated = True
        operator.select_scaled = False

        operator = layout.operator(SelectMovedPoseBones.bl_idname, text="Scaled")
        operator.select_rotated = False
        operator.select_translated = False
        operator.select_scaled = True

    @staticmethod
    def draw_menu(this, _):
        this.layout.menu(SelectMovedPoseBonesMenu.bl_idname)

    @staticmethod
    def register():
        bpy.types.VIEW3D_MT_select_pose.append(SelectMovedPoseBonesMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.VIEW3D_MT_select_pose.remove(SelectMovedPoseBonesMenu.draw_menu)
