# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import math
import random
from typing import Iterable, List, Tuple

import bpy
import bpy_extras
from mathutils import Quaternion, Vector
from ..m17n import _


def create_skin_hair(  # pylint: disable=too-many-arguments
    width: float,
    height: float,
    max_bend_angle: float,
    length: float,
    length_around_factor: float,
    length_threshold: float,
    number_of_cuts: int,
    pitch: float,
    fluctuation_factor: float,
    thickness: float,
    segments: int,
) -> Tuple[List[Vector], List[Tuple[int, int, int, int]]]:
    # pylint: disable=too-many-locals
    vertices: List[Vector] = []
    faces: List[Tuple[int, int, int, int]] = []

    def sprout(position: Vector, length: float, number_of_cuts: int):
        quaternion = Quaternion()
        vertices.extend(calc_edge_vertices(position, quaternion, thickness, 0))

        for cut_count in range(1, number_of_cuts+1):
            theta = random.random() * math.pi * 2
            quaternion @= Quaternion(  # pylint: disable=too-many-function-args
                [math.cos(theta), 0, math.sin(theta)],
                random.random() * max_bend_angle
            )

            cut_radius = thickness * (1 - cut_count / number_of_cuts)
            cut_length = length / number_of_cuts

            vertices.extend(calc_edge_vertices(position, quaternion, cut_radius, cut_length))
            vertex_count = len(vertices)

            faces.extend([
                (v1, v2, v4, v3)
                for (v1, v2), (v3, v4)
                in zip(
                    sliding(range(vertex_count-2*segments, vertex_count-1*segments)),
                    sliding(range(vertex_count-1*segments, vertex_count-0*segments))
                )
            ])

            position += quaternion @ Vector([0, length / number_of_cuts, 0])

    def sliding(target: List[int]) -> Iterable[Tuple[int, int]]:
        for i in range(len(target)-1):
            yield (target[i], target[i+1])

        yield (target[-1], target[0])

    segment_cos = [math.cos(i * math.pi * 2 / segments) for i in range(segments)]
    segment_sin = [math.sin(i * math.pi * 2 / segments) for i in range(segments)]

    def calc_edge_vertices(origin: Vector, rotation: Quaternion, radius: float, length: float) -> List[Vector]:
        return [
            origin + rotation @ Vector([radius * segment_cos[i], length, radius * segment_sin[i]])
            for i in range(segments)
        ]

    def frange(start: float, stop: float, step: float = 1.0) -> Iterable[float]:
        if step == 0:
            return

        value = start
        count: int = 0
        while value < stop:
            value = float(start + count * step)
            yield value
            count += 1

    fluctuation = pitch * fluctuation_factor
    min_number_of_cuts = min(number_of_cuts, 2)

    for xpos in frange(-width/2, +width/2, pitch):
        xpos_factor = 1-(2*xpos/width)**2 * (1-length_around_factor)
        for zpos in frange(-height/2, +height/2, pitch):
            zpos_factor = 1-(2*zpos/height)**2 * (1-length_around_factor)

            target_length = length * xpos_factor * zpos_factor
            if target_length < length_threshold:
                continue

            target_number_of_cuts = max(min_number_of_cuts, math.ceil(number_of_cuts * target_length / length))

            theta = random.random() * math.pi * 2
            band = random.random() * fluctuation

            sprout(
                Vector([
                    xpos + band * math.cos(theta),
                    0,
                    zpos + band * math.sin(theta)
                ]),
                target_length,
                target_number_of_cuts
            )
    return vertices, faces


class AddSkinHairMesh(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.add_skin_hair_mesh'
    bl_label = _('Add Skin Hair Mesh')
    bl_description = _('Construct a skin hair mesh')
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(default=0.006, min=0.0, precision=4, unit='LENGTH')
    height: bpy.props.FloatProperty(default=0.025, min=0.0, precision=4, unit='LENGTH')
    pitch: bpy.props.FloatProperty(default=0.001, min=0.0, precision=5, unit='LENGTH')
    length: bpy.props.FloatProperty(default=0.04, min=0.0, precision=2, unit='LENGTH')
    max_bend_angle: bpy.props.FloatProperty(default=math.pi / 4, min=-math.pi, max=+math.pi, unit='ROTATION')
    number_of_cuts: bpy.props.IntProperty(default=20, min=1)
    fluctuation_factor: bpy.props.FloatProperty(default=0.5, min=0.0, precision=1)
    length_around_factor: bpy.props.FloatProperty(default=1.0, min=0.0, precision=2)
    length_threshold: bpy.props.FloatProperty(default=0.001, min=0.0, precision=3, unit='LENGTH')
    thickness: bpy.props.FloatProperty(default=0.00004, min=0.0, precision=5, unit='LENGTH')
    segments: bpy.props.IntProperty(default=3, min=3)

    align: bpy.props.EnumProperty(
        name=_('Align'),
        items=(
            ('WORLD', _('World'), _('Align the new object to the world')),
            ('VIEW', _('View'), _('Align the new object to the view')),
            ('CURSOR', _('3D Cursor'), _('Use the 3D cursor orientation for the new object')),
        ),
        default='WORLD',
        update=lambda p, _: p.rotation.zero() if p.align == 'WORLD' else None,
    )

    location: bpy.props.FloatVectorProperty(
        name=_('Location'),
        subtype='TRANSLATION',
    )
    rotation: bpy.props.FloatVectorProperty(
        name=_('Rotation'),
        subtype='EULER',
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context: bpy.types.Context):
        verts, faces = create_skin_hair(
            self.width,
            self.height,
            self.max_bend_angle,
            self.length,
            self.length_around_factor,
            self.length_threshold,
            self.number_of_cuts,
            self.pitch,
            self.fluctuation_factor,
            self.thickness,
            self.segments,
        )
        mesh = bpy.data.meshes.new('Skin Hair')
        mesh.from_pydata(verts, [], faces)
        bpy_extras.object_utils.object_data_add(context, mesh, operator=self)

        return {'FINISHED'}


class UuuNyaaMeshExtrasMenu(bpy.types.Menu):
    bl_idname = 'VIEW3D_MT_uuunyaa_mesh_extras'
    bl_label = _('UuuNyaa')

    def draw(self, _context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator(AddSkinHairMesh.bl_idname, text=_('Skin Hair'))

    @staticmethod
    def draw_menu(this, _context):
        this.layout.menu(UuuNyaaMeshExtrasMenu.bl_idname, text=_('UuuNyaa Extras'))

    @staticmethod
    def register():
        bpy.types.VIEW3D_MT_mesh_add.append(UuuNyaaMeshExtrasMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.VIEW3D_MT_mesh_add.remove(UuuNyaaMeshExtrasMenu.draw_menu)
