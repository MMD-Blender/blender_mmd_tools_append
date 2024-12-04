# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Iterable, List

import bpy
from ...editors.meshes import MeshEditor
from ...converters.physics.rigid_body_to_cloth import RigidBodyToClothConverter, PhysicsMode
from ...m17n import _
from ...tuners import TunerABC, TunerRegistry
from ...utilities import MessageException, import_mmd_tools


mmd_tools = import_mmd_tools()
if not hasattr(mmd_tools.core.model.Model, 'clothGroupObject'):
    def mmd_model_cloth_group_object_method(self):
        # pylint: disable=protected-access
        if not hasattr(self, '_cloth_grp'):
            self._cloth_grp = None
            for i in self.rootObject().children:
                if i.name == 'cloths':
                    self._cloth_grp = i
                    break

            if self._cloth_grp is None:
                cloths = bpy.data.objects.new(name='cloths', object_data=None)
                mmd_tools.bpyutils.SceneOp(bpy.context).link_object(cloths)
                cloths.parent = self.rootObject()
                cloths.hide = cloths.hide_select = True
                cloths.lock_rotation = cloths.lock_location = cloths.lock_scale = [True, True, True]
                self._cloth_grp = cloths

        return self._cloth_grp

    mmd_tools.core.model.Model.clothGroupObject = mmd_model_cloth_group_object_method

    def mmd_model_cloths_method(self):
        for obj in self.allObjects(self.clothGroupObject()):
            if obj.type != 'MESH':
                continue
            if MeshEditor(obj).find_cloth_modifier() is None:
                continue
            yield obj

    mmd_tools.core.model.Model.cloths = mmd_model_cloths_method


class ClothTunerABC(TunerABC, MeshEditor):
    pass


