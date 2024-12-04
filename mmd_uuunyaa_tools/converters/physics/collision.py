# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Iterable

import bpy
from ...editors.meshes import MeshEditor
from ...m17n import _
from ...tuners import TunerABC, TunerRegistry
from ...utilities import MessageException, import_mmd_tools


class CollisionTunerABC(TunerABC, MeshEditor):
    pass


class NothingCollisionTuner(CollisionTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_COLLISION_NOTHING'

    @classmethod
    def get_name(cls) -> str:
        return _('Nothing')

    def execute(self):
        pass


class ThinSmoothCollisionTuner(CollisionTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_COLLISION_THIN_SMOOTH'

    @classmethod
    def get_name(cls) -> str:
        return _('Thin Smooth')

    def execute(self):
        collision_settings: bpy.types.CollisionSettings = self.find_collision_settings()
        collision_settings.damping = 0.000
        collision_settings.thickness_outer = 0.001
        collision_settings.thickness_inner = 0.200
        collision_settings.cloth_friction = 0.000


TUNERS = TunerRegistry(
    (0, NothingCollisionTuner),
    (1, ThinSmoothCollisionTuner),
)


class UuuNyaaCollisionAdjusterPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_collision_adjuster'
    bl_label = _('UuuNyaa Collision Adjuster')
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return MeshEditor(context.active_object).find_collision_modifier() is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mesh_object: bpy.types.Object = context.active_object
        collision_settings = mesh_object.mmd_uuunyaa_tools_collision_settings

        col = layout.column()
        col.prop(collision_settings, 'presets')
        col.prop(collision_settings, 'damping', slider=True)
        col.prop(collision_settings, 'thickness_outer', slider=True)
        col.prop(collision_settings, 'thickness_inner', slider=True)
        col.prop(collision_settings, 'cloth_friction')

        col = layout.column()
        col.label(text=_('Batch Operation:'))
        col.operator(CopyCollisionAdjusterSettings.bl_idname, text=_('Copy to Selected'), icon='DUPLICATE')


class CopyCollisionAdjusterSettings(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.copy_collision_adjuster_settings'
    bl_label = _('Copy Collision Adjuster Settings')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len([o for o in context.selected_objects if o.type == 'MESH']) >= 2

    def execute(self, context: bpy.types.Context):
        from_object = context.active_object
        from_settings = from_object.mmd_uuunyaa_tools_collision_settings
        from_modifier = MeshEditor(from_object).get_collision_modifier()

        for to_object in context.selected_objects:
            if to_object.type != 'MESH':
                continue

            if from_object == to_object:
                continue

            MeshEditor(to_object).get_collision_modifier(from_modifier.name)

            to_settings = to_object.mmd_uuunyaa_tools_collision_settings
            to_settings.presets = from_settings.presets
            to_settings.damping = from_settings.damping
            to_settings.thickness_outer = from_settings.thickness_outer
            to_settings.thickness_inner = from_settings.thickness_inner
            to_settings.cloth_friction = from_settings.cloth_friction

        return {'FINISHED'}


class SelectCollisionMesh(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_collision_mesh'
    bl_label = _('Select Collision Mesh')
    bl_options = {'REGISTER', 'UNDO'}

    same_mmd_model: bpy.props.BoolProperty(name=_('Same MMD Model'))
    same_physics_settings: bpy.props.BoolProperty(name=_('Same Physics Settings'))

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        if active_object.type != 'MESH':
            return False

        return MeshEditor(active_object).find_collision_modifier() is not None

    @staticmethod
    def filter_only_in_mmd_model(key_object: bpy.types.Object) -> Iterable[bpy.types.Object]:
        mmd_tools = import_mmd_tools()
        mmd_root = mmd_tools.core.model.Model.findRoot(key_object)
        if mmd_root is None:
            return

        return mmd_tools.core.model.Model(mmd_root).allObjects()

    def execute(self, context: bpy.types.Context):
        key_object = context.active_object
        key_settings = key_object.mmd_uuunyaa_tools_collision_settings

        obj: bpy.types.Object
        for obj in self.filter_only_in_mmd_model(key_object) if self.same_mmd_model else bpy.data.objects:
            if obj.type != 'MESH':
                continue

            if MeshEditor(obj).find_collision_modifier() is None:
                continue

            if self.same_physics_settings and not key_settings.physics_equals(obj.mmd_uuunyaa_tools_collision_settings):
                continue

            obj.select_set(True)

        return {'FINISHED'}


class RemoveMeshCollision(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.remove_mesh_collision'
    bl_label = _('Remove Mesh Collision')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        if active_object.type != 'MESH':
            return False

        return MeshEditor(active_object).find_collision_modifier() is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: bpy.types.Context):
        try:
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue

                MeshEditor(obj).remove_collision_modifier()

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class CollisionAdjusterSettingsPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def _update_presets(prop, _):
        TUNERS[prop.presets](prop.id_data).execute()

    presets: bpy.props.EnumProperty(
        name=_('Presets'),
        items=TUNERS.to_enum_property_items(),
        update=_update_presets.__func__,
        default=None
    )

    damping: bpy.props.FloatProperty(
        name=_('Damping'), min=0.000, max=1.000, precision=3,
        get=lambda p: getattr(MeshEditor(p.id_data).find_collision_settings(), 'damping', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_collision_settings(), 'damping', v),
    )

    thickness_outer: bpy.props.FloatProperty(
        name=_('Thickness Outer'), min=0.001, max=1.000, precision=3,
        get=lambda p: getattr(MeshEditor(p.id_data).find_collision_settings(), 'thickness_outer', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_collision_settings(), 'thickness_outer', v),
    )

    thickness_inner: bpy.props.FloatProperty(
        name=_('Thickness Inner'), min=0.001, max=1.000, precision=3,
        get=lambda p: getattr(MeshEditor(p.id_data).find_collision_settings(), 'thickness_inner', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_collision_settings(), 'thickness_inner', v),
    )

    cloth_friction: bpy.props.FloatProperty(
        name=_('Cloth Friction'), min=0.000, max=80.000, step=10, precision=3,
        get=lambda p: getattr(MeshEditor(p.id_data).find_collision_settings(), 'cloth_friction', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_collision_settings(), 'cloth_friction', v),
    )

    def physics_equals(self, obj):
        return (
            isinstance(obj, CollisionAdjusterSettingsPropertyGroup)
            and self.presets == obj.presets
            and self.damping == obj.damping
            and self.thickness_outer == obj.thickness_outer
            and self.thickness_inner == obj.thickness_inner
            and self.cloth_friction == obj.cloth_friction
        )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_uuunyaa_tools_collision_settings = bpy.props.PointerProperty(type=CollisionAdjusterSettingsPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_uuunyaa_tools_collision_settings
