# -*- coding: utf-8 -*-
# Copyright 2021
#   小威廉伯爵 https://github.com/958261649/Miku_Miku_Rig
#   UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Set, Tuple

import bmesh
import bpy
from ...editors.meshes import MeshEditor
from ...m17n import _, iface_
from ...utilities import MessageException, import_mmd_tools


class PhysicsMode(Enum):
    AUTO = 'Auto'
    BONE_CONSTRAINT = 'Bone Constraint'
    SURFACE_DEFORM = 'Surface Deform'


translation_properties = [
    _('Auto'),
    _('Bone Constraint'),
    _('Surface Deform'),
]


@dataclass
class Edges:
    up_edges: Set[bmesh.types.BMEdge] = field(default_factory=set)
    down_edges: Set[bmesh.types.BMEdge] = field(default_factory=set)
    side_edges: Set[bmesh.types.BMEdge] = field(default_factory=set)


@dataclass
class Vertices:
    up_verts: Set[bmesh.types.BMVert] = field(default_factory=set)
    down_verts: Set[bmesh.types.BMVert] = field(default_factory=set)
    ribbon_verts: Set[bmesh.types.BMVert] = field(default_factory=set)
    side_verts: Set[bmesh.types.BMVert] = field(default_factory=set)
    all_ribbon: bool = False


