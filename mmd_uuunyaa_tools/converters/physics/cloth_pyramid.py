# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import datetime
import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Set, Tuple

import bmesh
import bpy
import mathutils
import numpy as np
from mathutils import Matrix, Vector
from ...editors.armatures import ArmatureEditor
from ...editors.meshes import MeshEditor
from ...m17n import _
from ...utilities import MessageException


class PyramidVertex(IntEnum):
    STRING = 0
    APEX = 1
    BASE_A = 2
    BASE_B = 3
    BASE_C = 4
    BASE_D = 5


@dataclass
class Target:
    bone_name: str
    parent_bone_name: str
    deform_mesh_object: bpy.types.Object
    vertex_group: bpy.types.VertexGroup
    origin: Vector
    direction: Vector


class PyramidBoneNames:
    base: str
    apex: str
    base_a: str
    base_b: str
    base_c: str
    base_d: str

    def __init__(self, target_bone_name):
        self.base = f'physics_pyramid_base_{target_bone_name}'
        self.apex = f'physics_pyramid_apex_{target_bone_name}'
        self.base_a = f'physics_pyramid_base_a_{target_bone_name}'
        self.base_b = f'physics_pyramid_base_b_{target_bone_name}'
        self.base_c = f'physics_pyramid_base_c_{target_bone_name}'
        self.base_d = f'physics_pyramid_base_d_{target_bone_name}'


class PyramidMeshEditor(MeshEditor):
    PYRAMID_CLOTH_TARGET_BONE_PROPERTY_NAME = 'physics_pyramid_cloth_target_bone'
    PYRAMID_CLOTH_PARENT_BONE_PROPERTY_NAME = 'physics_pyramid_cloth_parent_bone'

    @staticmethod
    def is_pyramid_mesh_object(obj: bpy.types.Object) -> bool:
        return obj.type == 'MESH' and PyramidMeshEditor.PYRAMID_CLOTH_TARGET_BONE_PROPERTY_NAME in obj

    @property
    def target_bone_name(self) -> str:
        return self.mesh_object[self.PYRAMID_CLOTH_TARGET_BONE_PROPERTY_NAME]

    @target_bone_name.setter
    def target_bone_name(self, value: str):
        self.mesh_object[self.PYRAMID_CLOTH_TARGET_BONE_PROPERTY_NAME] = value

    @property
    def parent_bone_name(self) -> str:
        return self.mesh_object[self.PYRAMID_CLOTH_PARENT_BONE_PROPERTY_NAME]

    @parent_bone_name.setter
    def parent_bone_name(self, value: str):
        self.mesh_object[self.PYRAMID_CLOTH_PARENT_BONE_PROPERTY_NAME] = value

    def assign_vertex_groups(self):
        self.edit_vertex_group('string', [([PyramidVertex.STRING], 1.0)])
        self.edit_vertex_group('apex', [([PyramidVertex.APEX], 1.0)])
        self.edit_vertex_group('base_a', [([PyramidVertex.BASE_A], 1.0)])
        self.edit_vertex_group('base_b', [([PyramidVertex.BASE_B], 1.0)])
        self.edit_vertex_group('base_c', [([PyramidVertex.BASE_C], 1.0)])
        self.edit_vertex_group('base_d', [([PyramidVertex.BASE_D], 1.0)])

    def setup_cloth_modifier(self, string_pin_weight: float, apex_pin_weight: float, base_pin_weight: float, time_scale: float) -> bpy.types.ClothModifier:
        cloth_modifier: bpy.types.ClothModifier = self.edit_cloth_modifier(
            'physics_pyramid_cloth',
            vertex_group_mass=self.edit_vertex_group('physics_pyramid_cloth_pin', [
                ([PyramidVertex.STRING], string_pin_weight),  # 0.4 - 0.6
                ([PyramidVertex.APEX], apex_pin_weight),  # 0.4 - 0.6
                ([PyramidVertex.BASE_A, PyramidVertex.BASE_B, PyramidVertex.BASE_C, PyramidVertex.BASE_D], base_pin_weight),  # 0.8 - 1.0
            ]).name,
            time_scale=time_scale,
            bending_model='LINEAR'
        )
        self.mesh_object.mmd_uuunyaa_tools_cloth_settings.presets = 'PHYSICS_CLOTH_BREAST_PYRAMID'
        return cloth_modifier

    def _get_pin_weight(self, vid: int) -> float:
        pin_vertex_group = self.mesh_object.vertex_groups.get('physics_pyramid_cloth_pin')
        if pin_vertex_group is None:
            return 0
        return pin_vertex_group.weight(vid)

    def _set_pin_weight(self, vid: int, weight: float):
        self.edit_vertex_group('physics_pyramid_cloth_pin', [([vid], weight)])

    @property
    def string_pin_weight(self) -> float:
        return self._get_pin_weight(PyramidVertex.STRING)

    @string_pin_weight.setter
    def string_pin_weight(self, value: float):
        self._set_pin_weight(PyramidVertex.STRING, value)

    @property
    def apex_pin_weight(self) -> float:
        return self._get_pin_weight(PyramidVertex.APEX)

    @apex_pin_weight.setter
    def apex_pin_weight(self, value: float):
        self._set_pin_weight(PyramidVertex.APEX, value)

    @property
    def base_pin_weight(self) -> float:
        return self._get_pin_weight(PyramidVertex.BASE_A)

    @base_pin_weight.setter
    def base_pin_weight(self, value: float):
        self._set_pin_weight(PyramidVertex.BASE_A, value)
        self._set_pin_weight(PyramidVertex.BASE_B, value)
        self._set_pin_weight(PyramidVertex.BASE_C, value)
        self._set_pin_weight(PyramidVertex.BASE_D, value)

    @property
    def time_scale(self) -> float:
        cloth_modifier = self.find_cloth_modifier()
        if cloth_modifier is None:
            return 0
        return cloth_modifier.settings.time_scale

    @time_scale.setter
    def time_scale(self, value: float):
        self.edit_cloth_modifier('physics_pyramid_cloth', time_scale=value)