class NothingClothTuner(ClothTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_CLOTH_NOTHING'

    @classmethod
    def get_name(cls) -> str:
        return _('Nothing')

    def execute(self):
        pass


class CottonClothTuner(ClothTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_CLOTH_COTTON'

    @classmethod
    def get_name(cls) -> str:
        return _('Cotton')

    def execute(self):
        cloth_settings: bpy.types.ClothSettings = self.find_cloth_settings()
        cloth_settings.mass = 0.300
        cloth_settings.air_damping = 1.000
        cloth_settings.tension_stiffness = 15
        cloth_settings.compression_stiffness = 15
        cloth_settings.shear_stiffness = 15
        cloth_settings.bending_stiffness = 0.500
        cloth_settings.tension_damping = 5
        cloth_settings.compression_damping = 5
        cloth_settings.shear_damping = 5
        cloth_settings.bending_damping = 0.5


class SilkClothTuner(ClothTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_CLOTH_SILK'

    @classmethod
    def get_name(cls) -> str:
        return _('Silk')

    def execute(self):
        cloth_settings: bpy.types.ClothSettings = self.find_cloth_settings()
        cloth_settings.mass = 0.150
        cloth_settings.air_damping = 1.000
        cloth_settings.tension_stiffness = 5
        cloth_settings.compression_stiffness = 5
        cloth_settings.shear_stiffness = 5
        cloth_settings.bending_stiffness = 0.05
        cloth_settings.tension_damping = 0
        cloth_settings.compression_damping = 0
        cloth_settings.shear_damping = 0
        cloth_settings.bending_damping = 0.5


class BreastPyramidClothTuner(ClothTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_CLOTH_BREAST_PYRAMID'

    @classmethod
    def get_name(cls) -> str:
        return _('Breast Pyramid')

    def execute(self):
        cloth_settings: bpy.types.ClothSettings = self.find_cloth_settings()
        cloth_settings.mass = 1.000
        cloth_settings.air_damping = 1.000
        cloth_settings.tension_stiffness = 5
        cloth_settings.compression_stiffness = 5
        cloth_settings.shear_stiffness = 5
        cloth_settings.bending_stiffness = 0.05
        cloth_settings.tension_damping = 0
        cloth_settings.compression_damping = 0
        cloth_settings.shear_damping = 0
        cloth_settings.bending_damping = 0.5


TUNERS = TunerRegistry(
    (0, NothingClothTuner),
    (1, CottonClothTuner),
    (2, SilkClothTuner),
    (3, BreastPyramidClothTuner),
)


class UuuNyaaClothAdjuster(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_cloth_adjuster'
    bl_label = _('UuuNyaa Cloth Adjuster')
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return MeshEditor(context.active_object).find_cloth_modifier() is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mesh_object: bpy.types.Object = context.active_object
        cloth_settings = mesh_object.mmd_uuunyaa_tools_cloth_settings

        box = layout.box()
        col = box.column()
        col.prop(cloth_settings, 'presets')
        col.prop(cloth_settings, 'mass')
        col.prop(cloth_settings, 'stiffness')
        col.prop(cloth_settings, 'damping')

        col = box.column()
        col.label(text=_('Collision:'))
        col.prop(cloth_settings, 'collision_quality')
        col.prop(cloth_settings, 'distance_min', slider=True)
        col.prop(cloth_settings, 'impulse_clamp')

        col = box.column()
        col.label(text=_('Batch Operation:'))
        col.operator(CopyClothAdjusterSettings.bl_idname, text=_('Copy to Selected'), icon='DUPLICATE')

        col = layout.column(align=True)
        col.label(text=_('Cache:'))
        row = col.row(align=True)
        row.prop(cloth_settings, 'frame_start', text=_('Simulation Start'))
        row.prop(cloth_settings, 'frame_end', text=_('Simulation End'))

        if MeshEditor(mesh_object).find_subsurface_modifier('physics_cloth_subsurface') is None:
            return

        col = layout.column(align=True)
        col.label(text=_('Subdivision:'))
        col.prop(cloth_settings, 'subdivision_levels', text=_('Subdivision Levels'))


class CopyClothAdjusterSettings(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.copy_cloth_adjuster_settings'
    bl_label = _('Copy Cloth Adjuster Settings')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len([o for o in context.selected_objects if o.type == 'MESH']) >= 2

    def execute(self, context: bpy.types.Context):
        from_object = context.active_object
        from_settings = from_object.mmd_uuunyaa_tools_cloth_settings
        from_modifier = MeshEditor(from_object).get_cloth_modifier()

        for to_object in context.selected_objects:
            if to_object.type != 'MESH':
                continue

            if from_object == to_object:
                continue

            MeshEditor(to_object).get_cloth_modifier(from_modifier.name)

            to_settings = to_object.mmd_uuunyaa_tools_cloth_settings
            to_settings.presets = from_settings.presets
            to_settings.mass = from_settings.mass
            to_settings.stiffness = from_settings.stiffness
            to_settings.damping = from_settings.damping
            to_settings.collision_quality = from_settings.collision_quality
            to_settings.distance_min = from_settings.distance_min
            to_settings.impulse_clamp = from_settings.impulse_clamp

        return {'FINISHED'}


class SelectClothMesh(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_cloth_mesh'
    bl_label = _('Select Cloth Mesh')
    bl_options = {'REGISTER', 'UNDO'}

    only_in_mmd_model: bpy.props.BoolProperty(name=_('Same MMD Model'))
    only_physics_equals: bpy.props.BoolProperty(name=_('Same Physics Settings'))
    only_cache_equals: bpy.props.BoolProperty(name=_('Same Cache Settings'))

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        if active_object.type != 'MESH':
            return False

        return MeshEditor(active_object).find_cloth_modifier() is not None

    @staticmethod
    def filter_only_in_mmd_model(key_object: bpy.types.Object) -> Iterable[bpy.types.Object]:
        mmd_root = mmd_tools.core.model.Model.findRoot(key_object)
        if mmd_root is None:
            return

        mmd_model = mmd_tools.core.model.Model(mmd_root)

        for obj in mmd_model.meshes():
            yield obj

        yield from mmd_model.cloths()

    def execute(self, context: bpy.types.Context):
        key_object = context.active_object
        key_settings = key_object.mmd_uuunyaa_tools_cloth_settings

        obj: bpy.types.Object
        for obj in self.filter_only_in_mmd_model(key_object) if self.only_in_mmd_model else bpy.data.objects:
            if obj.type != 'MESH':
                continue

            if MeshEditor(obj).find_cloth_modifier() is None:
                continue

            if self.only_physics_equals and not key_settings.physics_equals(obj.mmd_uuunyaa_tools_cloth_settings):
                continue

            if self.only_cache_equals and not key_settings.cache_equals(obj.mmd_uuunyaa_tools_cloth_settings):
                continue

            obj.select_set(True)

        return {'FINISHED'}


class RemoveMeshCloth(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.remove_mesh_cloth'
    bl_label = _('Remove Mesh Cloth')
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

        return MeshEditor(active_object).find_cloth_modifier() is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: bpy.types.Context):
        try:
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue

                MeshEditor(obj).remove_cloth_modifier()

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class ConvertRigidBodyToClothOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.convert_rigid_body_to_cloth'
    bl_label = _('Convert Rigid Body to Cloth')
    bl_description = _('Select both the mesh to be deformed and the rigid body')
    bl_options = {'REGISTER', 'UNDO'}

    subdivision_level: bpy.props.IntProperty(name=_('Subdivision Levels'), min=0, max=5, default=0)
    ribbon_stiffness: bpy.props.FloatProperty(name=_('Ribbon Stiffness'), min=0, max=1, default=0.2)
    physics_mode: bpy.props.EnumProperty(
        name=_('Physics Mode'),
        items=[(m.name, m.value, '') for m in PhysicsMode],
        default=PhysicsMode.AUTO.name
    )
    extend_ribbon_area: bpy.props.BoolProperty(
        name=_('Extend Ribbon Area'),
        default=True
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        selected_mesh_mmd_root = None
        selected_rigid_body_mmd_root = None

        mmd_find_root = import_mmd_tools().core.model.Model.findRoot
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                return False

            if obj.mmd_type == 'RIGID_BODY':
                selected_rigid_body_mmd_root = mmd_find_root(obj)
            elif obj.mmd_type == 'NONE':
                selected_mesh_mmd_root = mmd_find_root(obj)

            if selected_rigid_body_mmd_root == selected_mesh_mmd_root:
                return selected_rigid_body_mmd_root is not None

        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        try:
            mmd_find_root = import_mmd_tools().core.model.Model.findRoot

            target_mmd_root_object = None
            rigid_body_objects: List[bpy.types.Object] = []
            mesh_objects: List[bpy.types.Object] = []

            obj: bpy.types.Object
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue

                mmd_root_object = mmd_find_root(obj)
                if mmd_root_object is None:
                    continue

                if target_mmd_root_object is None:
                    target_mmd_root_object = mmd_root_object
                elif target_mmd_root_object != mmd_root_object:
                    raise MessageException(_('Multiple MMD models selected. Please select single model at a time.'))

                if obj.mmd_type == 'RIGID_BODY':
                    rigid_body_objects.append(obj)
                elif obj.mmd_type == 'NONE':
                    mesh_objects.append(obj)

            RigidBodyToClothConverter.convert(
                target_mmd_root_object,
                rigid_body_objects,
                mesh_objects,
                self.subdivision_level,
                self.ribbon_stiffness,
                PhysicsMode[self.physics_mode],
                self.extend_ribbon_area
            )

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class ClothAdjusterSettingsPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def _update_presets(prop, _):
        TUNERS[prop.presets](prop.id_data).execute()

    presets: bpy.props.EnumProperty(
        name=_('Presets'),
        items=TUNERS.to_enum_property_items(),
        update=_update_presets.__func__,
        default=None
    )

    mass: bpy.props.FloatProperty(
        name=_('Vertex Mass'), min=0, soft_max=10, step=10, unit='MASS',
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_settings(), 'mass', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_settings(), 'mass', v),
    )

    @staticmethod
    def _set_stiffness(prop, value):
        cloth_settings: bpy.types.ClothSettings = MeshEditor(prop.id_data).find_cloth_settings()
        cloth_settings.tension_stiffness = value
        cloth_settings.compression_stiffness = value
        cloth_settings.shear_stiffness = value

    stiffness: bpy.props.FloatProperty(
        name=_('Stiffness'), min=0, soft_max=50, max=10000, precision=3, step=10,
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_settings(), 'tension_stiffness', 0),
        set=_set_stiffness.__func__,
    )

    @staticmethod
    def _set_damping(prop, value):
        cloth_settings: bpy.types.ClothSettings = MeshEditor(prop.id_data).find_cloth_settings()
        cloth_settings.tension_damping = value
        cloth_settings.compression_damping = value
        cloth_settings.shear_damping = value

    damping: bpy.props.FloatProperty(
        name=_('Damping'), min=0, max=50, precision=3, step=10,
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_settings(), 'tension_damping', 0),
        set=_set_damping.__func__,
    )

    collision_quality: bpy.props.IntProperty(
        name=_('Collision Quality'), min=1, max=20,
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'collision_quality', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'collision_quality', v),
    )

    distance_min: bpy.props.FloatProperty(
        name=_('Minimum Distance'), min=0.001, max=1.000, step=10, unit='LENGTH',
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'distance_min', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'distance_min', v),
    )

    impulse_clamp: bpy.props.FloatProperty(
        name=_('Impulse Clamping'), min=0, max=100, precision=3, step=10,
        get=lambda p: getattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'impulse_clamp', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_collision_settings(), 'impulse_clamp', v),
    )

    frame_start: bpy.props.IntProperty(
        name=_('Simulation Start'), min=0, max=1048574,
        get=lambda p: getattr(getattr(MeshEditor(p.id_data).find_cloth_modifier(), 'point_cache', None), 'frame_start', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_modifier().point_cache, 'frame_start', v),
    )

    frame_end: bpy.props.IntProperty(
        name=_('Simulation End'), min=1, max=1048574,
        get=lambda p: getattr(getattr(MeshEditor(p.id_data).find_cloth_modifier(), 'point_cache', None), 'frame_end', 0),
        set=lambda p, v: setattr(MeshEditor(p.id_data).find_cloth_modifier().point_cache, 'frame_end', v),
    )

    @staticmethod
    def _set_subdivision_levels(prop, subdivision_level):
        cloth_mesh_object: bpy.types.Object = prop.id_data
        cloth_mesh_editor = MeshEditor(cloth_mesh_object)

        cloth_subsurface_modifier = cloth_mesh_editor.find_subsurface_modifier(name='physics_cloth_subsurface')
        if cloth_subsurface_modifier is None:
            return

        def set_bind_modifier(modifier: bpy.types.Modifier, bind: bool):
            if modifier is None:
                return

            if bind and not modifier.show_viewport:
                return

            if modifier.type == 'SURFACE_DEFORM':
                if bind == modifier.is_bound:
                    return
                bpy.ops.object.surfacedeform_bind({'object': modifier.id_data}, modifier=modifier.name)
            elif modifier.type == 'CORRECTIVE_SMOOTH':
                if bind == modifier.is_bind:
                    return
                bpy.ops.object.correctivesmooth_bind({'object': modifier.id_data}, modifier=modifier.name)

        def set_bind_modifiers(modifiers: Iterable[bpy.types.Modifier], bind: bool):
            for modifier in modifiers:
                set_bind_modifier(modifier, bind)

        cloth_corrective_smooth_modifier = cloth_mesh_editor.find_corrective_smooth_modifier()
        target_mesh_modifiers: List[bpy.types.SurfaceDeformModifier] = [
            m
            for o in bpy.data.objects
            for m in o.modifiers
            if m.type == 'SURFACE_DEFORM' and m.target == cloth_mesh_object
        ]

        if cloth_corrective_smooth_modifier is not None:
            if subdivision_level == 0:
                cloth_corrective_smooth_modifier.show_viewport = False
            else:
                cloth_corrective_smooth_modifier.show_viewport = True
                set_bind_modifier(cloth_corrective_smooth_modifier, False)

        set_bind_modifiers(target_mesh_modifiers, False)

        cloth_subsurface_modifier.levels = subdivision_level
        cloth_subsurface_modifier.render_levels = subdivision_level

        set_bind_modifier(cloth_corrective_smooth_modifier, True)
        set_bind_modifiers(target_mesh_modifiers, True)

    subdivision_levels: bpy.props.IntProperty(
        name=_('Subdivision Levels'), min=0, soft_max=2, max=6,
        get=lambda p: getattr(MeshEditor(p.id_data).find_subsurface_modifier(name='physics_cloth_subsurface'), 'levels', 0),
        set=_set_subdivision_levels.__func__,
    )

    def physics_equals(self, obj):
        return (
            isinstance(obj, ClothAdjusterSettingsPropertyGroup)
            and self.presets == obj.presets
            and self.mass == obj.mass
            and self.stiffness == obj.stiffness
            and self.damping == obj.damping
            and self.collision_quality == obj.collision_quality
            and self.distance_min == obj.distance_min
            and self.impulse_clamp == obj.impulse_clamp
        )

    def cache_equals(self, obj):
        return (
            isinstance(obj, ClothAdjusterSettingsPropertyGroup)
            and self.frame_start == obj.frame_start
            and self.frame_end == obj.frame_end
        )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_uuunyaa_tools_cloth_settings = bpy.props.PointerProperty(type=ClothAdjusterSettingsPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_uuunyaa_tools_cloth_settings
