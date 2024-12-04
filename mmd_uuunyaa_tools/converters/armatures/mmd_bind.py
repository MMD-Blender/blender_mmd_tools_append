# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import bpy
from ...converters.armatures.mmd import MMDBoneInfo
from ...editors.armatures import ArmatureEditor, PoseBoneEditor


class GroupType(Enum):
    NONE = 'none'
    FACE = 'face'
    TORSO = 'torso'
    ARM_L = 'arm_l'
    ARM_R = 'arm_R'
    LEG_L = 'leg_l'
    LEG_R = 'leg_R'


class MMDBindType(Enum):
    NONE = 0
    COPY_POSE = 1
    COPY_PARENT = 2
    COPY_LOCAL = 3
    COPY_SPINE = 4
    COPY_TOE = 5
    COPY_EYE = 6
    COPY_ROOT = 7
    COPY_LEG_D = 8


@dataclass
class MMDBindInfo:
    bone_info: MMDBoneInfo

    pose_bone_name: Optional[str]
    bind_bone_name: Optional[str]

    group_type: GroupType
    bind_type: MMDBindType


@dataclass
class DataPath:
    bone_name: str
    prop_name: str

    @property
    def bone_data_path(self) -> str:
        return f'["{self.bone_name}"]'

    @property
    def prop_data_path(self) -> str:
        return f'["{self.prop_name}"]'

    @property
    def data_path(self) -> str:
        return f'["{self.bone_name}"]["{self.prop_name}"]'


class ControlType(Enum):
    EYE_MMD_UUUNYAA = 'eye_mmd_uuunyaa'
    BIND_MMD_UUUNYAA = 'bind_mmd_uuunyaa'
    LEG_L_MMD_UUUNYAA = 'leg_l_mmd_uuunyaa'
    LEG_R_MMD_UUUNYAA = 'leg_r_mmd_uuunyaa'
    TOE_L_MMD_UUUNYAA = 'toe_l_mmd_uuunyaa'
    TOE_R_MMD_UUUNYAA = 'toe_r_mmd_uuunyaa'
    TORSO_NECK_FOLLOW = 'torso_neck_follow'
    TORSO_HEAD_FOLLOW = 'torso_head_follow'
    ARM_L_IK_FK = 'arm_l_ik_fk'
    ARM_R_IK_FK = 'arm_r_ik_fk'
    ARM_L_IK_STRETCH = 'arm_l_ik_stretch'
    ARM_R_IK_STRETCH = 'arm_r_ik_stretch'
    ARM_L_IK_PARENT = 'arm_l_ik_parent'
    ARM_R_IK_PARENT = 'arm_r_ik_parent'
    ARM_L_POLE_VECTOR = 'arm_l_pole_vector'
    ARM_R_POLE_VECTOR = 'arm_r_pole_vector'
    LEG_L_IK_FK = 'leg_l_ik_fk'
    LEG_R_IK_FK = 'leg_r_ik_fk'
    LEG_L_IK_STRETCH = 'leg_l_ik_stretch'
    LEG_R_IK_STRETCH = 'leg_r_ik_stretch'
    LEG_L_IK_PARENT = 'leg_l_ik_parent'
    LEG_R_IK_PARENT = 'leg_r_ik_parent'
    LEG_L_POLE_VECTOR = 'leg_l_pole_vector'
    LEG_R_POLE_VECTOR = 'leg_r_pole_vector'
    LEG_L_POLE_PARENT = 'leg_l_pole_parent'
    LEG_R_POLE_PARENT = 'leg_r_pole_parent'