def add_pyramid_mesh_objects(
    breast_bones: List[bpy.types.EditBone],
    mesh_objects: List[bpy.types.Object],
    head_tail: float, string_length_ratio: float, base_area_factor: float, project_vertically: bool
) -> List[bpy.types.Object]:
    targets = to_targets(breast_bones, mesh_objects, head_tail)

    if len(targets) == 0:
        raise MessageException(_('Target bones not found.')) from None

    pyramid_mesh_objects: List[bpy.types.Object] = []

    for target in targets:
        pyramid_mesh_objects.append(build_pyramid_mesh_object(target, string_length_ratio, base_area_factor, project_vertically))

    return pyramid_mesh_objects


def build_pyramid_mesh_object(target: Target, string_length_ratio: float, base_area_factor: float, project_vertically: bool) -> bpy.types.Object:
    deform_bmesh: bmesh.types.BMesh = bmesh.new()

    # pylint: disable=no-member
    depsgraph: bpy.types.Depsgraph = bpy.context.evaluated_depsgraph_get()
    deform_bmesh.from_object(target.deform_mesh_object, depsgraph)

    apex_vertex, base_vertices = to_pyramid_vertices(deform_bmesh, target, base_area_factor, project_vertically)
    vertices: List[Vector] = [
        apex_vertex * string_length_ratio,
        apex_vertex,
        *base_vertices
    ]

    pyramid_mesh = bpy.data.meshes.new(f'physics_pyramid_cloth_{target.bone_name}')
    pyramid_mesh.from_pydata(vertices, [
        [PyramidVertex.STRING, PyramidVertex.APEX]
    ], [
        [PyramidVertex.APEX, PyramidVertex.BASE_A, PyramidVertex.BASE_B],
        [PyramidVertex.APEX, PyramidVertex.BASE_B, PyramidVertex.BASE_C],
        [PyramidVertex.APEX, PyramidVertex.BASE_C, PyramidVertex.BASE_D],
        [PyramidVertex.APEX, PyramidVertex.BASE_D, PyramidVertex.BASE_A],
    ])
    pyramid_mesh.update()

    deform_bmesh.free()

    pyramid_mesh_editor = PyramidMeshEditor(bpy.data.objects.new(f'physics_pyramid_cloth_{target.bone_name}', pyramid_mesh))
    pyramid_mesh_editor.mesh_object.matrix_basis = Matrix.Translation(target.origin)
    pyramid_mesh_editor.mesh_object.hide_render = True
    pyramid_mesh_editor.mesh_object.display_type = 'WIRE'

    pyramid_mesh_editor.target_bone_name = target.bone_name
    pyramid_mesh_editor.parent_bone_name = target.parent_bone_name
    pyramid_mesh_editor.link_to_active_collection()

    return pyramid_mesh_editor.mesh_object


def assign_pyramid_weights(
    pyramid_mesh_objects: List[bpy.types.Object],
    deform_mesh_objects: List[bpy.types.Object],
    boundary_expansion_hop_count: int
):
    for pyramid_mesh_object in pyramid_mesh_objects:
        target_bone_name = PyramidMeshEditor(pyramid_mesh_object).target_bone_name

        pyramid_armature_object = pyramid_mesh_object.parent

        for deform_mesh_object in deform_mesh_objects:
            vertex_group = deform_mesh_object.vertex_groups.get(target_bone_name)
            if vertex_group is None:
                continue

            assign_deform_weights(
                pyramid_armature_object,
                deform_mesh_object,
                target_bone_name,
                boundary_expansion_hop_count
            )


