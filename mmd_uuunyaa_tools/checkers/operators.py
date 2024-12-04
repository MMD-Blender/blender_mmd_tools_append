# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set, Tuple

import bpy
from ..m17n import _, iface_


class CheckResultStatus(Enum):
    GOOD = _('Good')
    AVERAGE = _('Average')
    WARNING = _('Warning')
    POOR = _('Poor')
    BAD = _('Bad')
    UNKNOWN = _('Unknown')


def status_to_icon(status: CheckResultStatus) -> str:
    if status is CheckResultStatus.GOOD:
        return 'COLORSET_03_VEC'
    if status is CheckResultStatus.AVERAGE:
        return 'COLORSET_04_VEC'
    if status is CheckResultStatus.WARNING:
        return 'COLORSET_09_VEC'
    if status is CheckResultStatus.POOR:
        return 'COLORSET_02_VEC'
    if status is CheckResultStatus.BAD:
        return 'COLORSET_01_VEC'

    # UNKNOWN
    return 'COLORSET_13_VEC'


def impact_to_status(impact: float) -> CheckResultStatus:
    if impact < 0:
        return CheckResultStatus.GOOD
    if impact < 4:
        return CheckResultStatus.AVERAGE
    if impact < 16:
        return CheckResultStatus.WARNING
    if impact < 32:
        return CheckResultStatus.POOR

    return CheckResultStatus.BAD


@dataclass
class CheckResult:
    name: str
    status: CheckResultStatus
    impact: float
    data_path: str
    message: Optional[str]
    indent: int = 0
    editable: bool = True

    @property
    def icon(self) -> str:
        return status_to_icon(self.status)


