# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import math
import os
import re
from abc import ABC
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import bpy
import rna_prop_ui
from mathutils import Matrix, Vector
from mmd_uuunyaa_tools import PACKAGE_PATH
from mmd_uuunyaa_tools.utilities import raise_installation_error

PATH_BLENDS_RIGSHAPELIBRARY = os.path.join(PACKAGE_PATH, 'blends', 'RigShapeLibrary.blend')


@dataclass
class DriverVariable:
    name: str
    target: bpy.types.Object
    data_path: str


class PoseBoneEditor(ABC):
    @staticmethod
    def add_driver(constraint: bpy.types.Constraint, driver_path: str, driver_expression: str, *driver_variables: DriverVariable):
        driver: bpy.types.Driver = constraint.driver_add(driver_path).driver
        for driver_variable in driver_variables:
            variable: bpy.types.DriverVariable = driver.variables.new()
            variable.name = driver_variable.name
            variable.targets[0].id = driver_variable.target
            variable.targets[0].data_path = driver_variable.data_path
        driver.expression = driver_expression

    @classmethod
    def add_influence_driver(cls, constraint: bpy.types.Constraint, target: bpy.types.Object, data_path: str, invert_influence=False):
        variable = DriverVariable('mmd_uuunyaa_influence', target, data_path)
        cls.add_driver(constraint, 'influence', ('1-' if invert_influence else '+') + variable.name, variable)

    @classmethod
    def update_influence_driver(cls, constraint: bpy.types.Constraint, target: bpy.types.Object, data_path: str, invert_influence=False):
        constraint.driver_remove('influence')
        cls.add_influence_driver(constraint, target, data_path, invert_influence=invert_influence)

    @staticmethod
    def add_prop(
        pose_bone: bpy.types.PoseBone,
        prop_name: str,
        default=0.000,
        min=0.000, max=1.000,
        soft_min=None, soft_max=None,
        description=None,
        overridable=True,
        subtype=None
    ):
        # pylint: disable=redefined-builtin,too-many-arguments
        rna_prop_ui.rna_idprop_ui_create(
            pose_bone, prop_name,
            default=default,
            min=min, max=max,
            soft_min=soft_min, soft_max=soft_max,
            description=description,
            overridable=overridable,
            subtype=subtype
        )

    @staticmethod
    def add_constraint(pose_bone: bpy.types.PoseBone, constraint_type: str, name: str, **kwargs) -> bpy.types.Constraint:
        constraints = pose_bone.constraints
        constraint = constraints.new(constraint_type)
        constraint.name = name
        for key, value in kwargs.items():
            setattr(constraint, key, value)
        return constraint

    @staticmethod
    def list_constraints(pose_bone: bpy.types.PoseBone, constraint_type: str) -> Iterable[bpy.types.Constraint]:
        for constraint in pose_bone.constraints:
            if constraint.type == constraint_type:
                yield constraint

    @classmethod
    def edit_constraint(cls, pose_bone: bpy.types.PoseBone, constraint_type: str, **kwargs):
        constraints = list(cls.list_constraints(pose_bone, constraint_type))
        if len(constraints) == 0:
            cls.add_constraint(pose_bone, constraint_type, constraint_type, **kwargs)
        elif len(constraints) == 1:
            constraint = constraints[0]
            for key, value in kwargs.items():
                setattr(constraint, key, value)
        else:
            raise AttributeError('too many constraints')

    @classmethod
    def edit_constraints(cls, pose_bone: bpy.types.PoseBone, constraint_type: str, **kwargs):
        for constraint in cls.list_constraints(pose_bone, constraint_type):
            for key, value in kwargs.items():
                setattr(constraint, key, value)

    @classmethod
    def add_copy_transforms_constraint(
        cls,
        pose_bone: bpy.types.PoseBone,
        target_object: bpy.types.Object,
        subtarget: str,
        space: str,
        influence_data_path: Optional[str] = None,
        invert_influence: bool = False,
        **kwargs
    ) -> bpy.types.Constraint:
        # pylint: disable=too-many-arguments
        constraint = cls.add_constraint(
            pose_bone, 'COPY_TRANSFORMS', 'mmd_uuunyaa_copy_transforms',
            target=target_object,
            subtarget=subtarget,
            target_space=space,
            owner_space=space,
            **kwargs
        )
        if influence_data_path:
            cls.add_influence_driver(constraint, target_object, influence_data_path, invert_influence=invert_influence)
        return constraint

    @classmethod
    def add_copy_rotation_constraint(
        cls,
        pose_bone: bpy.types.PoseBone,
        target_object: bpy.types.Object,
        subtarget: str,
        space: str,
        influence_data_path: Optional[str] = None,
        invert_influence: bool = False,
        **kwargs
    ) -> bpy.types.Constraint:
        # pylint: disable=too-many-arguments
        constraint = cls.add_constraint(
            pose_bone, 'COPY_ROTATION', 'mmd_uuunyaa_copy_rotation',
            target=target_object,
            subtarget=subtarget,
            target_space=space,
            owner_space=space,
            **kwargs
        )
        if influence_data_path:
            cls.add_influence_driver(constraint, target_object, influence_data_path, invert_influence=invert_influence)
        return constraint

    @classmethod
    def add_copy_location_constraint(
        cls,
        pose_bone: bpy.types.PoseBone,
        target_object: bpy.types.Object,
        subtarget: str,
        space: str,
        influence_data_path: Optional[str] = None,
        invert_influence: bool = False,
        **kwargs
    ) -> bpy.types.Constraint:
        # pylint: disable=too-many-arguments
        constraint = cls.add_constraint(
            pose_bone, 'COPY_LOCATION', 'mmd_uuunyaa_copy_location',
            target=target_object,
            subtarget=subtarget,
            target_space=space,
            owner_space=space,
            **kwargs
        )
        if influence_data_path:
            cls.add_influence_driver(constraint, target_object, influence_data_path, invert_influence=invert_influence)
        return constraint

    @classmethod
    def add_copy_scale_constraint(
        cls,
        pose_bone: bpy.types.PoseBone,
        target_object: bpy.types.Object,
        subtarget: str,
        space: str,
        influence_data_path: Optional[str] = None,
        invert_influence: bool = False,
        **kwargs
    ) -> bpy.types.Constraint:
        # pylint: disable=too-many-arguments
        constraint = cls.add_constraint(
            pose_bone, 'COPY_SCALE', 'mmd_uuunyaa_copy_scale',
            target=target_object,
            subtarget=subtarget,
            target_space=space,
            owner_space=space,
            **kwargs
        )
        if influence_data_path:
            cls.add_influence_driver(constraint, target_object, influence_data_path, invert_influence=invert_influence)
        return constraint

    @classmethod
    def add_ik_constraint(
        cls,
        pose_bone: bpy.types.PoseBone,
        target_object: bpy.types.Object,
        subtarget: str,
        chain_count: int,
        iterations: int,
        influence_data_path: Optional[str] = None,
        invert_influence: bool = False,
        **kwargs
    ) -> bpy.types.Constraint:
        # pylint: disable=too-many-arguments
        constraint = cls.add_constraint(
            pose_bone, 'IK', 'mmd_uuunyaa_ik_mmd',
            target=target_object,
            subtarget=subtarget,
            chain_count=chain_count,
            iterations=iterations,
            **kwargs
        )
        if influence_data_path:
            cls.add_influence_driver(constraint, target_object, influence_data_path, invert_influence=invert_influence)
        return constraint

    @staticmethod
    def remove_constraints(pose_bones: Dict[str, bpy.types.PoseBone]):
        for pose_bone in pose_bones.values():
            for constraint in pose_bone.constraints:
                if not constraint.name.startswith('mmd_uuunyaa_'):
                    continue
                pose_bone.constraints.remove(constraint)


