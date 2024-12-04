# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import bpy
from ...editors.meshes import MeshEditor
from ...m17n import _
from ...tuners import TunerABC, TunerRegistry


class UuuNyaaDynamicPaintAdjuster(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_pyramid_dynamic_paint_adjuster'
    bl_label = _('UuuNyaa Dynamic Paint Adjuster')
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return MeshEditor(context.active_object).find_dynamic_paint_modifier() is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mesh_object: bpy.types.Object = context.active_object
        dynamic_paint_settings = mesh_object.mmd_uuunyaa_tools_dynamic_paint_settings

        box = layout.box()
        col = box.column()
        col.prop(dynamic_paint_settings, 'presets')

        modifier = MeshEditor(context.active_object).find_dynamic_paint_modifier()
        if modifier.ui_type != 'CANVAS':
            return

        if modifier.canvas_settings is None:
            return

        col = layout.column()
        col.prop(dynamic_paint_settings, 'active_surface', text=_('Cache'))

        active_surface_index = modifier.canvas_settings.canvas_surfaces.find(dynamic_paint_settings.active_surface)
        if active_surface_index == -1:
            return

        active_surface = modifier.canvas_settings.canvas_surfaces[active_surface_index]

        row = col.row(align=True)
        row.prop(active_surface, 'frame_start', text=_('Simulation Start'))
        row.prop(active_surface, 'frame_end', text=_('Simulation End'))


class DynamicPaintTunerABC(TunerABC, MeshEditor):
    pass


class NothingDynamicPaintTuner(DynamicPaintTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_DYNAMIC_PAINT_NOTHING'

    @classmethod
    def get_name(cls) -> str:
        return _('Nothing')

    def execute(self):
        pass


class CanvasSkinPressDynamicPaintTuner(DynamicPaintTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_DYNAMIC_PAINT_CANVAS_SKIN_PRESS'

    @classmethod
    def get_name(cls) -> str:
        return _('Canvas Skin Press')

    SKIN_PRESS_SURFACE_NAME = 'Skin Press Surface'

    def execute(self):
        modifier = self.find_dynamic_paint_modifier()

        canvas_surface: bpy.types.DynamicPaintSurface
        if modifier.canvas_settings is None:
            bpy.ops.dpaint.type_toggle(type='CANVAS')
            canvas_surface = modifier.canvas_settings.canvas_surfaces.active

        else:
            canvas_surface_index = modifier.canvas_settings.canvas_surfaces.find(self.SKIN_PRESS_SURFACE_NAME)
            if canvas_surface_index >= 0:
                canvas_surface = modifier.canvas_settings.canvas_surfaces[canvas_surface_index]
            else:
                bpy.ops.dpaint.surface_slot_add()
                canvas_surface = modifier.canvas_settings.canvas_surfaces.active

        modifier.ui_type = 'CANVAS'
        canvas_surface.name = self.SKIN_PRESS_SURFACE_NAME
        canvas_surface.surface_type = 'DISPLACE'
        canvas_surface.brush_radius_scale = 3.0
        canvas_surface.use_dissolve = True
        canvas_surface.dissolve_speed = 1


class BrushDefaultDynamicPaintTuner(DynamicPaintTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return 'PHYSICS_DYNAMIC_PAINT_BRUSH_DEFAULT'

    @classmethod
    def get_name(cls) -> str:
        return _('Brush Default')

    def execute(self):
        modifier = self.find_dynamic_paint_modifier()

        if modifier.brush_settings is None:
            bpy.ops.dpaint.type_toggle(type='BRUSH')

        modifier.ui_type = 'BRUSH'


TUNERS = TunerRegistry(
    (0, NothingDynamicPaintTuner),
    (1, CanvasSkinPressDynamicPaintTuner),
    (2, BrushDefaultDynamicPaintTuner),
)


class DynamicPaintAdjusterSettingsPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def _update_presets(prop, _):
        TUNERS[prop.presets](prop.id_data).execute()

    @staticmethod
    def _surface_items(prop, _context):
        modifier = MeshEditor(prop.id_data).find_dynamic_paint_modifier()
        if modifier is None:
            return []

        if modifier.ui_type != 'CANVAS':
            return []

        surface_type2icon = {
            'PAINT': 'TPAINT_HLT',
            'DISPLACE': 'MOD_DISPLACE',
            'WEIGHT': 'MOD_VERTEX_WEIGHT',
            'WAVE': 'MOD_WAVE',
        }

        return [
            (s.name, s.name, '', surface_type2icon.get(s.surface_type, 'QUESTION'), i)
            for i, s in enumerate(modifier.canvas_settings.canvas_surfaces)
        ]

    @staticmethod
    def _get_active_surface(prop):
        modifier = MeshEditor(prop.id_data).find_dynamic_paint_modifier()
        if modifier is None:
            return 0

        if modifier.ui_type != 'CANVAS':
            return 0

        return modifier.canvas_settings.canvas_surfaces.active_index

    @staticmethod
    def _set_active_surface(prop, index):
        modifier = MeshEditor(prop.id_data).find_dynamic_paint_modifier()
        if modifier is None:
            return

        if modifier.ui_type != 'CANVAS':
            return

        modifier.canvas_settings.canvas_surfaces.active_index = index

    presets: bpy.props.EnumProperty(
        name=_('Presets'),
        items=TUNERS.to_enum_property_items(),
        update=_update_presets.__func__,
        default=None
    )

    active_surface: bpy.props.EnumProperty(
        name=_('Active Surface'),
        items=_surface_items.__func__,
        get=_get_active_surface.__func__,
        set=_set_active_surface.__func__,
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_uuunyaa_tools_dynamic_paint_settings = bpy.props.PointerProperty(type=DynamicPaintAdjusterSettingsPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_uuunyaa_tools_dynamic_paint_settings