class MMDBindArmatureObjectABC(ArmatureEditor, PoseBoneEditor):
    # pylint: disable=too-many-public-methods
    datapaths: Dict[str, DataPath]
    mmd_bind_infos: List[MMDBindInfo]

    def create_props(self, prop_storage_bone: bpy.types.PoseBone):
        for control_type in [
            ControlType.BIND_MMD_UUUNYAA, ControlType.EYE_MMD_UUUNYAA,
            ControlType.LEG_L_MMD_UUUNYAA, ControlType.LEG_R_MMD_UUUNYAA,
            ControlType.TOE_L_MMD_UUUNYAA, ControlType.TOE_R_MMD_UUUNYAA
        ]:
            data_path = self.datapaths.get(control_type)
            if data_path is None:
                continue

            self.add_prop(prop_storage_bone, data_path.prop_name)

    def assign_mmd_bone_names(self, mmd2pose_bone_name_overrides: Optional[Dict[str, str]] = None):
        pose_bones = self.pose_bones
        mmd_bone_name2pose_bone_names = {b.bone_info.mmd_bone_name: b.pose_bone_name for b in self.mmd_bind_infos}

        if mmd2pose_bone_name_overrides is not None:
            mmd_bone_name2pose_bone_names.update(mmd2pose_bone_name_overrides)

        # clear mmd pose bone names
        for pose_bone in pose_bones:
            if pose_bone.mmd_bone.name_j not in mmd_bone_name2pose_bone_names:
                continue
            pose_bone.mmd_bone.name_j = ''

        for mmd_bone_name, pose_bone_name in mmd_bone_name2pose_bone_names.items():
            if pose_bone_name is None:
                continue

            if pose_bone_name not in pose_bones:
                continue

            pose_bones[pose_bone_name].mmd_bone.name_j = mmd_bone_name

    @abstractmethod
    def has_face_bones(self) -> bool:
        pass

    def _add_eye_constraints(
        self,
        target_eye_l_bone: bpy.types.PoseBone, target_eye_r_bone: bpy.types.PoseBone,
        control_eye_l_bone: bpy.types.PoseBone, control_eye_r_bone: bpy.types.PoseBone,
        control_eyes_bone: bpy.types.PoseBone
    ):
        eye_mmd_uuunyaa_data_path = f'pose.bones{self.datapaths[ControlType.EYE_MMD_UUUNYAA].data_path}'
        self.add_copy_rotation_constraint(target_eye_l_bone, self.raw_object, control_eye_l_bone.name, 'LOCAL', eye_mmd_uuunyaa_data_path, invert_influence=True)
        self.add_copy_rotation_constraint(target_eye_r_bone, self.raw_object, control_eye_r_bone.name, 'LOCAL', eye_mmd_uuunyaa_data_path, invert_influence=True)
        self.add_copy_rotation_constraint(control_eye_l_bone, self.raw_object, control_eyes_bone.name, 'LOCAL', eye_mmd_uuunyaa_data_path, invert_influence=True, mix_mode='ADD')
        self.add_copy_rotation_constraint(control_eye_r_bone, self.raw_object, control_eyes_bone.name, 'LOCAL', eye_mmd_uuunyaa_data_path, invert_influence=True, mix_mode='ADD')

    def _get_property(self, control_type: ControlType):
        datapath = self.datapaths.get(control_type)
        if datapath is None:
            return None
        return self.pose_bones[datapath.bone_name][datapath.prop_name]

    def _set_property(self, control_type: ControlType, value):
        datapath = self.datapaths.get(control_type)
        if datapath is None:
            return
        self.pose_bones[datapath.bone_name][datapath.prop_name] = value

    ######################
    # generated methods

    @property
    def torso_neck_follow(self):
        return self._get_property(ControlType.TORSO_NECK_FOLLOW)

    @torso_neck_follow.setter
    def torso_neck_follow(self, value):
        self._set_property(ControlType.TORSO_NECK_FOLLOW, value)

    @property
    def torso_head_follow(self):
        return self._get_property(ControlType.TORSO_HEAD_FOLLOW)

    @torso_head_follow.setter
    def torso_head_follow(self, value):
        self._set_property(ControlType.TORSO_HEAD_FOLLOW, value)

    @property
    def arm_l_ik_fk(self):
        return self._get_property(ControlType.ARM_L_IK_FK)

    @arm_l_ik_fk.setter
    def arm_l_ik_fk(self, value):
        self._set_property(ControlType.ARM_L_IK_FK, value)

    @property
    def arm_r_ik_fk(self):
        return self._get_property(ControlType.ARM_R_IK_FK)

    @arm_r_ik_fk.setter
    def arm_r_ik_fk(self, value):
        self._set_property(ControlType.ARM_R_IK_FK, value)

    @property
    def arm_l_ik_stretch(self):
        return self._get_property(ControlType.ARM_L_IK_STRETCH)

    @arm_l_ik_stretch.setter
    def arm_l_ik_stretch(self, value):
        self._set_property(ControlType.ARM_L_IK_STRETCH, value)

    @property
    def arm_r_ik_stretch(self):
        return self._get_property(ControlType.ARM_R_IK_STRETCH)

    @arm_r_ik_stretch.setter
    def arm_r_ik_stretch(self, value):
        self._set_property(ControlType.ARM_R_IK_STRETCH, value)

    @property
    def arm_l_ik_parent(self):
        return self._get_property(ControlType.ARM_L_IK_PARENT)

    @arm_l_ik_parent.setter
    def arm_l_ik_parent(self, value):
        self._set_property(ControlType.ARM_L_IK_PARENT, value)

    @property
    def arm_r_ik_parent(self):
        return self._get_property(ControlType.ARM_R_IK_PARENT)

    @arm_r_ik_parent.setter
    def arm_r_ik_parent(self, value):
        self._set_property(ControlType.ARM_R_IK_PARENT, value)

    @property
    def arm_l_pole_vector(self):
        return self._get_property(ControlType.ARM_L_POLE_VECTOR)

    @arm_l_pole_vector.setter
    def arm_l_pole_vector(self, value):
        self._set_property(ControlType.ARM_L_POLE_VECTOR, value)

    @property
    def arm_r_pole_vector(self):
        return self._get_property(ControlType.ARM_R_POLE_VECTOR)

    @arm_r_pole_vector.setter
    def arm_r_pole_vector(self, value):
        self._set_property(ControlType.ARM_R_POLE_VECTOR, value)

    @property
    def leg_l_ik_fk(self):
        return self._get_property(ControlType.LEG_L_IK_FK)

    @leg_l_ik_fk.setter
    def leg_l_ik_fk(self, value):
        self._set_property(ControlType.LEG_L_IK_FK, value)

    @property
    def leg_r_ik_fk(self):
        return self._get_property(ControlType.LEG_R_IK_FK)

    @leg_r_ik_fk.setter
    def leg_r_ik_fk(self, value):
        self._set_property(ControlType.LEG_R_IK_FK, value)

    @property
    def leg_l_ik_stretch(self):
        return self._get_property(ControlType.LEG_L_IK_STRETCH)

    @leg_l_ik_stretch.setter
    def leg_l_ik_stretch(self, value):
        self._set_property(ControlType.LEG_L_IK_STRETCH, value)

    @property
    def leg_r_ik_stretch(self):
        return self._get_property(ControlType.LEG_R_IK_STRETCH)

    @leg_r_ik_stretch.setter
    def leg_r_ik_stretch(self, value):
        self._set_property(ControlType.LEG_R_IK_STRETCH, value)

    @property
    def leg_l_ik_parent(self):
        return self._get_property(ControlType.LEG_L_IK_PARENT)

    @leg_l_ik_parent.setter
    def leg_l_ik_parent(self, value):
        self._set_property(ControlType.LEG_L_IK_PARENT, value)

    @property
    def leg_r_ik_parent(self):
        return self._get_property(ControlType.LEG_R_IK_PARENT)

    @leg_r_ik_parent.setter
    def leg_r_ik_parent(self, value):
        self._set_property(ControlType.LEG_R_IK_PARENT, value)

    @property
    def leg_l_pole_vector(self):
        return self._get_property(ControlType.LEG_L_POLE_VECTOR)

    @leg_l_pole_vector.setter
    def leg_l_pole_vector(self, value):
        self._set_property(ControlType.LEG_L_POLE_VECTOR, value)

    @property
    def leg_r_pole_vector(self):
        return self._get_property(ControlType.LEG_R_POLE_VECTOR)

    @leg_r_pole_vector.setter
    def leg_r_pole_vector(self, value):
        self._set_property(ControlType.LEG_R_POLE_VECTOR, value)

    @property
    def leg_l_pole_parent(self):
        return self._get_property(ControlType.LEG_L_POLE_PARENT)

    @leg_l_pole_parent.setter
    def leg_l_pole_parent(self, value):
        self._set_property(ControlType.LEG_L_POLE_PARENT, value)

    @property
    def leg_r_pole_parent(self):
        return self._get_property(ControlType.LEG_R_POLE_PARENT)

    @leg_r_pole_parent.setter
    def leg_r_pole_parent(self, value):
        self._set_property(ControlType.LEG_R_POLE_PARENT, value)