class EditBoneEditor(ABC):

    @staticmethod
    def to_center(left: Vector, right: Vector) -> Vector:
        return (left + right) / 2

    @staticmethod
    def to_stretch(from_: Vector, to_: Vector, stretch_factor: float) -> Vector:
        return from_ + (to_ - from_) * stretch_factor

    @classmethod
    def to_bone_center(cls, bone: bpy.types.EditBone) -> Vector:
        return cls.to_center(bone.head, bone.tail)

    @staticmethod
    def to_bone_stretch(bone: bpy.types.EditBone, stretch_factor: float) -> Vector:
        return bone.head + bone.vector * stretch_factor

    @staticmethod
    def to_bone_suffix(bone_name: str) -> Optional[str]:
        match = re.search(r'[_\.]([lLrR])$', bone_name)
        if not match:
            return None

        raw_suffix = match.group(1)
        if raw_suffix in {'l', 'L'}:
            return 'L'
        return 'R'

    @staticmethod
    def to_angle(vector: Vector, plane: str) -> float:
        if plane == 'XZ':
            return math.atan2(vector.z, vector.x)

        if plane == 'XY':
            return math.atan2(vector.y, vector.x)

        if plane == 'YZ':
            return math.atan2(vector.z, vector.y)

        raise ValueError(f"unknown plane, expected: XY, XZ, YZ, not '{plane}'")

    @staticmethod
    def move_bone(edit_bone: bpy.types.EditBone, head: Vector = None, tail: Vector = None):
        vector: Vector = edit_bone.vector

        if head is not None and tail is not None:
            edit_bone.head = head
            edit_bone.tail = tail

        elif head is not None:
            edit_bone.head = head
            edit_bone.tail = head + vector

        elif tail is not None:
            edit_bone.head = tail - vector
            edit_bone.tail = tail

    @staticmethod
    def fit_edit_bone_rotation(target_bone: bpy.types.EditBone, reference_bone: bpy.types.EditBone):
        def set_rotation(bone, rotation_matrix: Matrix):
            bone.matrix = Matrix.Translation(bone.matrix.to_translation()) @ rotation_matrix

        def to_rotation_matrix(bone) -> Matrix:
            return bone.matrix.to_quaternion().to_matrix().to_4x4()

        set_rotation(target_bone, to_rotation_matrix(reference_bone))

    @staticmethod
    def insert_edit_bone(edit_bone: bpy.types.EditBone, parent_bone: bpy.types.EditBone):
        for bone in parent_bone.children:
            bone.parent = edit_bone
        edit_bone.parent = parent_bone

    @staticmethod
    def load_custom_shapes(custom_shape_names: List[str]):
        if len(custom_shape_names) == 0:
            return

        try:
            with bpy.data.libraries.load(PATH_BLENDS_RIGSHAPELIBRARY, link=False) as (_, data_to):
                data_to.objects = custom_shape_names
        except OSError as exception:
            raise_installation_error(exception)


class ArmatureEditor(EditBoneEditor, PoseBoneEditor):
    raw_object: bpy.types.Object
    raw_armature: bpy.types.Armature

    def __init__(self, armature_object: bpy.types.Object):
        self.raw_object = armature_object
        self.raw_armature: bpy.types.Armature = armature_object.data

    @property
    def bones(self) -> bpy.types.ArmatureBones:
        return self.raw_armature.bones

    @property
    def pose_bones(self) -> Dict[str, bpy.types.PoseBone]:
        return self.raw_object.pose.bones

    @property
    def pose_bone_groups(self) -> bpy.types.BoneCollections:
        return self.raw_object.pose.bone_Collections

    @property
    def edit_bones(self) -> bpy.types.ArmatureEditBones:
        return self.raw_armature.edit_bones

    @staticmethod
    def get_or_create_bone(edit_bones: bpy.types.ArmatureEditBones, bone_name: str) -> bpy.types.EditBone:
        if bone_name in edit_bones:
            return edit_bones[bone_name]

        return edit_bones.new(bone_name)
