# -*- coding: utf-8 -*-
# Copyright 2022 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Dict, List, Optional, Tuple

import bpy
import mathutils
from mathutils import Matrix, Vector
from ...m17n import _


class StretchBoneToVertexOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.stretch_bone_to_vertex'
    bl_label = _('Stretch Bone to Vertex')
    bl_options = {'REGISTER', 'UNDO'}

    distance_threshold: bpy.props.FloatProperty(default=0.001, min=0, precision=4, subtype='DISTANCE')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'POSE':
            return False

        if len(context.selected_pose_bones) == 0:
            # At least one bone must be selected.
            return False

        for obj in context.selected_objects:
            # At least one mesh must be selected.
            if obj.type == 'MESH':
                return True

        return False

    def execute(self, context: bpy.types.Context):
        target_pose_bones: List[bpy.types.PoseBone] = list(context.selected_pose_bones)
        target_mesh_objects: List[bpy.types.Object] = [o for o in context.selected_objects if o.type == 'MESH' and not o.hide]

        i2vm: Dict[int, Tuple[bpy.types.MeshVertex, bpy.types.Object]] = dict(enumerate((v, m) for m in target_mesh_objects for v in m.data.vertices))

        mesh_object: Optional[bpy.types.Object] = None
        mesh_matrix: Matrix = Matrix()
        vertex_index = mathutils.kdtree.KDTree(len(i2vm))
        for i, (v, m) in i2vm.items():
            if m != mesh_object:
                mesh_object = m
                mesh_matrix = m.matrix_world

            vertex_index.insert(mesh_matrix @ v.co, i)
        vertex_index.balance()

        distance_threshold: float = self.distance_threshold

        def clear_and_new_constraint(constraints: bpy.types.PoseBoneConstraints, type_name: str):
            c: bpy.types.Constraint
            for c in constraints:
                if c.type != type_name:
                    continue
                pose_bone.constraints.remove(c)
            return constraints.new(type=type_name)

        def set_vertex_group(co: Vector, name: str) -> Tuple[Optional[bpy.types.MeshVertex], Optional[bpy.types.Object]]:
            _co, index, distance = vertex_index.find(co)
            if distance > distance_threshold:
                return None, None

            vertex, mesh_object = i2vm[index]
            vertex_group: bpy.types.VertexGroup = (
                mesh_object.vertex_groups[name] if name in mesh_object.vertex_groups else
                mesh_object.vertex_groups.new(name=name)
            )
            vertex_group.add([vertex.index], 1.0, 'REPLACE')
            return vertex, mesh_object

        for pose_bone in target_pose_bones:
            _vertex, mesh_object = set_vertex_group(pose_bone.tail, pose_bone.name)
            if mesh_object is None:
                continue

            con: bpy.types.StretchToConstraint = clear_and_new_constraint(pose_bone.constraints, 'STRETCH_TO')
            con.target = mesh_object
            con.subtarget = pose_bone.name
            con.rest_length = pose_bone.length

        return {'FINISHED'}