def convert_pyramid_mesh_to_cloth(
    pyramid_mesh_objects: List[bpy.types.Object],
    deform_mesh_objects: List[bpy.types.Object],
    boundary_expansion_hop_count: int
) -> List[Tuple[bpy.types.Object, bpy.types.Object]]:
    pairs: List[Tuple[bpy.types.Object, bpy.types.Object]] = []

    for pyramid_mesh_object in pyramid_mesh_objects:
        pyramid_mesh_editor = PyramidMeshEditor(pyramid_mesh_object)
        target_bone_name = pyramid_mesh_editor.target_bone_name
        parent_bone_name = pyramid_mesh_editor.parent_bone_name

        pyramid_mesh_editor.assign_vertex_groups()
        pyramid_mesh_editor.setup_cloth_modifier(0.8, 0.4, 1.0, 0.5)

        for deform_mesh_object in deform_mesh_objects:
            vertex_group = deform_mesh_object.vertex_groups.get(target_bone_name)
            if vertex_group is None:
                continue

            deform_armature_object = deform_mesh_object.find_armature()
            if deform_mesh_object is None:
                continue

            build_pyramid_bones(
                deform_armature_object,
                pyramid_mesh_object,
                target_bone_name,
                parent_bone_name
            )

            assign_deform_weights(
                deform_armature_object,
                deform_mesh_object,
                target_bone_name,
                boundary_expansion_hop_count
            )

            pairs.append((pyramid_mesh_object, deform_mesh_object))

    return pairs


def build_pyramid_bones(armature_object: bpy.types.Object, pyramid_mesh_object: bpy.types.Object, target_bone_name: str, parent_bone_name: str):
    bone_names = PyramidBoneNames(target_bone_name)
    armature: bpy.types.Armature = armature_object.data

    if bone_names.base in armature.bones:
        # already built
        return

    print(f'build pyramid bones: {target_bone_name}')

    bpy.context.selected_objects.append(armature_object)
    bpy.context.view_layer.objects.active = armature_object

    bpy.ops.object.mode_set(mode='EDIT')

    pyramid_mesh: bpy.types.Mesh = pyramid_mesh_object.data
    vertices: List[Vector] = [v.co for v in pyramid_mesh.vertices]

    origin: Vector = pyramid_mesh_object.location - armature_object.location
    direction: Vector = vertices[PyramidVertex.APEX].normalized()

    bone_length = vertices[PyramidVertex.APEX].length / 7.5
    bone_vector = direction * bone_length

    # Move the apex vertex into the mesh
    pyramid_mesh.vertices[PyramidVertex.APEX].co -= bone_vector
    pyramid_mesh.update()

    def create_bones():
        base_bone = armature.edit_bones.new(bone_names.base)
        base_bone.head = origin
        base_bone.tail = origin + bone_vector
        base_bone.parent = armature.edit_bones[parent_bone_name]

        apex_bone = armature.edit_bones.new(bone_names.apex)
        apex_bone.parent = base_bone
        apex_bone.head = origin + vertices[PyramidVertex.APEX]
        apex_bone.tail = origin + vertices[PyramidVertex.APEX] + bone_vector

        base_a_bone = armature.edit_bones.new(bone_names.base_a)
        base_a_bone.parent = base_bone
        base_a_bone.head = origin + vertices[PyramidVertex.BASE_A]
        base_a_bone.tail = origin + vertices[PyramidVertex.BASE_A] + bone_vector

        base_b_bone = armature.edit_bones.new(bone_names.base_b)
        base_b_bone.parent = base_bone
        base_b_bone.head = origin + vertices[PyramidVertex.BASE_B]
        base_b_bone.tail = origin + vertices[PyramidVertex.BASE_B] + bone_vector

        base_c_bone = armature.edit_bones.new(bone_names.base_c)
        base_c_bone.parent = base_bone
        base_c_bone.head = origin + vertices[PyramidVertex.BASE_C]
        base_c_bone.tail = origin + vertices[PyramidVertex.BASE_C] + bone_vector

        base_d_bone = armature.edit_bones.new(bone_names.base_d)
        base_d_bone.parent = base_bone
        base_d_bone.head = origin + vertices[PyramidVertex.BASE_D]
        base_d_bone.tail = origin + vertices[PyramidVertex.BASE_D] + bone_vector

    create_bones()

    bpy.ops.object.mode_set(mode='OBJECT')

    pyramid_mesh_object.parent = armature_object
    pyramid_mesh_object.parent_type = 'BONE'
    pyramid_mesh_object.parent_bone = bone_names.base
    pyramid_mesh_object.matrix_parent_inverse = armature.bones[bone_names.base].matrix_local.inverted() @ Matrix.Translation(-bone_vector)

    bpy.ops.object.mode_set(mode='POSE')

    armature_editor = ArmatureEditor(armature_object)
    pose_bones = armature_editor.pose_bones
    armature_editor.add_copy_location_constraint(pose_bones[bone_names.apex], pyramid_mesh_object, 'apex', 'WORLD')
    armature_editor.add_copy_location_constraint(pose_bones[bone_names.base_a], pyramid_mesh_object, 'base_a', 'WORLD')
    armature_editor.add_copy_location_constraint(pose_bones[bone_names.base_b], pyramid_mesh_object, 'base_b', 'WORLD')
    armature_editor.add_copy_location_constraint(pose_bones[bone_names.base_c], pyramid_mesh_object, 'base_c', 'WORLD')
    armature_editor.add_copy_location_constraint(pose_bones[bone_names.base_d], pyramid_mesh_object, 'base_d', 'WORLD')

    bones = armature_editor.bones
    bones[bone_names.base].use_deform = False
    bones[target_bone_name].use_deform = False

    bpy.ops.object.mode_set(mode='OBJECT')

