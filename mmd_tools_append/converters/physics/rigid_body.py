# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

from collections.abc import Iterable

import bpy

from ...editors.meshes import MeshEditor
from ...utilities import import_mmd_tools


class MMDAppendRigidBodyAdjusterPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_rigid_body_adjuster"
    bl_label = "MMD Append Rigid Body Adjuster"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return MeshEditor(context.active_object).find_rigid_body_object() is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column()
        col.label(text="Batch Operation:")
        col.operator("rigidbody.object_settings_copy", text="Copy to Selected", icon="DUPLICATE")


class SelectMeshRigidBody(bpy.types.Operator):
    bl_idname = "mmd_tools_append.select_rigid_body_mesh"
    bl_label = "Select Rigid Body Mesh"
    bl_options = {"REGISTER", "UNDO"}

    only_in_mmd_model: bpy.props.BoolProperty(name="Only in the MMD Model")
    only_same_settings: bpy.props.BoolProperty(name="Only the same Settings")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != "OBJECT":
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        if active_object.type != "MESH":
            return False

        return MeshEditor(active_object).find_rigid_body_object() is not None

    @staticmethod
    def filter_only_in_mmd_model(key_object: bpy.types.Object) -> Iterable[bpy.types.Object]:
        mmd_tools = import_mmd_tools()
        mmd_root = mmd_tools.core.model.FnModel.find_root_object(key_object)
        if mmd_root is None:
            return []

        return mmd_tools.core.model.FnModel.iterate_child_objects(mmd_root)

    def execute(self, context: bpy.types.Context):
        key_object = context.active_object
        key_rigid_body_object = key_object.find_rigid_body_object()

        obj: bpy.types.Object
        for obj in self.filter_only_in_mmd_model(key_object) if self.only_in_mmd_model else bpy.data.objects:
            if obj.type != "MESH":
                continue

            rigid_body_object = MeshEditor(obj).find_rigid_body_object()
            if rigid_body_object is None:
                continue

            if self.only_same_settings and rigid_body_object != key_rigid_body_object:
                continue

            obj.select_set(True)

        return {"FINISHED"}
