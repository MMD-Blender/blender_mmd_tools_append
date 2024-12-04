# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Iterable

import bpy
from ...editors.meshes import MeshEditor
from ...m17n import _
from ...utilities import import_mmd_tools


class UuuNyaaRigidBodyAdjusterPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_rigid_body_adjuster'
    bl_label = _('UuuNyaa Rigid Body Adjuster')
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return MeshEditor(context.active_object).find_rigid_body_object() is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column()
        col.label(text=_('Batch Operation:'))
        col.operator('rigidbody.object_settings_copy', text=_('Copy to Selected'), icon='DUPLICATE')


class SelectMeshRigidBody(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_rigid_body_mesh'
    bl_label = _('Select Rigid Body Mesh')
    bl_options = {'REGISTER', 'UNDO'}

    only_in_mmd_model: bpy.props.BoolProperty(name=_('Only in the MMD Model'))
    only_same_settings: bpy.props.BoolProperty(name=_('Only the same Settings'))

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        if active_object.type != 'MESH':
            return False

        return MeshEditor(active_object).find_rigid_body_object() is not None

    @staticmethod
    def filter_only_in_mmd_model(key_object: bpy.types.Object) -> Iterable[bpy.types.Object]:
        mmd_tools = import_mmd_tools()
        mmd_root = mmd_tools.core.model.Model.findRoot(key_object)
        if mmd_root is None:
            return []

        return mmd_tools.core.model.Model(mmd_root).allObjects()

    def execute(self, context: bpy.types.Context):
        key_object = context.active_object
        key_rigid_body_object = key_object.find_rigid_body_object()

        obj: bpy.types.Object
        for obj in self.filter_only_in_mmd_model(key_object) if self.only_in_mmd_model else bpy.data.objects:
            if obj.type != 'MESH':
                continue

            rigid_body_object = MeshEditor(obj).find_rigid_body_object()
            if rigid_body_object is None:
                continue

            if self.only_same_settings and rigid_body_object != key_rigid_body_object:
                continue

            obj.select_set(True)

        return {'FINISHED'}