def assign_deform_weights(pyramid_armature_object: bpy.types.Object, deform_mesh_object: bpy.types.Object, target_bone_name: str, boundary_expansion_hop_count: int):
    mesh_editor = MeshEditor(deform_mesh_object)
    deform_bmesh: bmesh.types.BMesh = bmesh.new()

    start_time = datetime.datetime.now()

    print(f'assign deform weights:begin: {target_bone_name}')

    # pylint: disable=no-member
    depsgraph: bpy.types.Depsgraph = bpy.context.evaluated_depsgraph_get()
    deform_bmesh.from_object(mesh_editor.mesh_object, depsgraph)
    deform_bmesh.transform(deform_mesh_object.matrix_world)

    vid2weight = expand_boundary(
        to_vid2weight(deform_bmesh, mesh_editor.get_vertex_group(target_bone_name).index),
        deform_bmesh, boundary_expansion_hop_count
    )
    deform_bmesh_verts = deform_bmesh.verts

    print(f'assign deform weights:build_adjacencies: vid_count={len(vid2weight)}, {datetime.datetime.now() - start_time}')

    adjacencies, vid2uid = build_adjacencies(deform_bmesh_verts, vid2weight)

    # unified vertex id to numpy id
    uid2nid: Dict[int, int] = {uid: nid for nid, uid in enumerate(set(vid2uid.values()))}
    uid2vids: Dict[int, List[int]] = {uid: [vid for vid in vid2uid if vid2uid[vid] == uid] for uid in vid2uid.values()}
    nid2uid: Dict[int, int] = {v: k for k, v in uid2nid.items()}

    sink_nids: Set[int] = set()

    for index, weight in vid2weight.items():
        if weight > 0:
            continue
        sink_nids.add(uid2nid[vid2uid[index]])

    nid_count = len(uid2nid)

    adjacency_matrix = np.zeros((nid_count, nid_count))
    for (from_uid, to_uid), span in adjacencies.items():
        magnitude = math.exp(-span)
        adjacency_matrix[uid2nid[from_uid], uid2nid[to_uid]] = magnitude
        adjacency_matrix[uid2nid[to_uid], uid2nid[from_uid]] = magnitude

    deform_bmesh_verts.ensure_lookup_table()
    vertex_kdtree = mathutils.kdtree.KDTree(nid_count)
    for uid in uid2nid:
        if vid2weight[uid] == 0:
            continue
        vertex_kdtree.insert(deform_bmesh_verts[uid].co, uid)
    vertex_kdtree.balance()

    def collect_nid2weight(position: Vector, scale: float):
        max_weight: Optional[float] = None
        nid2weight: Dict[int, float] = {}
        for _co, near_uid, near_span in vertex_kdtree.find_n(position, 16):
            weight = math.exp(-near_span/scale)

            if max_weight is None:
                max_weight = weight
                weight = 1
            else:
                weight = weight / max_weight

            nid2weight[uid2nid[near_uid]] = weight

            if weight < 0.4:
                break

        return nid2weight

    bone_names = PyramidBoneNames(target_bone_name)

    pyramid_armature: bpy.types.Armature = pyramid_armature_object.data
    pyramid_origin = pyramid_armature_object.location
    bone_length = pyramid_armature.bones[bone_names.apex].length

    bone_name2nid2weight: Dict[str, Dict[int, float]] = {
        bone_names.apex: collect_nid2weight(pyramid_armature.bones[bone_names.apex].tail_local + pyramid_origin, bone_length),
        bone_names.base_a: collect_nid2weight(pyramid_armature.bones[bone_names.base_a].head_local + pyramid_origin, bone_length),
        bone_names.base_b: collect_nid2weight(pyramid_armature.bones[bone_names.base_b].head_local + pyramid_origin, bone_length),
        bone_names.base_c: collect_nid2weight(pyramid_armature.bones[bone_names.base_c].head_local + pyramid_origin, bone_length),
        bone_names.base_d: collect_nid2weight(pyramid_armature.bones[bone_names.base_d].head_local + pyramid_origin, bone_length),
    }

    print(f'assign deform weights:auto_weight: nid_count={nid_count}, {datetime.datetime.now() - start_time}')

    laplacian_matrix = np.diag(np.sum(adjacency_matrix, axis=1))
    laplacian_matrix -= adjacency_matrix
    eigen_values, eigen_vector = np.linalg.eigh(laplacian_matrix)
    diffusion = np.exp(-eigen_values*2)

    for bone_name in bone_name2nid2weight:
        nid2weight = {
            nid: (weight * 10 if b == bone_name else -weight)
            for b, n2w in bone_name2nid2weight.items()
            for nid, weight in n2w.items()
        }

        print(f'assign deform weights:auto_weight: {bone_name}, {datetime.datetime.now() - start_time}')

        weights = np.zeros(nid_count)
        for _iteration in range(min(60, nid_count//2)):
            for nid, weight in nid2weight.items():
                if weight > 0:
                    weights[nid] += weight
                else:
                    weights[nid] = 0

            weights = eigen_vector.T @ weights
            weights *= diffusion
            weights = eigen_vector @ weights

            for nid in sink_nids:
                weights[nid] = 0

        # normalize
        weights[weights < 0] = 0
        weights = weights / np.max(weights)

        mesh_editor.edit_vertex_group(bone_name, [
            (uid2vids[nid2uid[nid]], weights[nid].item() * vid2weight[nid2uid[nid]]) for nid in range(nid_count)
        ])

    deform_bmesh.free()
    print(f'assign deform weights:finish: {datetime.datetime.now() - start_time}')


def to_vid2weight(deform_bmesh: bmesh.types.BMesh, vertex_group_index: int) -> Dict[int, float]:
    vid2weight: Dict[int, float] = {}

    deform_layer = deform_bmesh.verts.layers.deform.verify()

    tri_loops: Tuple[bmesh.types.BMLoop, bmesh.types.BMLoop, bmesh.types.BMLoop]
    for tri_loops in deform_bmesh.calc_loop_triangles():
        loop_vid2weight = {l.vert.index: l.vert[deform_layer].get(vertex_group_index, 0.0) for l in tri_loops}
        if max(loop_vid2weight.values()) == 0:
            continue

        vid2weight.update(loop_vid2weight)

    return vid2weight


def expand_boundary(vid2weight: Dict[int, float], deform_bmesh: bmesh.types.BMesh, boundary_expansion_hop_count: int):
    if boundary_expansion_hop_count == 0:
        return vid2weight

    limit_weight = max(vid2weight.values())

    new_boundary_vids: Set[int] = set()
    old_boundary_vids: Set[int] = set()

    for _iteration in range(boundary_expansion_hop_count):
        edge: bmesh.types.BMEdge
        for edge in deform_bmesh.edges:
            vert0_vid = edge.verts[0].index
            vert0_isin = vert0_vid in vid2weight
            vert1_vid = edge.verts[1].index
            vert1_isin = vert1_vid in vid2weight

            if vert0_isin and vert1_isin:
                old_boundary_vids.add(vert0_vid)
                old_boundary_vids.add(vert1_vid)

            elif vert0_isin:
                old_boundary_vids.add(vert0_vid)
                new_boundary_vids.add(vert1_vid)

            elif vert1_isin:
                new_boundary_vids.add(vert0_vid)
                old_boundary_vids.add(vert1_vid)

        for vid in new_boundary_vids:
            vid2weight.setdefault(vid, 0)
        new_boundary_vids.clear()

        for vid in old_boundary_vids:
            vid2weight[vid] += 0.1
        old_boundary_vids.clear()

    weight_scale = limit_weight / max(vid2weight.values())

    return {
        vid: weight * weight_scale
        for vid, weight in vid2weight.items()
    }


def build_adjacencies(
    verts: bmesh.types.BMVertSeq,
    vid2weight: Dict[int, float]
) -> Tuple[Dict[Tuple[int, int], float], Dict[int, int]]:

    verts.ensure_lookup_table()
    vert_kdtree = mathutils.kdtree.KDTree(len(vid2weight))
    for vid in vid2weight:
        vert_kdtree.insert(verts[vid].co, vid)
    vert_kdtree.balance()

    # vertex id to unified vertex id
    vid2uid_span: Dict[int, Tuple[int, float]] = {}

    # build adjacency dictionary
    adjacencies: Dict[Tuple[int, int], float] = {}

    for from_vid in vid2weight:
        from_vert: bmesh.types.BMVert = verts[from_vid]

        link_vids: List[int] = [e.other_vert(from_vert).index for e in from_vert.link_edges]

        if len(link_vids) == 0:
            continue

        link_vert_spans: List[float] = [(verts[vid].co - from_vert.co).length for vid in link_vids]
        link_vert_min_span: float = min(link_vert_spans)
        link_vert_max_span: float = max(link_vert_spans)

        from_uid, span = vid2uid_span.setdefault(from_vid, (from_vid, 0))
        if span > link_vert_min_span:
            vid2uid_span[from_vid] = (from_vid, 0)
            from_uid = from_vid

        # collect unified vertices
        for _co, near_vid, near_span in vert_kdtree.find_range(from_vert.co, link_vert_max_span):
            if from_vid == near_vid:
                continue

            if near_span < link_vert_min_span:
                near_uid, span = vid2uid_span.setdefault(near_vid, (from_uid, near_span))
                if span > near_span:
                    vid2uid_span[near_vid] = (from_uid, near_span)
                    near_uid = from_uid
            elif near_vid not in link_vids:
                continue
            else:
                near_uid, _span = vid2uid_span.setdefault(near_vid, (near_vid, near_span))

            if from_uid == near_uid:
                continue

            adjacencies[(from_uid, near_uid)] = near_span

    vid2uid = {vid: uid for vid, (uid, _span) in vid2uid_span.items()}
    return {
        (vid2uid[from_xid], vid2uid[near_xid]): span
        for (from_xid, near_xid), span in adjacencies.items()
    }, vid2uid


def to_pyramid_vertices(deform_bmesh: bmesh.types.BMesh, target: Target, base_area_factor: float, project_vertically: bool) -> Tuple[Vector, List[Vector]]:
    to_world_matrix: Matrix = target.deform_mesh_object.matrix_world

    target_direction: Vector = target.direction
    target_origin: Vector = target.origin

    apex_vertex, vid2weight = to_apex_vertex(deform_bmesh, to_world_matrix, target_direction, target_origin, target.vertex_group.index)
    if apex_vertex is None:
        raise MessageException(f'The intersection of {target.bone_name} and {target.deform_mesh_object.name} not found.') from None

    base_vertices = to_base_vertices(deform_bmesh.verts, to_world_matrix, target_direction, target_origin, vid2weight, base_area_factor, project_vertically)

    return apex_vertex, base_vertices


def to_apex_vertex(deform_bmesh: bmesh.types.BMesh, to_world_matrix, target_direction, target_origin, vertex_group_index) -> Tuple[Vector, Dict[int, float]]:
    deform_layer = deform_bmesh.verts.layers.deform.verify()

    vid2weight: Dict[int, float] = {}

    mesh_max_weight = 0.0

    apex_location: Optional[Vector] = None

    tri_loops: Tuple[bmesh.types.BMLoop, bmesh.types.BMLoop, bmesh.types.BMLoop]
    for tri_loops in deform_bmesh.calc_loop_triangles():
        vertex_weights = [l.vert[deform_layer].get(vertex_group_index, 0.0) for l in tri_loops]
        loop_max_weight: float = max(vertex_weights)
        if loop_max_weight == 0:
            continue

        if mesh_max_weight < loop_max_weight:
            mesh_max_weight = loop_max_weight

        intersection: Vector = mathutils.geometry.intersect_ray_tri(
            to_world_matrix @ tri_loops[0].vert.co, to_world_matrix @ tri_loops[1].vert.co, to_world_matrix @ tri_loops[2].vert.co,
            target_direction, target_origin
        )

        vid2weight[tri_loops[0].vert.index] = vertex_weights[0]
        vid2weight[tri_loops[1].vert.index] = vertex_weights[1]
        vid2weight[tri_loops[2].vert.index] = vertex_weights[2]

        if intersection is None:
            continue

        apex_location = intersection

    if apex_location is None:
        return None, None

    return (
        apex_location - target_origin,
        {k: v/mesh_max_weight for k, v in vid2weight.items()}
    )


def to_base_vertices(deform_verts: bmesh.types.BMVertSeq, to_world_matrix, target_direction, target_origin, deform_vertex_index_weights: Dict[int, float], base_area_factor: float, project_vertically: bool) -> List[Vector]:
    ortho_projection_matrix = Matrix.OrthoProjection(target_direction, 4)

    f_l = 1
    intrinsic_matrix = Matrix([
        [f_l, 0.0, 0.0, 0.0],
        [0.0, f_l, 0.0, 0.0],
        [0.0, 0.0, f_l, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    wide_projection_matrix: Matrix = intrinsic_matrix @ ortho_projection_matrix @ Matrix.Translation(-target_origin)

    wide_project_2d_vertices: Set[Tuple[float, float]] = set()
    wide_project_3d_vertices: List[Vector] = []

    deform_verts.ensure_lookup_table()
    for deform_vertex_index, deform_vertex_weight in deform_vertex_index_weights.items():
        wide_project_3d_vertex = wide_projection_matrix @ (to_world_matrix @ deform_verts[deform_vertex_index].co)
        wide_project_2d_vertex = wide_project_3d_vertex / wide_project_3d_vertex[2]

        wide_project_2d_vertices.add(wide_project_2d_vertex[0:2])
        wide_project_3d_vertices.append(wide_project_3d_vertex * (deform_vertex_weight**base_area_factor))

    box_fit_angle: float = mathutils.geometry.box_fit_2d(list(wide_project_2d_vertices))
    rotate_matrix: Matrix = Matrix.Rotation(+box_fit_angle, 4, target_direction) @ ortho_projection_matrix

    x_min = float('+inf')
    x_max = float('-inf')
    z_min = float('+inf')
    z_max = float('-inf')

    for vertex in wide_project_3d_vertices:
        rotate_vertex: Vector = rotate_matrix @ vertex

        if x_min > rotate_vertex.x:
            x_min = rotate_vertex.x

        if x_max < rotate_vertex.x:
            x_max = rotate_vertex.x

        if z_min > rotate_vertex.z:
            z_min = rotate_vertex.z

        if z_max < rotate_vertex.z:
            z_max = rotate_vertex.z

    rotate_matrix_invert: Matrix
    if project_vertically:
        front_vector = Vector([0, -1, 0])
        rotate_matrix_invert = Matrix.Rotation(-box_fit_angle, 4, front_vector) @ Matrix.OrthoProjection(front_vector, 4)
    else:
        rotate_matrix_invert = Matrix.Rotation(-box_fit_angle, 4, target_direction) @ ortho_projection_matrix

    base_vertices: List[Vector] = [
        rotate_matrix_invert @ Vector([x_min, 0, 0]),
        rotate_matrix_invert @ Vector([0, 0, z_min]),
        rotate_matrix_invert @ Vector([x_max, 0, 0]),
        rotate_matrix_invert @ Vector([0, 0, z_max]),
    ]

    return base_vertices


def to_targets(breast_bones: List[bpy.types.EditBone], deform_mesh_objects: List[bpy.types.Object], head_tail: float) -> List[Target]:
    targets: List[Target] = []

    for breast_bone in breast_bones:
        breast_bone_direction_vector: Vector = breast_bone.vector.normalized()

        bone_name = breast_bone.name
        parent_bone_name: str
        origin: Vector
        direction: Vector

        if breast_bone_direction_vector.z < -0.6:
            if not breast_bone.use_connect:
                raise MessageException('Unsupported breast bone structure.') from None

            parent_bone_name = breast_bone.parent.parent.name
            direction = breast_bone.parent.vector.normalized()
            origin = breast_bone.parent.head + breast_bone.vector / 2 + head_tail * breast_bone.parent.vector

        elif -0.4 < breast_bone_direction_vector.z < +0.4:
            parent_bone_name = breast_bone.parent.name
            direction = breast_bone_direction_vector
            origin = breast_bone.head + head_tail * breast_bone.vector

        else:
            raise MessageException(f'Unsupported breast bone structure. too shallow angle {breast_bone_direction_vector.z}') from None

        for deform_mesh_object in deform_mesh_objects:
            vertex_group = deform_mesh_object.vertex_groups.get(bone_name)
            if vertex_group is None:
                continue

            targets.append(Target(
                bone_name,
                parent_bone_name,
                deform_mesh_object,
                vertex_group,
                origin,
                direction,
            ))

    return targets


class AddPyramidMeshByBreastBoneOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.add_pyramid_mesh_by_breast_bone'
    bl_label = _('Add Pyramid Mesh by Breast Bone')
    bl_options = {'REGISTER', 'UNDO'}

    head_tail: bpy.props.FloatProperty(name=_('Head/Tail'), default=0.5, min=0.0, max=1.0, step=10)
    string_length_ratio: bpy.props.FloatProperty(name=_('String Length Ratio'), default=2.0, min=1.0, max=100.0, step=10)
    base_area_factor: bpy.props.FloatProperty(name=_('Base Area Factor'), default=0.1, min=0.0, max=100.0, step=10)
    project_vertically: bpy.props.BoolProperty(name=_('Project Base Vertices Vertically'), default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'EDIT_ARMATURE':
            return False

        if len(context.selected_bones) == 0:
            # At least one bone must be selected.
            return False

        for obj in context.selected_objects:
            # At least one mesh must be selected.
            if obj.type == 'MESH':
                return True

        return False

    def execute(self, context: bpy.types.Context):
        try:
            target_edit_bones: List[bpy.types.EditBone] = [b for b in context.selected_editable_bones if b.use_deform]
            target_mesh_objects: List[bpy.types.Object] = [o for o in context.selected_objects if o.type == 'MESH' and not o.hide]

            add_pyramid_mesh_objects(
                target_edit_bones,
                target_mesh_objects,
                self.head_tail,
                self.string_length_ratio,
                self.base_area_factor,
                self.project_vertically
            )

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class ConvertPyramidMeshToClothOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.convert_pyramid_mesh_to_cloth'
    bl_label = _('Convert Pyramid Mesh to Cloth')
    bl_options = {'REGISTER', 'UNDO'}

    boundary_expansion_hop_count: bpy.props.IntProperty(name=_('Boundary Expansion Hop Count'), default=0, min=0, max=5)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        pyramid_mesh_count = 0
        deform_mesh_count = 0
        target_armature_count = 0

        obj: bpy.types.Object
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if PyramidMeshEditor.is_pyramid_mesh_object(obj):
                    if obj.parent is not None:
                        continue  # already converted
                    pyramid_mesh_count += 1
                else:
                    deform_mesh_count += 1

            elif obj.type == 'ARMATURE':
                target_armature_count += 1

            else:
                continue

            if pyramid_mesh_count > 0 and deform_mesh_count > 0:
                return True

        return False

    def execute(self, context: bpy.types.Context):
        try:
            pyramid_mesh_objects: List[bpy.types.Object] = []
            deform_mesh_objects: List[bpy.types.Object] = []

            obj: bpy.types.Object
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    if PyramidMeshEditor.is_pyramid_mesh_object(obj):
                        if obj.parent is not None:
                            continue  # already converted
                        pyramid_mesh_objects.append(obj)
                    else:
                        deform_mesh_objects.append(obj)

            convert_pyramid_mesh_to_cloth(
                pyramid_mesh_objects,
                deform_mesh_objects,
                self.boundary_expansion_hop_count
            )

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class AssignPyramidWeightsOperator(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.assign_pyramid_weights'
    bl_label = _('Assign Pyramid Weights')
    bl_options = {'REGISTER', 'UNDO'}

    boundary_expansion_hop_count: bpy.props.IntProperty(name=_('Boundary Expansion Hop Count'), default=0, min=0, max=5)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != 'OBJECT':
            return False

        pyramid_mesh_count = 0
        target_mesh_count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            if PyramidMeshEditor.is_pyramid_mesh_object(obj):
                pyramid_mesh_count += 1
            else:
                target_mesh_count += 1

            if pyramid_mesh_count > 0 and target_mesh_count > 0:
                return True

        return False

    def execute(self, context: bpy.types.Context):
        try:
            pyramid_mesh_objects: List[bpy.types.Object] = []
            deform_mesh_objects: List[bpy.types.Object] = []

            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue

                if PyramidMeshEditor.is_pyramid_mesh_object(obj):
                    pyramid_mesh_objects.append(obj)
                else:
                    deform_mesh_objects.append(obj)

            assign_pyramid_weights(
                pyramid_mesh_objects,
                deform_mesh_objects,
                self.boundary_expansion_hop_count
            )

        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))
            return {'CANCELLED'}

        return {'FINISHED'}


class UuuNyaaPyramidClothAdjuster(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_pyramid_cloth_adjuster'
    bl_label = _('UuuNyaa Pyramid Cloth Adjuster')
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return PyramidMeshEditor.is_pyramid_mesh_object(context.active_object)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mesh_object: bpy.types.Object = context.active_object
        pyramid_cloth_settings = mesh_object.mmd_uuunyaa_tools_pyramid_cloth_settings

        box = layout.box()

        col = box.column()
        col.label(text=_('Weights:'))
        col.prop(pyramid_cloth_settings, 'string_pin_weight')
        col.prop(pyramid_cloth_settings, 'apex_pin_weight')
        col.prop(pyramid_cloth_settings, 'base_pin_weight')

        col = box.column()
        col.label(text=_('Cloth Physics:'))
        col.prop(pyramid_cloth_settings, 'time_scale')

        col = box.column()
        col.label(text=_('Batch Operation:'))
        col.operator(CopyPyramidClothAdjusterSettings.bl_idname, text=_('Copy to Selected'), icon='DUPLICATE')


class CopyPyramidClothAdjusterSettings(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.copy_pyramid_cloth_adjuster_settings'
    bl_label = _('Copy Pyramid Cloth Adjuster Settings')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len([o for o in context.selected_objects if o.type == 'MESH']) >= 2

    def execute(self, context: bpy.types.Context):
        from_object = context.active_object
        from_editor = PyramidMeshEditor(from_object)

        for to_object in context.selected_objects:
            if not PyramidMeshEditor.is_pyramid_mesh_object(to_object):
                continue

            if from_object == to_object:
                continue

            to_editor = PyramidMeshEditor(to_object)
            to_editor.string_pin_weight = from_editor.string_pin_weight
            to_editor.apex_pin_weight = from_editor.apex_pin_weight
            to_editor.base_pin_weight = from_editor.base_pin_weight
            to_editor.time_scale = from_editor.time_scale

        return {'FINISHED'}


class PyramidClothAdjusterSettingsPropertyGroup(bpy.types.PropertyGroup):
    string_pin_weight: bpy.props.FloatProperty(
        name=_('String Pin Weight'), min=0.0, max=1.0, precision=3, step=10,
        get=lambda p: PyramidMeshEditor(p.id_data).string_pin_weight,
        set=lambda p, v: setattr(PyramidMeshEditor(p.id_data), 'string_pin_weight', v),
    )

    apex_pin_weight: bpy.props.FloatProperty(
        name=_('Apex Pin Weight'), min=0.0, max=1.0, precision=3, step=10,
        get=lambda p: PyramidMeshEditor(p.id_data).apex_pin_weight,
        set=lambda p, v: setattr(PyramidMeshEditor(p.id_data), 'apex_pin_weight', v),
    )

    base_pin_weight: bpy.props.FloatProperty(
        name=_('Base Pin Weight'), min=0.0, max=1.0, precision=3, step=10,
        get=lambda p: PyramidMeshEditor(p.id_data).base_pin_weight,
        set=lambda p, v: setattr(PyramidMeshEditor(p.id_data), 'base_pin_weight', v),
    )

    time_scale: bpy.props.FloatProperty(
        name=_('Speed Multiplier'), min=0.0, soft_max=10.0, precision=3, step=10,
        get=lambda p: PyramidMeshEditor(p.id_data).time_scale,
        set=lambda p, v: setattr(PyramidMeshEditor(p.id_data), 'time_scale', v),
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_uuunyaa_tools_pyramid_cloth_settings = bpy.props.PointerProperty(type=PyramidClothAdjusterSettingsPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_uuunyaa_tools_pyramid_cloth_settings