class RigidBodyToClothConverter:
    @classmethod
    def convert(
        cls,
        mmd_root_object: bpy.types.Object,
        rigid_body_objects: List[bpy.types.Object],
        mesh_objects: List[bpy.types.Object],
        subdivision_level: int,
        ribbon_stiffness: float,
        physics_mode: PhysicsMode,
        extend_ribbon_area: bool
    ):  # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals, too-many-statements
        mmd_model = import_mmd_tools().core.model.Model(mmd_root_object)
        mmd_mesh_object = mesh_objects[0]
        mmd_armature_object = mmd_model.armature()

        rigid_bodys_count = len(rigid_body_objects)
        rigid_body_index_dict = {
            rigid_body_objects[i]: i
            for i in range(rigid_bodys_count)
        }

        pose_bones: List[bpy.types.PoseBone] = []
        for rigid_body_object in rigid_body_objects:
            pose_bone = mmd_armature_object.pose.bones.get(rigid_body_object.mmd_rigid.bone)

            if pose_bone is None:
                raise MessageException(
                    iface_('No bones related with {rigid_body_name}, Please relate a bone to the Rigid Body.')
                    .format(rigid_body_name=rigid_body_object.name)
                )

            pose_bones.append(pose_bone)

        def remove_objects(objects: Iterable[bpy.types.Object]):
            for obj in objects:
                bpy.data.objects.remove(obj)

        joint_objects, joint_edge_indices, side_joint_objects = cls.collect_joints(mmd_model, rigid_body_index_dict)

        remove_objects(joint_objects)

        cloth_mesh = bpy.data.meshes.new('physics_cloth')
        cloth_mesh.from_pydata([r.location for r in rigid_body_objects], joint_edge_indices, [])
        cloth_mesh.validate()

        cloth_mesh_object = bpy.data.objects.new('physics_cloth', cloth_mesh)
        cloth_mesh_object.parent = mmd_model.clothGroupObject()
        cloth_mesh_object.hide_render = True
        cloth_mesh_object.display_type = 'WIRE'

        # 标记出特殊边和点
        # These are special edge and vertex
        cloth_bm: bmesh.types.BMesh = bmesh.new()
        cloth_bm.from_mesh(cloth_mesh)

        cls.clean_mesh(cloth_bm, joint_edge_indices)

        # 标出头部，尾部，飘带顶点
        # try mark head,tail,ribbon vertex
        cloth_bm.verts.ensure_lookup_table()
        cloth_bm.edges.ensure_lookup_table()

        vertices = cls.collect_vertices(cloth_bm, pose_bones, physics_mode, extend_ribbon_area)
        edges = cls.collect_edges(cloth_bm, vertices)

        new_up_verts = cls.extend_up_edges(cloth_bm, pose_bones, vertices, edges, physics_mode)
        new_down_verts = cls.extend_down_edges(cloth_bm, pose_bones, vertices, edges)

        cls.fill_faces(cloth_bm, edges.up_edges, new_up_verts)
        cls.fill_faces(cloth_bm, edges.down_edges, new_down_verts)

        cloth_bm.verts.index_update()
        cloth_bm.faces.ensure_lookup_table()

        new_side_verts = cls.extend_side_vertices(cloth_bm, vertices, edges)
        cls.fill_faces(cloth_bm, edges.side_edges, new_side_verts)

        new_ribbon_verts = cls.extend_ribbon_vertices(cloth_bm)
        cls.fill_faces(cloth_bm, [e for e in cloth_bm.edges if e.is_wire], new_ribbon_verts)

        cls.normals_make_consistent(cloth_bm)
        cloth_bm.verts.ensure_lookup_table()
        cloth_bm.edges.ensure_lookup_table()
        cloth_bm.to_mesh(cloth_mesh)

        pin_vertex_group = cls.new_pin_vertex_group(cloth_mesh_object, side_joint_objects, new_up_verts, new_side_verts, rigid_body_index_dict)

        remove_objects(side_joint_objects)

        deform_vertex_group: bpy.types.VertexGroup = mmd_mesh_object.vertex_groups.new(name='physics_cloth_deform')

        mesh_editor = MeshEditor(cloth_mesh_object)
        mesh_editor.link_to_active_collection()
        mesh_editor.add_subsurface_modifier('physics_cloth_subsurface', subdivision_level, subdivision_level)
        mesh_editor.add_armature_modifier('physics_cloth_armature', mmd_armature_object, vertex_group=pin_vertex_group.name)
        mesh_editor.edit_cloth_modifier('physics_cloth', vertex_group_mass=pin_vertex_group.name)

        corrective_smooth_modifier = mesh_editor.add_corrective_smooth_modifier('physics_cloth_smooth', smooth_type='LENGTH_WEIGHTED', rest_source='BIND')
        bpy.ops.object.correctivesmooth_bind(modifier=corrective_smooth_modifier.name)
        if subdivision_level == 0:
            corrective_smooth_modifier.show_viewport = False

        deform_vertex_group_index = deform_vertex_group.index
        vertices_ribbon_verts = vertices.ribbon_verts

        cls.bind_mmd_mesh(mmd_mesh_object, cloth_mesh_object, cloth_bm, pose_bones, deform_vertex_group_index, vertices_ribbon_verts, physics_mode)
        cls.set_pin_vertex_weight(pin_vertex_group, vertices_ribbon_verts, ribbon_stiffness, physics_mode)

        remove_objects(rigid_body_objects)

        if not vertices.all_ribbon and physics_mode in {PhysicsMode.AUTO, PhysicsMode.SURFACE_DEFORM}:
            bpy.context.view_layer.objects.active = mmd_mesh_object
            bpy.ops.object.surfacedeform_bind(
                modifier=MeshEditor(mmd_mesh_object).add_surface_deform_modifier(
                    'physics_cloth_deform',
                    target=cloth_mesh_object,
                    vertex_group=deform_vertex_group.name
                ).name
            )

        cloth_bm.free()

    @staticmethod
    def bind_mmd_mesh(mmd_mesh_object: bpy.types.Object, cloth_mesh_object: bpy.types.Object, cloth_bm: bmesh.types.BMesh, pose_bones, deform_vertex_group_index, vertices_ribbon_verts, physics_mode):
        # pylint: disable=too-many-arguments, too-many-locals

        unnecessary_vertex_groups: List[bpy.types.VertexGroup] = []

        mmd_mesh: bpy.types.Mesh = mmd_mesh_object.data
        mmd_bm: bmesh.types.BMesh = bmesh.new()
        mmd_bm.from_mesh(mmd_mesh)

        mmd_bm.verts.layers.deform.verify()
        deform_layer = mmd_bm.verts.layers.deform.active

        bone: bpy.types.PoseBone
        for i, bone in enumerate(pose_bones):
            vert = cloth_bm.verts[i]
            name = bone.name
            if (
                vert in vertices_ribbon_verts and physics_mode == PhysicsMode.AUTO
                or physics_mode == PhysicsMode.BONE_CONSTRAINT
            ):
                line_vertex_group = cloth_mesh_object.vertex_groups.new(name=name)
                line_vertex_group.add([i], 1, 'REPLACE')
                for c in bone.constraints:
                    bone.constraints.remove(c)
                con: bpy.types.StretchToConstraint = bone.constraints.new(type='STRETCH_TO')
                con.target = cloth_mesh_object
                con.subtarget = name
                con.rest_length = bone.length
            else:
                # merge deform vertex weights
                from_vertex_group = mmd_mesh_object.vertex_groups.get(name)
                from_index = from_vertex_group.index
                unnecessary_vertex_groups.append(from_vertex_group)

                vert: bmesh.types.BMVert
                for vert in mmd_bm.verts:
                    deform_vert: bmesh.types.BMDeformVert = vert[deform_layer]
                    if from_index not in deform_vert:
                        continue

                    to_index = deform_vertex_group_index
                    deform_vert[to_index] = deform_vert.get(to_index, 0.0) + deform_vert[from_index]

        mmd_bm.to_mesh(mmd_mesh)
        mmd_bm.free()

        for vertex_group in unnecessary_vertex_groups:
            mmd_mesh_object.vertex_groups.remove(vertex_group)

    @staticmethod
    def new_pin_vertex_group(cloth_mesh_object: bpy.types.Object, side_joint_objects: List[bpy.types.Object], new_up_verts, new_side_verts, rigid_body_index_dict):
        pin_vertex_group = cloth_mesh_object.vertex_groups.new(name='physics_cloth_pin')

        for obj in side_joint_objects:
            if obj.rigid_body_constraint.object1 in rigid_body_index_dict:
                side_rigid_body = obj.rigid_body_constraint.object1
                pin_rigid_body = obj.rigid_body_constraint.object2
            else:
                side_rigid_body = obj.rigid_body_constraint.object2
                pin_rigid_body = obj.rigid_body_constraint.object1

            index1 = rigid_body_index_dict[side_rigid_body]
            vert2 = new_up_verts[index1]
            if vert2 is None:
                pin_index = [index1]
            else:
                vert3 = new_side_verts[vert2.index]
                if vert3 is None:
                    pin_index = [vert2.index]
                else:
                    pin_index = [vert2.index, vert3.index]

            pin_bone_name = pin_rigid_body.mmd_rigid.bone

            skin_vertex_group = cloth_mesh_object.vertex_groups.get(pin_bone_name)
            if skin_vertex_group is None:
                skin_vertex_group = cloth_mesh_object.vertex_groups.new(name=pin_bone_name)

            skin_vertex_group.add(pin_index, 1, 'REPLACE')
            pin_vertex_group.add(pin_index, 1, 'REPLACE')

        return pin_vertex_group

    @staticmethod
    def set_pin_vertex_weight(pin_vertex_group: bpy.types.VertexGroup, vertices_ribbon_verts: bmesh.types.BMVertSeq, weight: float, physics_mode: PhysicsMode):
        vert: bmesh.types.BMVert
        for vert in vertices_ribbon_verts:
            if (
                vert in vertices_ribbon_verts and physics_mode == PhysicsMode.AUTO
                or physics_mode == PhysicsMode.BONE_CONSTRAINT
            ):
                pin_vertex_group.add([vert.index], weight, 'REPLACE')

    @staticmethod
    def normals_make_consistent(cloth_bm: bmesh.types.BMesh):
        bmesh.ops.recalc_face_normals(cloth_bm, faces=cloth_bm.faces)
        cloth_bm.normal_update()

    @staticmethod
    def extend_side_vertices(cloth_bm: bmesh.types.BMesh, vertices: Vertices, edges: Edges) -> List[Optional[bmesh.types.BMVert]]:
        new_side_verts: List[Optional[bmesh.types.BMVert]] = [None for i in range(len(cloth_bm.verts))]

        for vert in vertices.side_verts:
            for edge in vert.link_edges:
                if edge not in edges.side_edges:
                    if edge.verts[0] == vert:
                        new_location = vert.co*2-edge.verts[1].co
                    else:
                        new_location = vert.co*2-edge.verts[0].co
                    break
            new_vert = cloth_bm.verts.new(new_location, vert)
            new_side_verts[vert.index] = new_vert

        return new_side_verts

    @staticmethod
    def extend_ribbon_vertices(cloth_bm: bmesh.types.BMesh) -> List[Optional[bmesh.types.BMVert]]:
        # 挤出飘带顶点
        # extrude ribbon edge
        new_ribbon_verts: List[Optional[bmesh.types.BMVert]] = [None for i in range(len(cloth_bm.verts))]

        for vert in cloth_bm.verts:
            if not vert.is_wire:
                continue

            new_location = [vert.co[0], vert.co[1]+0.01, vert.co[2]]
            new_vert = cloth_bm.verts.new(new_location, vert)
            new_ribbon_verts[vert.index] = new_vert

        return new_ribbon_verts

    @staticmethod
    def fill_faces(cloth_bm, edges, new_verts):
        for edge in edges:
            vert1 = edge.verts[0]
            vert2 = edge.verts[1]
            vert3 = new_verts[vert2.index]
            vert4 = new_verts[vert1.index]

            if vert3 is not None and vert4 is not None:
                cloth_bm.faces.new([vert1, vert2, vert3, vert4])

    @staticmethod
    def extend_up_edges(cloth_bm: bmesh.types.BMesh, pose_bones: List[bpy.types.PoseBone], vertices: Vertices, edges: Edges, physics_mode: PhysicsMode) -> List[Optional[bmesh.types.BMVert]]:
        new_up_verts: List[Optional[bmesh.types.BMVert]] = [None for i in range(len(cloth_bm.verts))]

        # 延长头部顶点
        # extend root vertex
        for vert in vertices.up_verts:
            new_location = pose_bones[vert.index].head

            if (
                (physics_mode == PhysicsMode.AUTO and vert not in vertices.ribbon_verts)
                or physics_mode == PhysicsMode.SURFACE_DEFORM
            ):
                for edge in vert.link_edges:
                    if edge in edges.up_edges:
                        break

                    if edge.verts[0] == vert:
                        new_location = vert.co*2-edge.verts[1].co
                    else:
                        new_location = vert.co*2-edge.verts[0].co

            new_vert = cloth_bm.verts.new(new_location)
            new_edge = cloth_bm.edges.new([vert, new_vert])
            new_up_verts[vert.index] = new_vert

            if vert in vertices.side_verts:
                vertices.side_verts.add(new_vert)
                edges.side_edges.add(new_edge)

        return new_up_verts

    @staticmethod
    def extend_down_edges(cloth_bm: bmesh.types.BMesh, pose_bones: List[bpy.types.PoseBone], vertices: Vertices, edges: Edges) -> List[Optional[bmesh.types.BMVert]]:
        new_down_verts: List[Optional[bmesh.types.BMVert]] = [None for i in range(len(cloth_bm.verts))]
        # 延长尾部顶点
        # extend tail vertex
        for vert in vertices.down_verts:
            if vert in vertices.up_verts:
                continue

            new_location = pose_bones[vert.index].tail
            for edge in vert.link_edges:
                if edge in edges.down_edges:
                    break

                if edge.verts[0] == vert:
                    new_location = vert.co*2-edge.verts[1].co
                else:
                    new_location = vert.co*2-edge.verts[0].co

            new_vert = cloth_bm.verts.new(new_location)
            new_edge = cloth_bm.edges.new([vert, new_vert])
            new_down_verts[vert.index] = new_vert

            if vert in vertices.side_verts:
                vertices.side_verts.add(new_vert)
                edges.side_edges.add(new_edge)

        return new_down_verts

    @staticmethod
    def collect_joints(mmd_model, rigid_body_index_dict: Dict[bpy.types.Object, int]) -> Tuple[List[bpy.types.Object], List[Tuple[int, int]], List[bpy.types.Object]]:
        joint_objects: List[bpy.types.Object] = []
        joint_edge_indices: List[Tuple[int, int]] = []
        side_joint_objects: List[bpy.types.Object] = []

        for obj in mmd_model.joints():
            obj1 = obj.rigid_body_constraint.object1
            obj2 = obj.rigid_body_constraint.object2
            if obj1 in rigid_body_index_dict and obj2 in rigid_body_index_dict:
                joint_objects.append(obj)
                joint_edge_indices.append((rigid_body_index_dict[obj1], rigid_body_index_dict[obj2]))
            elif obj1 in rigid_body_index_dict or obj2 in rigid_body_index_dict:
                side_joint_objects.append(obj)

        return joint_objects, joint_edge_indices, side_joint_objects

    @staticmethod
    def collect_vertices(cloth_bm: bmesh.types.BMesh, pose_bones: List[bpy.types.PoseBone], physics_mode: PhysicsMode, extend_ribbon_area: bool) -> Vertices:
        vertices = Vertices()

        for vert in cloth_bm.verts:
            if not vert.is_wire:
                continue
            vertices.ribbon_verts.add(vert)

        if extend_ribbon_area:
            boundary_verts = vertices.ribbon_verts
            boundary_verts_next = []
            while len(boundary_verts) != 0:
                for vert in [
                    v2
                    for v in boundary_verts
                    for e in v.link_edges
                    for v2 in e.verts
                    if v2 not in vertices.ribbon_verts
                ]:
                    vertices.ribbon_verts.add(vert)
                    boundary_verts_next.append(vert)
                boundary_verts = boundary_verts_next.copy()
                boundary_verts_next.clear()

        vertices.all_ribbon = True
        for face in cloth_bm.faces:
            ribbon_face: bool = False
            for vert in face.verts:
                if vert in vertices.ribbon_verts:
                    ribbon_face = True
                    break

            if not ribbon_face:
                vertices.all_ribbon = False
                break

        vert: bmesh.types.BMVert
        for vert in cloth_bm.verts:
            bone = pose_bones[vert.index]
            if not bone.bone.use_connect and vert.is_boundary:
                vertices.up_verts.add(vert)
            elif bone.parent not in pose_bones:
                vertices.up_verts.add(vert)
            elif len(bone.children) == 0:
                vertices.down_verts.add(vert)
            elif bone.children[0] not in pose_bones:
                vertices.down_verts.add(vert)

            if (
                vert in vertices.ribbon_verts and physics_mode == PhysicsMode.AUTO
                or physics_mode == PhysicsMode.BONE_CONSTRAINT
            ):
                vert.co = bone.tail

        return vertices

    @staticmethod
    def collect_edges(cloth_bm: bmesh.types.BMesh, vertices: Vertices) -> Edges:
        edges = Edges()

        for edge in cloth_bm.edges:
            if not edge.is_boundary:
                continue

            vert1 = edge.verts[0]
            vert2 = edge.verts[1]
            if vert1 in vertices.up_verts and vert2 in vertices.up_verts:
                edges.up_edges.add(edge)
            elif vert1 in vertices.down_verts and vert2 in vertices.down_verts:
                edges.down_edges.add(edge)
            else:
                edges.side_edges.add(edge)
                if edge.verts[0] not in vertices.side_verts:
                    vertices.side_verts.add(edge.verts[0])
                if edge.verts[1] not in vertices.side_verts:
                    vertices.side_verts.add(edge.verts[1])
        return edges

    @staticmethod
    def clean_mesh(cloth_bm: bmesh.types.BMesh, save_edges: List[Tuple[int, int]]):
        def remove_edges(cloth_bm: bmesh.types.BMesh, save_edges):
            # 删除多余边
            # remove extra edge
            for edge in cloth_bm.edges:
                is_save_edge = False
                for i in save_edges:
                    if edge.verts[0].index in i and edge.verts[1].index in i:
                        is_save_edge = True
                        break

                if not is_save_edge:
                    cloth_bm.edges.remove(edge)

        bmesh.ops.holes_fill(cloth_bm, edges=cloth_bm.edges, sides=4)
        remove_edges(cloth_bm, save_edges)