class CheckEeveeRenderingPerformance(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.check_eevee_rendering_performance'
    bl_label = _('Check Eevee Rendering Performance')
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False
        return True

    @staticmethod
    def check_blender_version(_context: bpy.types.Context):
        return CheckResult(
            _('Blender Version'),
            CheckResultStatus.GOOD if bpy.app.version >= (2, 93, 0) else CheckResultStatus.BAD,
            0,
            bpy.app.version_string,
            _('>= 2.93 LTS is Good'),
            editable=False,
        )

    @staticmethod
    def check_render_engine(context: bpy.types.Context):
        return CheckResult(
            _('Render Engine'),
            CheckResultStatus.GOOD if context.scene.render.engine == 'BLENDER_EEVEE' else CheckResultStatus.BAD,
            0,
            'scene.render.engine',
            _('= Eevee is Good'),
        )

    @staticmethod
    def sample_to_status(samples: int) -> CheckResultStatus:
        if samples > 512:
            return CheckResultStatus.BAD
        if samples > 128:
            return CheckResultStatus.POOR
        if samples > 32:
            return CheckResultStatus.WARNING
        if samples > 16:
            return CheckResultStatus.AVERAGE
        return CheckResultStatus.GOOD

    @classmethod
    def check_taa_render_samples(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Render Samples'),
            cls.sample_to_status(context.scene.eevee.taa_render_samples),
            0.0141 * context.scene.eevee.taa_render_samples + -0.439,
            'scene.eevee.taa_render_samples',
            _('<= 16 is Good'),
            1
        )

    @classmethod
    def check_taa_samples(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Viewport Samples'),
            cls.sample_to_status(context.scene.eevee.taa_samples),
            0,
            'scene.eevee.taa_samples',
            _('<= 16 is Good'),
            1
        )

    @classmethod
    def check_use_gtao(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Ambient Occlusion'),
            CheckResultStatus.AVERAGE if context.scene.eevee.use_gtao else CheckResultStatus.GOOD,
            0 if context.scene.eevee.use_gtao else -3.9,
            'scene.eevee.use_gtao',
            _('= False is Good'),
        )

    @classmethod
    def check_use_bloom(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Bloom'),
            CheckResultStatus.AVERAGE if context.scene.eevee.use_bloom else CheckResultStatus.GOOD,
            0 if context.scene.eevee.use_bloom else -2.9,
            'scene.eevee.use_bloom',
            _('= False is Good'),
        )

    @classmethod
    def check_use_motion_blur(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Motion Blur'),
            CheckResultStatus.AVERAGE if context.scene.eevee.use_motion_blur else CheckResultStatus.GOOD,
            0 if context.scene.eevee.use_motion_blur else -3.4,
            'scene.eevee.use_motion_blur',
            _('= False is Good'),
        )

    @classmethod
    def check_bokeh_max_size(cls, context: bpy.types.Context) -> CheckResult:
        status = CheckResultStatus.UNKNOWN
        if context.scene.eevee.bokeh_max_size > 256:
            status = CheckResultStatus.BAD
        elif context.scene.eevee.bokeh_max_size > 128:
            status = CheckResultStatus.POOR
        elif context.scene.eevee.bokeh_max_size > 32:
            status = CheckResultStatus.WARNING
        elif context.scene.eevee.bokeh_max_size > 16:
            status = CheckResultStatus.AVERAGE
        else:
            status = CheckResultStatus.GOOD

        return CheckResult(
            _('Depth of Field Max Size'),
            status,
            -0.0163 + 4.85E-03 * (math.log(context.scene.eevee.bokeh_max_size) if context.scene.eevee.bokeh_max_size != 0 else 0),
            'scene.eevee.bokeh_max_size',
            _('<= 16 is Good'),
        )

    @classmethod
    def check_sss_samples(cls, context: bpy.types.Context) -> CheckResult:
        status = CheckResultStatus.UNKNOWN
        if context.scene.eevee.sss_samples == 32:
            status = CheckResultStatus.BAD
        elif context.scene.eevee.sss_samples > 16:
            status = CheckResultStatus.POOR
        elif context.scene.eevee.sss_samples > 8:
            status = CheckResultStatus.WARNING
        elif context.scene.eevee.sss_samples > 4:
            status = CheckResultStatus.AVERAGE
        else:
            status = CheckResultStatus.GOOD

        return CheckResult(
            _('Subsurface Scattering Samples'),
            status,
            -8.22E-04 + 1.7E-04 * context.scene.eevee.sss_samples + 8.29E-06 * math.pow(context.scene.eevee.sss_samples, 2),
            'scene.eevee.sss_samples',
            _('<= 4 is Good'),
        )

    @classmethod
    def check_use_ssr(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Screen Space Refraction'),
            CheckResultStatus.WARNING if context.scene.eevee.use_ssr else CheckResultStatus.GOOD,
            0 if context.scene.eevee.use_ssr else -11.4,
            'scene.eevee.use_ssr',
            _('= False is Good'),
        )

    @classmethod
    def check_use_ssr_halfres(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Half Res Trace'),
            CheckResultStatus.AVERAGE if not context.scene.eevee.use_ssr_halfres else CheckResultStatus.GOOD,
            -2.2 if context.scene.eevee.use_ssr_halfres else 0,
            'scene.eevee.use_ssr_halfres',
            _('= True is Good'),
            1
        )

    @classmethod
    def check_use_compositing(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Compositing'),
            CheckResultStatus.WARNING if context.scene.render.use_compositing else CheckResultStatus.GOOD,
            -(0.6-1.7) if context.scene.render.use_compositing else 0,
            'scene.render.use_compositing',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_cryptomatte_object(cls, context: bpy.types.Context) -> Optional[CheckResult]:
        if not hasattr(context.view_layer, 'use_pass_cryptomatte_object'):
            return None

        return CheckResult(
            _('Pass Cryptomatte Object'),
            CheckResultStatus.BAD if context.view_layer.use_pass_cryptomatte_object else CheckResultStatus.GOOD,
            -(-0.7-121.6) if context.view_layer.use_pass_cryptomatte_object else 0,
            'view_layer.use_pass_cryptomatte_object',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_cryptomatte_material(cls, context: bpy.types.Context) -> Optional[CheckResult]:
        if not hasattr(context.view_layer, 'use_pass_cryptomatte_material'):
            return None

        return CheckResult(
            _('Pass Cryptomatte Material'),
            CheckResultStatus.BAD if context.view_layer.use_pass_cryptomatte_material else CheckResultStatus.GOOD,
            -(-0.9-121.7) if context.view_layer.use_pass_cryptomatte_material else 0,
            'view_layer.use_pass_cryptomatte_material',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_cryptomatte_asset(cls, context: bpy.types.Context) -> Optional[CheckResult]:
        if not hasattr(context.view_layer, 'use_pass_cryptomatte_asset'):
            return None

        return CheckResult(
            _('Pass Cryptomatte Asset'),
            CheckResultStatus.BAD if context.view_layer.use_pass_cryptomatte_asset else CheckResultStatus.GOOD,
            -(-1.2-120.6) if context.view_layer.use_pass_cryptomatte_asset else 0,
            'view_layer.use_pass_cryptomatte_asset',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_glossy_direct(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Glossy Light'),
            CheckResultStatus.POOR if context.view_layer.use_pass_glossy_direct else CheckResultStatus.GOOD,
            -(-0.7-31.8) if context.view_layer.use_pass_glossy_direct else 0,
            'view_layer.use_pass_glossy_direct',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_diffuse_direct(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Diffuse Light'),
            CheckResultStatus.POOR if context.view_layer.use_pass_diffuse_direct else CheckResultStatus.GOOD,
            -(-0.7-26.8) if context.view_layer.use_pass_diffuse_direct else 0,
            'view_layer.use_pass_diffuse_direct',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_emit(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Emit'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_emit else CheckResultStatus.GOOD,
            -(-0.6-14.3) if context.view_layer.use_pass_emit else 0,
            'view_layer.use_pass_emit',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_glossy_color(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Glossy Color'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_glossy_color else CheckResultStatus.GOOD,
            -(-0.5-14.1) if context.view_layer.use_pass_glossy_color else 0,
            'view_layer.use_pass_glossy_color',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_diffuse_color(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Diffuse Color'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_diffuse_color else CheckResultStatus.GOOD,
            -(-0.7-14.5) if context.view_layer.use_pass_diffuse_color else 0,
            'view_layer.use_pass_diffuse_color',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_shadow(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Shadow'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_shadow else CheckResultStatus.GOOD,
            -(-0.4-8.6) if context.view_layer.use_pass_shadow else 0,
            'view_layer.use_pass_shadow',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_ambient_occlusion(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Ambient Occlusion'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_ambient_occlusion else CheckResultStatus.GOOD,
            -(-0.3-6.4) if context.view_layer.use_pass_ambient_occlusion else 0,
            'view_layer.use_pass_ambient_occlusion',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_normal(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Normal'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_normal else CheckResultStatus.GOOD,
            -(-0.6-4.4) if context.view_layer.use_pass_normal else 0,
            'view_layer.use_pass_normal',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_bloom(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Bloom'),
            CheckResultStatus.WARNING if context.view_layer.eevee.use_pass_bloom else CheckResultStatus.GOOD,
            -(-0.8-2.6) if context.view_layer.eevee.use_pass_bloom else 0,
            'view_layer.eevee.use_pass_bloom',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_volume_direct(cls, context: bpy.types.Context) -> Optional[CheckResult]:
        if not hasattr(context.view_layer.eevee, 'use_pass_volume_direct'):
            return None

        return CheckResult(
            _('Pass Volume Light'),
            CheckResultStatus.WARNING if context.view_layer.eevee.use_pass_volume_direct else CheckResultStatus.GOOD,
            -(-0.7-2.9) if context.view_layer.eevee.use_pass_volume_direct else 0,
            'view_layer.eevee.use_pass_volume_direct',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_z(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Z'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_z else CheckResultStatus.GOOD,
            -(-0.2-1.6) if context.view_layer.use_pass_z else 0,
            'view_layer.use_pass_z',
            _('= False is Good'),
        )

    @classmethod
    def check_use_pass_environment(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Pass Environment'),
            CheckResultStatus.WARNING if context.view_layer.use_pass_environment else CheckResultStatus.GOOD,
            -(-0.6-2.3) if context.view_layer.use_pass_environment else 0,
            'view_layer.use_pass_environment',
            _('= False is Good'),
        )

    @classmethod
    def check_use_sequencer(cls, context: bpy.types.Context) -> CheckResult:
        return CheckResult(
            _('Use Sequencer'),
            CheckResultStatus.WARNING if context.scene.render.use_sequencer else CheckResultStatus.GOOD,
            0,
            'scene.render.use_sequencer',
            _('= False is Good'),
        )

    @classmethod
    def check_file_format(cls, context: bpy.types.Context) -> CheckResult:
        format_to_status = {
            'BMP': (CheckResultStatus.WARNING, 14.14 / 5.54 - 1),
            'IRIS': (CheckResultStatus.AVERAGE, 8.64 / 5.54 - 1),
            'PNG': (CheckResultStatus.WARNING, 22.88 / 5.54 - 1),
            'JPEG': (CheckResultStatus.AVERAGE, 5.54 / 5.54 - 1),
            'JPEG2000': (CheckResultStatus.BAD, 38.79 / 5.54 - 1),
            'TARGA': (CheckResultStatus.WARNING, 12.66 / 5.54 - 1),
            'TARGA_RAW': (CheckResultStatus.WARNING, 14.14 / 5.54 - 1),
            'CINEON': (CheckResultStatus.AVERAGE, 9.85 / 5.54 - 1),
            'DPX': (CheckResultStatus.AVERAGE, 8.47 / 5.54 - 1),
            'OPEN_EXR_MULTILAYER': (CheckResultStatus.GOOD, 5.63 / 5.54 - 1),
            'OPEN_EXR': (CheckResultStatus.GOOD, 5.35 / 5.54 - 1),
            'HDR': (CheckResultStatus.AVERAGE, 9.52 / 5.54 - 1),
            'TIFF': (CheckResultStatus.BAD, 37.62 / 5.54 - 1),
            'AVI_JPEG': (CheckResultStatus.AVERAGE, 5.66 / 5.54 - 1),
            'AVI_RAW': (CheckResultStatus.AVERAGE, 5.70 / 5.54 - 1),
            'FFMPEG': (CheckResultStatus.GOOD, 5.61 / 5.54 - 1),
        }

        status, impact = format_to_status[context.scene.render.image_settings.file_format]
        return CheckResult(_('File Format'), status, impact, 'scene.render.image_settings.file_format', _('= JPEG is Good'))

    @staticmethod
    def resolve_data_path(context: bpy.types.Object, data_path: str) -> Tuple[bpy.types.Object, str]:
        path_fragments = data_path.split('.')
        if len(path_fragments) < 2:
            return (context, data_path)

        for path_fragment in path_fragments[:-1]:
            context = getattr(context, path_fragment)

        return (context, path_fragments[-1])

    @classmethod
    def check_meshes_use_auto_smooth(cls, context: bpy.types.Context) -> CheckResult:
        mesh_count = 0
        use_auto_smooth_mesh_count = 0

        obj: bpy.types.Object
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue

            if obj.hide_render:
                continue

            mesh: bpy.types.Mesh = obj.data

            mesh_count += 1

            if not mesh.use_auto_smooth:
                continue

            use_auto_smooth_mesh_count += 1

        return CheckResult(
            _('Meshes Use Auto Smooth'),
            CheckResultStatus.GOOD if use_auto_smooth_mesh_count == 0 else CheckResultStatus.WARNING,
            min(use_auto_smooth_mesh_count * 0.7, 3),
            f'{use_auto_smooth_mesh_count} / {mesh_count}',
            _('= 0 is Good'),
            editable=False
        )

    @classmethod
    def check_materials_method(cls, context: bpy.types.Context) -> CheckResult:
        active_materials: Set[bpy.types.Material] = set()

        obj: bpy.types.Object
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue

            if obj.hide_render:
                continue

            material_slot: bpy.types.MaterialSlot
            for material_slot in obj.material_slots:
                if material_slot.material is None:
                    continue
                active_materials.add(material_slot.material)

        material_count = len(active_materials)
        alpha_hashed_material_count = 0

        for material in active_materials:
            if material.blend_method != 'HASHED' and material.shadow_method != 'HASHED':
                continue
            alpha_hashed_material_count += 1

        return CheckResult(
            _('Materials Use Alpha Hashed'),
            CheckResultStatus.GOOD if alpha_hashed_material_count == 0 else CheckResultStatus.WARNING,
            min(alpha_hashed_material_count * 0.4, 2),
            f'{alpha_hashed_material_count} / {material_count}',
            _('= 0 is Good'),
            editable=False
        )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout
        layout.label(text=_('Eevee Rendering Performance Checker'), icon='MOD_TIME')

        results = list(filter(lambda e: e is not None, [
            self.check_blender_version(context),
            self.check_render_engine(context),

            self.check_taa_render_samples(context),
            self.check_taa_samples(context),

            self.check_use_gtao(context),
            self.check_use_bloom(context),
            self.check_bokeh_max_size(context),
            self.check_sss_samples(context),
            self.check_use_ssr(context),
            self.check_use_ssr_halfres(context),
            self.check_use_motion_blur(context),

            self.check_file_format(context),

            self.check_use_compositing(context),
            self.check_use_sequencer(context),

            self.check_use_pass_z(context),
            self.check_use_pass_normal(context),

            self.check_use_pass_diffuse_direct(context),
            self.check_use_pass_diffuse_color(context),
            self.check_use_pass_glossy_direct(context),
            self.check_use_pass_glossy_color(context),
            self.check_use_pass_volume_direct(context),
            self.check_use_pass_emit(context),
            self.check_use_pass_environment(context),
            self.check_use_pass_shadow(context),
            self.check_use_pass_ambient_occlusion(context),
            self.check_use_pass_bloom(context),

            self.check_use_pass_cryptomatte_object(context),
            self.check_use_pass_cryptomatte_material(context),
            self.check_use_pass_cryptomatte_asset(context),

            self.check_meshes_use_auto_smooth(context),
            self.check_materials_method(context),
        ]))

        total_impact: float = 0.0
        for result in results:
            total_impact += result.impact

        total_status = CheckResultStatus.UNKNOWN
        if total_impact > 100.0:
            total_status = CheckResultStatus.BAD
        elif total_impact > 25.0:
            total_status = CheckResultStatus.POOR
        elif total_impact > 6.25:
            total_status = CheckResultStatus.WARNING
        elif total_impact > 0.0:
            total_status = CheckResultStatus.AVERAGE
        else:
            total_status = CheckResultStatus.GOOD

        total_result = CheckResult(_('Total Performance Impact'), total_status, total_impact, f'{total_impact:+.2f}%', _('<= 0% is Good'), editable=False)

        def draw_check_result(layout: bpy.types.UILayout, result: CheckResult):
            row = layout.column().split(factor=0.1, align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{result.impact:+.2f}%')

            if result.indent > 0:
                row = row.split(factor=result.indent * 0.01, align=True)
                row.label(text='')

            row = row.split(factor=0.15, align=True)
            row.label(text=result.status.value, text_ctxt='Status', icon=result.icon)
            row = row.split(factor=0.75, align=True)
            if result.editable:
                data, property_name = self.resolve_data_path(context, result.data_path)
                row.prop(data, property_name, text=result.name)
            else:
                row.label(text='{}: {}'.format(iface_(result.name), result.data_path))

            row.label(text=result.message)

        draw_check_result(layout, total_result)
        col = layout.column(align=True)
        for result in results:
            draw_check_result(col, result)

        col = layout.column(align=True)
        col.label(text=_('Object with Impact Selection:'), icon='RESTRICT_SELECT_OFF')
        col.operator(SelectMeshObjectsWithUseAutoSmooth.bl_idname, icon='MESH_DATA')
        col.operator(SelectMeshObjectsWithSlowMaterial.bl_idname, icon='MATERIAL')

    # results: List[CheckResult] = []

    def invoke(self, context: bpy.types.Context, _event):
        return context.window_manager.invoke_popup(self, width=600)

    def execute(self, _context):
        return {'FINISHED'}


class SelectMeshObjectsWithUseAutoSmooth(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_mesh_objects_with_use_auto_smooth'
    bl_label = _('Select Mesh Objects with Use Auto Smooth')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj: bpy.types.Object
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue

            if obj.hide_render:
                continue

            mesh: bpy.types.Mesh = obj.data
            if not mesh.use_auto_smooth:
                continue

            obj.select_set(True)

        return {'FINISHED'}


class SelectMeshObjectsWithSlowMaterial(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.select_mesh_objects_with_slow_material'
    bl_label = _('Select Mesh Objects with Use Alpha Hashed')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj: bpy.types.Object
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue

            if obj.hide_render:
                continue

            material_slot: bpy.types.MaterialSlot
            for material_slot in obj.material_slots:
                material = material_slot.material
                if material is None:
                    continue

                if material.blend_method != 'HASHED' and material.shadow_method != 'HASHED':
                    continue

                obj.select_set(True)

        return {'FINISHED'}
