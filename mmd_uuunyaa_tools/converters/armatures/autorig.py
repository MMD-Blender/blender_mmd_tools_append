# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import math
from typing import Dict, Iterable, Tuple

import bpy
from mathutils import Euler, Matrix, Vector
from ...converters.armatures.mmd import (MMDArmatureObject,
                                                        MMDBoneInfo)
from ...converters.armatures.mmd_bind import (
    ControlType, DataPath, GroupType, MMDBindArmatureObjectABC, MMDBindInfo,
    MMDBindType)


class AutoRigArmatureObject(MMDBindArmatureObjectABC):
    # pylint: disable=too-many-instance-attributes
    prop_storage_bone_name = 'c_root_master.x'
    prop_name_mmd_uuunyaa_bind_mmd_autorig = 'mmd_uuunyaa_bind_mmd_autorig'

    mmd_bind_infos = [
        MMDBindInfo(MMDBoneInfo.全ての親, 'c_pos', 'c_pos', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.センター, 'c_traj', 'c_traj', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.グルーブ, 'groove', 'groove', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.腰, 'c_root_master.x', '	c_root_master.x', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.上半身, 'c_spine_01.x', 'spine_01.x', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.上半身1, None, None, GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.上半身2, 'c_spine_02.x', 'spine_02.x', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.首, 'c_neck.x', 'neck.x', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.頭, 'c_head.x', 'head.x', GroupType.TORSO, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.両目, 'mmd_uuunyaa_eyes_fk', 'mmd_uuunyaa_eyes_fk', GroupType.FACE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左目, 'mmd_uuunyaa_eye_fk.l', 'c_eye.l', GroupType.FACE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右目, 'mmd_uuunyaa_eye_fk.r', 'c_eye.r', GroupType.FACE, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.左肩, 'c_shoulder.l', 'shoulder.l', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左腕, 'c_arm_fk.l', 'arm.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左腕捩, 'mmd_uuunyaa_upper_arm_twist_fk.l', None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左ひじ, 'c_forearm_fk.l', 'forearm.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左手捩, 'mmd_uuunyaa_wrist_twist_fk.l', None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左手首, 'c_hand_fk.l', 'hand.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左親指０, 'c_thumb1.l', 'thumb1.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左親指１, 'c_thumb2.l', 'thumb2.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左親指２, 'c_thumb3.l', 'thumb3.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左人指０, None, None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左人指１, 'c_index1.l', 'index1.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左人指２, 'c_index2.l', 'index2.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左人指３, 'c_index3.l', 'index3.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左中指０, None, None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左中指１, 'c_middle1.l', 'middle1.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左中指２, 'c_middle2.l', 'middle2.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左中指３, 'c_middle3.l', 'middle3.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左薬指０, None, None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左薬指１, 'c_ring1.l', 'ring1.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左薬指２, 'c_ring2.l', 'ring2.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左薬指３, 'c_ring3.l', 'ring3.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左小指０, None, None, GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左小指１, 'c_pinky1.l', 'pinky1.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左小指２, 'c_pinky2.l', 'pinky2.l', GroupType.ARM_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左小指３, 'c_pinky3.l', 'pinky3.l', GroupType.ARM_L, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.右肩, 'c_shoulder.r', 'shoulder.r', GroupType.TORSO, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右腕, 'c_arm_fk.r', 'arm.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右腕捩, 'mmd_uuunyaa_upper_arm_twist_fk.r', None, GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右ひじ, 'c_forearm_fk.r', 'forearm.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右手捩, 'mmd_uuunyaa_wrist_twist_fk.r', None, GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右手首, 'c_hand_fk.r', 'hand.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右親指０, 'c_thumb1.r', 'thumb1.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右親指１, 'c_thumb2.r', 'thumb2.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右親指２, 'c_thumb3.r', 'thumb3.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右人指０, None, None, GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右人指１, 'c_index1.r', 'index1.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右人指２, 'c_index2.r', 'index2.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右人指３, 'c_index3.r', 'index3.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右中指０, None, None, GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右中指１, 'c_middle1.r', 'middle1.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右中指２, 'c_middle2.r', 'middle2.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右中指３, 'c_middle3.r', 'middle3.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右薬指０, None, None, GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右薬指１, 'c_ring1.r', 'ring1.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右薬指２, 'c_ring2.r', 'ring2.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右薬指３, 'c_ring3.r', 'ring3.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右小指０, None, None, GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右小指１, 'c_pinky1.r', 'pinky1.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右小指２, 'c_pinky2.r', 'pinky2.r', GroupType.ARM_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右小指３, 'c_pinky3.r', 'pinky3.r', GroupType.ARM_R, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.下半身, 'c_root.x', 'root.x', GroupType.TORSO, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.左足, 'c_thigh_ik.l', 'thigh.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左ひざ, 'c_leg_fk.l', 'leg.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左足首, 'c_foot_fk.l', 'foot.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左足ＩＫ, 'c_foot_ik.l', 'c_foot_ik.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左足先EX, 'c_toes_ik.l', 'toes_01.l', GroupType.LEG_L, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.右足, 'c_thigh_ik.r', 'thigh.r', GroupType.LEG_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右ひざ, 'c_leg_fk.r', 'leg.r', GroupType.LEG_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右足首, 'c_foot_fk.r', 'foot.r', GroupType.LEG_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右足ＩＫ, 'c_foot_ik.r', 'c_foot_ik.r', GroupType.LEG_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右足先EX, 'c_toes_ik.r', 'toes_01.r', GroupType.LEG_R, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.左つま先ＩＫ, 'mmd_uuunyaa_toe_ik.l', 'mmd_uuunyaa_toe_ik.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右つま先ＩＫ, 'mmd_uuunyaa_toe_ik.r', 'mmd_uuunyaa_toe_ik.r', GroupType.LEG_R, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左つま先, None, None, GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右つま先, None, None, GroupType.LEG_R, MMDBindType.NONE),

        MMDBindInfo(MMDBoneInfo.左肩C, 'mmd_uuunyaa_shoulder_cancel.l', 'mmd_uuunyaa_shoulder_cancel.l', GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左肩P, 'mmd_uuunyaa_shoulder_parent.l', 'mmd_uuunyaa_shoulder_parent.l', GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右肩C, 'mmd_uuunyaa_shoulder_cancel.r', 'mmd_uuunyaa_shoulder_cancel.r', GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右肩P, 'mmd_uuunyaa_shoulder_parent.r', 'mmd_uuunyaa_shoulder_parent.r', GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左ダミー, None, None, GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右ダミー, None, None, GroupType.NONE, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.左足IK親, 'mmd_uuunyaa_leg_ik_parent.l', 'mmd_uuunyaa_leg_ik_parent.l', GroupType.LEG_L, MMDBindType.NONE),
        MMDBindInfo(MMDBoneInfo.右足IK親, 'mmd_uuunyaa_leg_ik_parent.r', 'mmd_uuunyaa_leg_ik_parent.r', GroupType.LEG_R, MMDBindType.NONE),
    ]

    @staticmethod
    def is_autorig_armature_object(obj: bpy.types.Object):
        if obj is None:
            return False

        if obj.type != 'ARMATURE':
            return False

        arp_updated = obj.data.get('arp_updated')
        if not arp_updated:
            return False

        return True

    def __init__(self, rigify_armature_object: bpy.types.Object):
        super().__init__(rigify_armature_object)

        control_types = {
            (True, False, 'L', 'ik_fk_switch'): ControlType.ARM_L_IK_FK,
            (True, False, 'R', 'ik_fk_switch'): ControlType.ARM_R_IK_FK,
            (True, False, 'L', 'auto_stretch'): ControlType.ARM_L_IK_STRETCH,
            (True, False, 'R', 'auto_stretch'): ControlType.ARM_R_IK_STRETCH,
            (True, False, 'L', 'pole_vector'): ControlType.ARM_L_POLE_VECTOR,
            (True, False, 'R', 'pole_vector'): ControlType.ARM_R_POLE_VECTOR,
            (False, True, 'L', 'ik_fk_switch'): ControlType.LEG_L_IK_FK,
            (False, True, 'R', 'ik_fk_switch'): ControlType.LEG_R_IK_FK,
            (False, True, 'L', 'auto_stretch'): ControlType.LEG_L_IK_STRETCH,
            (False, True, 'R', 'auto_stretch'): ControlType.LEG_R_IK_STRETCH,
            (False, True, 'L', 'pole_vector'): ControlType.LEG_L_POLE_VECTOR,
            (False, True, 'R', 'pole_vector'): ControlType.LEG_R_POLE_VECTOR,
            (False, True, 'L', 'pole_parent'): ControlType.LEG_L_POLE_PARENT,
            (False, True, 'R', 'pole_parent'): ControlType.LEG_R_POLE_PARENT,
        }

        datapaths: Dict[ControlType, DataPath] = {
            ControlType.BIND_MMD_UUUNYAA: DataPath(self.prop_storage_bone_name, self.prop_name_mmd_uuunyaa_bind_mmd_autorig),
            ControlType.EYE_MMD_UUUNYAA: DataPath(self.prop_storage_bone_name, 'mmd_uuunyaa_eye_mmd_autorig'),
            ControlType.LEG_L_MMD_UUUNYAA: DataPath(self.prop_storage_bone_name, 'mmd_uuunyaa_leg_l_mmd_autorig'),
            ControlType.LEG_R_MMD_UUUNYAA: DataPath(self.prop_storage_bone_name, 'mmd_uuunyaa_leg_r_mmd_autorig'),
            ControlType.TORSO_HEAD_FOLLOW: DataPath('c_head.x', 'head_free'),
        }

        pose_bones = self.pose_bones
        for pose_bone in pose_bones:
            bone_name = pose_bone.name

            is_arm_bone_name = 'c_hand_ik' in bone_name
            is_leg_bone_name = 'c_foot_ik' in bone_name
            bone_suffix = self.to_bone_suffix(bone_name)

            for key in pose_bone.keys():
                if key in {'ik_fk_switch', 'auto_stretch', 'pole_vector', 'pole_parent'}:
                    prop_name = key
                else:
                    continue

                control_type = control_types.get((is_arm_bone_name, is_leg_bone_name, bone_suffix, prop_name))
                if control_type is None:
                    continue

                datapaths[control_type] = DataPath(bone_name, key)

        self.datapaths = datapaths

    def has_face_bones(self) -> bool:
        require_bone_names = {'head.x', 'c_skull_02.x', 'c_eye.l', 'c_eye.r', 'c_eye_offset.l', 'c_eye_offset.r'}
        return len(require_bone_names - set(self.bones.keys())) == 0

    @property
    def eye_mmd_autorig(self):
        return self._get_property(ControlType.EYE_MMD_UUUNYAA)

    @eye_mmd_autorig.setter
    def eye_mmd_autorig(self, value):
        self._set_property(ControlType.EYE_MMD_UUUNYAA, value)

    @property
    def leg_l_mmd_autorig(self):
        return self._get_property(ControlType.LEG_L_MMD_UUUNYAA)

    @leg_l_mmd_autorig.setter
    def leg_l_mmd_autorig(self, value):
        self._set_property(ControlType.LEG_L_MMD_UUUNYAA, value)

    @property
    def leg_r_mmd_autorig(self):
        return self._get_property(ControlType.LEG_R_MMD_UUUNYAA)

    @leg_r_mmd_autorig.setter
    def leg_r_mmd_autorig(self, value):
        self._set_property(ControlType.LEG_R_MMD_UUUNYAA, value)

    def _add_upper_arm_twist_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        # add upper arm twist (腕捩)
        upper_arm_twist_fk_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_upper_arm_twist_fk.l')
        upper_arm_twist_fk_l_bone.layers = [i in {11} for i in range(32)]
        upper_arm_twist_fk_l_bone.head = rig_edit_bones['c_arm_fk.l'].tail - rig_edit_bones['c_arm_fk.l'].vector / 3
        upper_arm_twist_fk_l_bone.tail = rig_edit_bones['c_arm_fk.l'].tail
        upper_arm_twist_fk_l_bone.parent = rig_edit_bones['c_arm_fk.l']
        self.fit_edit_bone_rotation(upper_arm_twist_fk_l_bone, rig_edit_bones['c_arm_fk.l'])
        rig_edit_bones['c_forearm_fk.l'].use_connect = False
        rig_edit_bones['c_forearm_fk.l'].parent = upper_arm_twist_fk_l_bone

        upper_arm_twist_fk_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_upper_arm_twist_fk.r')
        upper_arm_twist_fk_r_bone.layers = [i in {11} for i in range(32)]
        upper_arm_twist_fk_r_bone.head = rig_edit_bones['c_arm_fk.r'].tail - rig_edit_bones['c_arm_fk.r'].vector / 3
        upper_arm_twist_fk_r_bone.tail = rig_edit_bones['c_arm_fk.r'].tail
        upper_arm_twist_fk_r_bone.parent = rig_edit_bones['c_arm_fk.r']
        self.fit_edit_bone_rotation(upper_arm_twist_fk_r_bone, rig_edit_bones['c_arm_fk.r'])
        rig_edit_bones['c_forearm_fk.r'].use_connect = False
        rig_edit_bones['c_forearm_fk.r'].parent = upper_arm_twist_fk_r_bone

        return upper_arm_twist_fk_l_bone, upper_arm_twist_fk_r_bone

    def _add_wrist_twist_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        # add wrist twist (手捩)
        wrist_twist_fk_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_wrist_twist_fk.l')
        wrist_twist_fk_l_bone.layers = [i in {11} for i in range(32)]
        wrist_twist_fk_l_bone.head = rig_edit_bones['c_forearm_fk.l'].tail - rig_edit_bones['c_forearm_fk.l'].vector / 3
        wrist_twist_fk_l_bone.tail = rig_edit_bones['c_forearm_fk.l'].tail
        wrist_twist_fk_l_bone.parent = rig_edit_bones['c_forearm_fk.l']
        self.fit_edit_bone_rotation(wrist_twist_fk_l_bone, rig_edit_bones['c_forearm_fk.l'])
        rig_edit_bones['c_hand_fk.l'].use_connect = False
        rig_edit_bones['c_hand_fk.l'].parent = wrist_twist_fk_l_bone

        wrist_twist_fk_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_wrist_twist_fk.r')
        wrist_twist_fk_r_bone.layers = [i in {11} for i in range(32)]
        wrist_twist_fk_r_bone.head = rig_edit_bones['c_forearm_fk.r'].tail - rig_edit_bones['c_forearm_fk.r'].vector / 3
        wrist_twist_fk_r_bone.tail = rig_edit_bones['c_forearm_fk.r'].tail
        wrist_twist_fk_r_bone.parent = rig_edit_bones['c_forearm_fk.r']
        self.fit_edit_bone_rotation(wrist_twist_fk_r_bone, rig_edit_bones['c_forearm_fk.r'])
        rig_edit_bones['c_hand_fk.r'].use_connect = False
        rig_edit_bones['c_hand_fk.r'].parent = wrist_twist_fk_r_bone

        return wrist_twist_fk_l_bone, wrist_twist_fk_r_bone

    def _add_leg_ik_parent_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        # add Leg IKP (足IK親) bones
        leg_ik_parent_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_leg_ik_parent.l')
        leg_ik_parent_l_bone.layers = [i in {1} for i in range(32)]
        leg_ik_parent_l_bone.tail = rig_edit_bones['foot.l'].head
        leg_ik_parent_l_bone.head = leg_ik_parent_l_bone.tail.copy()
        leg_ik_parent_l_bone.head.z = rig_edit_bones['foot.l'].tail.z
        leg_ik_parent_l_bone.roll = 0

        leg_ik_parent_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_leg_ik_parent.r')
        leg_ik_parent_r_bone.layers = [i in {1} for i in range(32)]
        leg_ik_parent_r_bone.tail = rig_edit_bones['foot.r'].head
        leg_ik_parent_r_bone.head = leg_ik_parent_r_bone.tail.copy()
        leg_ik_parent_r_bone.head.z = rig_edit_bones['foot.r'].tail.z
        leg_ik_parent_r_bone.roll = 0

        leg_ik_parent_l_bone.parent = rig_edit_bones['c_pos']
        rig_edit_bones['c_foot_ik.l'].parent = leg_ik_parent_l_bone

        leg_ik_parent_r_bone.parent = rig_edit_bones['c_pos']
        rig_edit_bones['c_foot_ik.r'].parent = leg_ik_parent_r_bone

        #

        rig_edit_bones['c_leg_pole.l'].roll = 0
        rig_edit_bones['c_leg_pole.r'].roll = 0

        return leg_ik_parent_l_bone, leg_ik_parent_r_bone

    def _add_toe_ik_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        # add toe IK (つま先ＩＫ)
        toe_ik_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_toe_ik.l')
        toe_ik_l_bone.layers = [i in {1} for i in range(32)]
        toe_ik_l_bone.head = rig_edit_bones['foot.l'].tail
        toe_ik_l_bone.tail = toe_ik_l_bone.head - Vector([0, 0, rig_edit_bones['mmd_uuunyaa_leg_ik_parent.l'].length])
        toe_ik_l_bone.parent = rig_edit_bones['c_foot_ik.l']
        self.fit_edit_bone_rotation(toe_ik_l_bone, rig_edit_bones['c_foot_ik.l'])

        toe_ik_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_toe_ik.r')
        toe_ik_r_bone.layers = [i in {1} for i in range(32)]
        toe_ik_r_bone.head = rig_edit_bones['foot.r'].tail
        toe_ik_r_bone.tail = toe_ik_r_bone.head - Vector([0, 0, rig_edit_bones['mmd_uuunyaa_leg_ik_parent.r'].length])
        toe_ik_r_bone.parent = rig_edit_bones['c_foot_ik.r']
        self.fit_edit_bone_rotation(toe_ik_r_bone, rig_edit_bones['c_foot_ik.r'])

        return toe_ik_l_bone, toe_ik_r_bone

    def _add_eye_fk_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone, bpy.types.EditBone]:
        rig_eyes_fk_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_eyes_fk')
        rig_eyes_fk_bone.head = rig_edit_bones['head.x'].tail + rig_edit_bones['head.x'].vector
        rig_eyes_fk_bone.head.y = rig_edit_bones['c_eye.l'].head.y
        rig_eyes_fk_bone.tail = rig_eyes_fk_bone.head - Vector([0, rig_edit_bones['c_eye.l'].length * 2, 0])
        rig_eyes_fk_bone.layers = [i in {0} for i in range(32)]
        rig_eyes_fk_bone.parent = rig_edit_bones['c_skull_02.x']
        self.fit_edit_bone_rotation(rig_eyes_fk_bone, rig_edit_bones['c_eye.l'])

        rig_eye_fk_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_eye_fk.l')
        rig_eye_fk_l_bone.head = rig_edit_bones['c_eye.l'].head
        rig_eye_fk_l_bone.tail = rig_edit_bones['c_eye.l'].tail
        rig_eye_fk_l_bone.layers = [i in {0} for i in range(32)]
        rig_eye_fk_l_bone.parent = rig_edit_bones['c_eye_offset.l']
        self.fit_edit_bone_rotation(rig_eye_fk_l_bone, rig_edit_bones['c_eye.l'])

        rig_eye_fk_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_eye_fk.r')
        rig_eye_fk_r_bone.head = rig_edit_bones['c_eye.r'].head
        rig_eye_fk_r_bone.tail = rig_edit_bones['c_eye.r'].tail
        rig_eye_fk_r_bone.layers = [i in {0} for i in range(32)]
        rig_eye_fk_r_bone.parent = rig_edit_bones['c_eye_offset.r']
        self.fit_edit_bone_rotation(rig_eye_fk_r_bone, rig_edit_bones['c_eye.r'])

        return rig_eye_fk_l_bone, rig_eye_fk_r_bone, rig_eyes_fk_bone

    def _adjust_torso_bone(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> bpy.types.EditBone:
        thigh_center = self.to_center(rig_edit_bones['thigh.l'].head, rig_edit_bones['thigh.r'].head)
        length = rig_edit_bones['root.x'].length / 2
        rig_edit_bones['c_root_master.x'].head = Vector([0, rig_edit_bones['root.x'].head.y + length, thigh_center.z + length])
        rig_edit_bones['c_root_master.x'].tail = rig_edit_bones['root.x'].head
        rig_edit_bones['c_root_master.x'].roll = 0

        return rig_edit_bones['c_root_master.x']

    def _add_root_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        # add center (センター) bone
        center_bone = self.get_or_create_bone(rig_edit_bones, 'c_traj')

        # add groove (グルーブ) bone
        groove_bone = self.get_or_create_bone(rig_edit_bones, 'groove')
        groove_bone.layers = [i in {1} for i in range(32)]
        groove_bone.head = center_bone.head
        groove_bone.tail = groove_bone.head + Vector([0.0, 0.0, center_bone.length])
        groove_bone.roll = 0

        return center_bone, groove_bone

    def _add_shoulder_parent_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        shoulder_parent_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_parent.l')
        shoulder_parent_l_bone.head = rig_edit_bones['c_shoulder.l'].head
        shoulder_parent_l_bone.tail = shoulder_parent_l_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.l'].length/2])
        shoulder_parent_l_bone.layers = [i in {0} for i in range(32)]
        shoulder_parent_l_bone.parent = rig_edit_bones['c_spine_02.x']
        shoulder_parent_l_bone.roll = 0

        rig_edit_bones['c_shoulder.l'].parent = shoulder_parent_l_bone

        shoulder_parent_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_parent.r')
        shoulder_parent_r_bone.head = rig_edit_bones['c_shoulder.r'].head
        shoulder_parent_r_bone.tail = shoulder_parent_r_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.r'].length/2])
        shoulder_parent_r_bone.layers = [i in {0} for i in range(32)]
        shoulder_parent_r_bone.parent = rig_edit_bones['c_spine_02.x']
        shoulder_parent_r_bone.roll = 0

        rig_edit_bones['c_shoulder.r'].parent = shoulder_parent_r_bone

        return shoulder_parent_l_bone, shoulder_parent_r_bone

    def _add_shoulder_cancel_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        shoulder_cancel_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel.l')
        shoulder_cancel_l_bone.head = rig_edit_bones['c_shoulder.l'].tail
        shoulder_cancel_l_bone.tail = shoulder_cancel_l_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.l'].length/2])
        shoulder_cancel_l_bone.layers = [i in {1} for i in range(32)]
        shoulder_cancel_l_bone.roll = 0

        shoulder_cancel_l_bone.parent = rig_edit_bones['c_shoulder.l']
        rig_edit_bones['c_arm_fk.l'].parent = shoulder_cancel_l_bone

        shoulder_cancel_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel.r')
        shoulder_cancel_r_bone.head = rig_edit_bones['c_shoulder.r'].tail
        shoulder_cancel_r_bone.tail = shoulder_cancel_r_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.r'].length/2])
        shoulder_cancel_r_bone.layers = [i in {1} for i in range(32)]
        shoulder_cancel_r_bone.roll = 0

        shoulder_cancel_r_bone.parent = rig_edit_bones['c_shoulder.r']
        rig_edit_bones['c_arm_fk.r'].parent = rig_edit_bones['c_shoulder.r']

        return shoulder_cancel_l_bone, shoulder_cancel_r_bone

    def _add_shoulder_cancel_dummy_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        shoulder_cancel_dummy_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel_dummy.l')
        shoulder_cancel_dummy_l_bone.head = rig_edit_bones['c_shoulder.l'].head
        shoulder_cancel_dummy_l_bone.tail = shoulder_cancel_dummy_l_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.l'].length/2])
        shoulder_cancel_dummy_l_bone.layers = [i in {2} for i in range(32)]
        shoulder_cancel_dummy_l_bone.parent = rig_edit_bones['mmd_uuunyaa_shoulder_parent.l']
        shoulder_cancel_dummy_l_bone.roll = 0

        shoulder_cancel_dummy_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel_dummy.r')
        shoulder_cancel_dummy_r_bone.head = rig_edit_bones['c_shoulder.r'].head
        shoulder_cancel_dummy_r_bone.tail = shoulder_cancel_dummy_r_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.r'].length/2])
        shoulder_cancel_dummy_r_bone.layers = [i in {2} for i in range(32)]
        shoulder_cancel_dummy_r_bone.parent = rig_edit_bones['mmd_uuunyaa_shoulder_parent.r']
        shoulder_cancel_dummy_r_bone.roll = 0

        return shoulder_cancel_dummy_l_bone, shoulder_cancel_dummy_r_bone

    def _add_shoulder_cancel_shadow_bones(self, rig_edit_bones: bpy.types.ArmatureEditBones) -> Tuple[bpy.types.EditBone, bpy.types.EditBone]:
        shoulder_cancel_shadow_l_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel_shadow.l')
        shoulder_cancel_shadow_l_bone.head = rig_edit_bones['c_shoulder.l'].head
        shoulder_cancel_shadow_l_bone.tail = shoulder_cancel_shadow_l_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.l'].length/2])
        shoulder_cancel_shadow_l_bone.layers = [i in {2} for i in range(32)]
        shoulder_cancel_shadow_l_bone.parent = rig_edit_bones['c_spine_02.x']
        shoulder_cancel_shadow_l_bone.roll = 0

        shoulder_cancel_shadow_r_bone = self.get_or_create_bone(rig_edit_bones, 'mmd_uuunyaa_shoulder_cancel_shadow.r')
        shoulder_cancel_shadow_r_bone.head = rig_edit_bones['c_shoulder.r'].head
        shoulder_cancel_shadow_r_bone.tail = shoulder_cancel_shadow_r_bone.head + Vector([0, 0, rig_edit_bones['c_shoulder.r'].length/2])
        shoulder_cancel_shadow_r_bone.layers = [i in {2} for i in range(32)]
        shoulder_cancel_shadow_r_bone.parent = rig_edit_bones['c_spine_02.x']
        shoulder_cancel_shadow_r_bone.roll = 0

        return shoulder_cancel_shadow_l_bone, shoulder_cancel_shadow_r_bone

    def imitate_mmd_bone_structure(self):
        # pylint: disable=too-many-statements
        rig_edit_bones = self.edit_bones

        # add center (センター) groove (グルーブ) bone
        center_bone, groove_bone = self._add_root_bones(rig_edit_bones)

        # set spine parent-child relationship
        self.insert_edit_bone(groove_bone, center_bone)

        self._add_shoulder_parent_bones(rig_edit_bones)
        self._add_shoulder_cancel_bones(rig_edit_bones)
        self._add_shoulder_cancel_dummy_bones(rig_edit_bones)
        self._add_shoulder_cancel_shadow_bones(rig_edit_bones)

        self._add_upper_arm_twist_bones(rig_edit_bones)

        self._add_wrist_twist_bones(rig_edit_bones)

        self._add_leg_ik_parent_bones(rig_edit_bones)

        self._add_toe_ik_bones(rig_edit_bones)

        # adjust torso bone
        self._adjust_torso_bone(rig_edit_bones)

        # set face bones
        if not self.has_face_bones():
            # There are not enough bones for the setup.
            return

        self._add_eye_fk_bones(rig_edit_bones)

    def imitate_mmd_pose_behavior(self):
        """Imitate the behavior of MMD armature as much as possible."""
        # pylint: disable=too-many-statements, too-many-locals

        pose_bones: Dict[str, bpy.types.PoseBone] = self.pose_bones

        self.create_props(pose_bones[self.prop_storage_bone_name])
        self.remove_constraints(pose_bones)

        self._imitate_mmd_eye_behavior(pose_bones)

        def list_constraints(pose_bone: bpy.types.PoseBone, constraint_type: str) -> Iterable[bpy.types.Constraint]:
            for constraint in pose_bone.constraints:
                if constraint.type == constraint_type:
                    yield constraint

        def edit_constraints(pose_bone: bpy.types.PoseBone, constraint_type: str, **kwargs):
            for constraint in list_constraints(pose_bone, constraint_type):
                for key, value in kwargs.items():
                    setattr(constraint, key, value)

        def add_constraint(pose_bone: bpy.types.PoseBone, constraint_type: str, name: str, **kwargs):
            constraints = pose_bone.constraints
            constraint = constraints.new(constraint_type)
            constraint.name = name
            for key, value in kwargs.items():
                setattr(constraint, key, value)
            return constraint

        # shoulders
        add_constraint(
            pose_bones['mmd_uuunyaa_shoulder_cancel_shadow.l'],
            'COPY_TRANSFORMS', 'mmd_uuunyaa_transform_shoulder_cancel',
            target=self.raw_object, subtarget='mmd_uuunyaa_shoulder_cancel_dummy.l',
            target_space='POSE', owner_space='POSE'
        )

        add_constraint(
            pose_bones['mmd_uuunyaa_shoulder_cancel_shadow.r'],
            'COPY_TRANSFORMS', 'mmd_uuunyaa_transform_shoulder_cancel',
            target=self.raw_object, subtarget='mmd_uuunyaa_shoulder_cancel_dummy.r',
            target_space='POSE', owner_space='POSE'
        )

        add_constraint(
            pose_bones['mmd_uuunyaa_shoulder_cancel.l'],
            'TRANSFORM', 'mmd_uuunyaa_transform_shoulder_cancel',
            target=self.raw_object, subtarget='mmd_uuunyaa_shoulder_cancel_shadow.l',
            map_from='ROTATION', map_to='ROTATION',
            from_min_x_rot=math.radians(-180), to_min_x_rot=math.radians(+180),
            from_max_x_rot=math.radians(+180), to_max_x_rot=math.radians(-180),
            from_min_y_rot=math.radians(-180), to_min_y_rot=math.radians(+180),
            from_max_y_rot=math.radians(+180), to_max_y_rot=math.radians(-180),
            from_min_z_rot=math.radians(-180), to_min_z_rot=math.radians(+180),
            from_max_z_rot=math.radians(+180), to_max_z_rot=math.radians(-180),
            target_space='LOCAL', owner_space='LOCAL'
        )

        add_constraint(
            pose_bones['mmd_uuunyaa_shoulder_cancel.r'],
            'TRANSFORM', 'mmd_uuunyaa_transform_shoulder_cancel',
            target=self.raw_object, subtarget='mmd_uuunyaa_shoulder_cancel_shadow.r',
            map_from='ROTATION', map_to='ROTATION',
            from_min_x_rot=math.radians(-180), to_min_x_rot=math.radians(+180),
            from_max_x_rot=math.radians(+180), to_max_x_rot=math.radians(-180),
            from_min_y_rot=math.radians(-180), to_min_y_rot=math.radians(+180),
            from_max_y_rot=math.radians(+180), to_max_y_rot=math.radians(-180),
            from_min_z_rot=math.radians(-180), to_min_z_rot=math.radians(+180),
            from_max_z_rot=math.radians(+180), to_max_z_rot=math.radians(-180),
            target_space='LOCAL', owner_space='LOCAL'
        )

        bones = self.bones
        bones['mmd_uuunyaa_shoulder_cancel.l'].hide = True
        bones['mmd_uuunyaa_shoulder_cancel.r'].hide = True

        # arms
        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.l'].lock_location = [True, True, True]
        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.l'].lock_rotation_w = False
        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.l'].lock_rotation = [True, False, True]

        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.r'].lock_location = [True, True, True]
        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.r'].lock_rotation_w = False
        pose_bones['mmd_uuunyaa_upper_arm_twist_fk.r'].lock_rotation = [True, False, True]

        # wrists
        pose_bones['mmd_uuunyaa_wrist_twist_fk.l'].lock_location = [True, True, True]
        pose_bones['mmd_uuunyaa_wrist_twist_fk.l'].lock_rotation_w = False
        pose_bones['mmd_uuunyaa_wrist_twist_fk.l'].lock_rotation = [True, False, True]

        pose_bones['mmd_uuunyaa_wrist_twist_fk.r'].lock_location = [True, True, True]
        pose_bones['mmd_uuunyaa_wrist_twist_fk.r'].lock_rotation_w = False
        pose_bones['mmd_uuunyaa_wrist_twist_fk.r'].lock_rotation = [True, False, True]

        leg_l_mmd_uuunyaa_data_path = f'pose.bones{self.datapaths[ControlType.LEG_L_MMD_UUUNYAA].data_path}'
        leg_r_mmd_uuunyaa_data_path = f'pose.bones{self.datapaths[ControlType.LEG_R_MMD_UUUNYAA].data_path}'

        # legs
        add_constraint(pose_bones['thigh_ik_nostr.l'], 'COPY_ROTATION', 'mmd_uuunyaa_copy_rotation', target=self.raw_object, subtarget='c_thigh_ik.l')
        shin_ik_l_bone = pose_bones['leg_ik_nostr.l']
        for constraint in list_constraints(pose_bones['leg_ik_nostr.l'], 'IK'):
            self.add_influence_driver(constraint, self.raw_object, leg_l_mmd_uuunyaa_data_path)
        self.add_ik_constraint(shin_ik_l_bone, self.raw_object, 'foot_ik_target.l', 2, 200, leg_l_mmd_uuunyaa_data_path, invert_influence=True, use_stretch=False)
        shin_ik_l_bone.use_ik_limit_z = True
        shin_ik_l_bone.ik_min_z = math.radians(0)
        shin_ik_l_bone.ik_max_z = math.radians(180)

        add_constraint(pose_bones['thigh_ik_nostr.r'], 'COPY_ROTATION', 'mmd_uuunyaa_copy_rotation', target=self.raw_object, subtarget='c_thigh_ik.r')
        shin_ik_r_bone = pose_bones['leg_ik_nostr.r']
        for constraint in list_constraints(pose_bones['leg_ik_nostr.r'], 'IK'):
            self.add_influence_driver(constraint, self.raw_object, leg_r_mmd_uuunyaa_data_path)
        self.add_ik_constraint(shin_ik_r_bone, self.raw_object, 'foot_ik_target.r', 2, 200, leg_r_mmd_uuunyaa_data_path, invert_influence=True, use_stretch=False)
        shin_ik_r_bone.use_ik_limit_z = True
        shin_ik_r_bone.ik_min_z = math.radians(-180)
        shin_ik_r_bone.ik_max_z = math.radians(0)

        def add_bone_hide_driver(pose_bone: bpy.types.PoseBone, leg_ik_fk_data_path: str, leg_mmd_uuunyaa_data_path: str):
            pose_bone.bone.driver_remove('hide')
            driver: bpy.types.Driver = pose_bone.bone.driver_add('hide').driver

            leg_ik_fk_variable: bpy.types.DriverVariable = driver.variables.new()
            leg_ik_fk_variable.name = 'mmd_uuunyaa_leg_ik_fk'
            leg_ik_fk_variable.targets[0].id = self.raw_object
            leg_ik_fk_variable.targets[0].data_path = leg_ik_fk_data_path
            leg_mmd_uuunyaa_variable: bpy.types.DriverVariable = driver.variables.new()
            leg_mmd_uuunyaa_variable.name = 'leg_mmd_uuunyaa'
            leg_mmd_uuunyaa_variable.targets[0].id = self.raw_object
            leg_mmd_uuunyaa_variable.targets[0].data_path = leg_mmd_uuunyaa_data_path

            driver.expression = f'(1-{leg_ik_fk_variable.name})*{leg_mmd_uuunyaa_variable.name}'

        leg_l_ik_fk_data_path = f'pose.bones{self.datapaths[ControlType.LEG_L_IK_FK].data_path}'
        leg_r_ik_fk_data_path = f'pose.bones{self.datapaths[ControlType.LEG_R_IK_FK].data_path}'

        add_bone_hide_driver(pose_bones['c_leg_pole.l'], leg_l_ik_fk_data_path, leg_l_mmd_uuunyaa_data_path)
        add_bone_hide_driver(pose_bones['c_leg_pole.r'], leg_r_ik_fk_data_path, leg_r_mmd_uuunyaa_data_path)

        for constraint in list_constraints(pose_bones['c_foot_ik.l'], 'CHILD_OF'):
            self.add_influence_driver(constraint, self.raw_object, leg_l_mmd_uuunyaa_data_path)

        for constraint in list_constraints(pose_bones['c_foot_ik.r'], 'CHILD_OF'):
            self.add_influence_driver(constraint, self.raw_object, leg_r_mmd_uuunyaa_data_path)

        # toe IK
        leg_l_mmd_uuunyaa = self.datapaths[ControlType.LEG_L_MMD_UUUNYAA]
        leg_r_mmd_uuunyaa = self.datapaths[ControlType.LEG_R_MMD_UUUNYAA]
        self.add_ik_constraint(pose_bones['foot.l'], self.raw_object, 'mmd_uuunyaa_toe_ik.l', 1, 3, f'pose.bones{leg_l_mmd_uuunyaa.data_path}', invert_influence=True)
        self.add_ik_constraint(pose_bones['foot.r'], self.raw_object, 'mmd_uuunyaa_toe_ik.r', 1, 3, f'pose.bones{leg_r_mmd_uuunyaa.data_path}', invert_influence=True)

        # toe MMD
        edit_constraints(pose_bones['toes_01.l'], 'COPY_ROTATION', mix_mode='ADD', target_space='LOCAL', owner_space='LOCAL')
        edit_constraints(pose_bones['toes_01.r'], 'COPY_ROTATION', mix_mode='ADD', target_space='LOCAL', owner_space='LOCAL')

        self._set_bone_custom_shapes(pose_bones)

        self.raw_object.show_in_front = True

        # set arms IK and stretch
        self.arm_l_ik_fk = 1.000
        self.arm_r_ik_fk = 1.000
        self.arm_l_ik_stretch = 0.000
        self.arm_r_ik_stretch = 0.000

        # set legs IK and stretch
        self.leg_l_ik_fk = 0.000
        self.leg_r_ik_fk = 0.000
        self.leg_l_ik_stretch = 0.000
        self.leg_r_ik_stretch = 0.000
        self.leg_l_pole_parent = 1  # torso
        self.leg_r_pole_parent = 1  # torso

        # set eye motion mode
        self.eye_mmd_autorig = 0.000  # MMD

        # set leg mode
        self.leg_l_mmd_autorig = 0.000  # MMD
        self.leg_r_mmd_autorig = 0.000  # MMD

        # torso hack
        self.torso_head_follow = 1.000  # follow chest

    def _set_bone_custom_shapes(self, pose_bones: Dict[str, bpy.types.PoseBone]):

        bone_widgets = [
            ('groove', 'WGT-Root.2Way', 20.0, 'body.x'),
            ('mmd_uuunyaa_shoulder_parent.l', 'WGT-rig_upper_arm_tweak.L', 0.5, 'body.l'),
            ('mmd_uuunyaa_shoulder_parent.r', 'WGT-rig_upper_arm_tweak.R', 0.5, 'body.r'),
            ('mmd_uuunyaa_upper_arm_twist_fk.l', 'WGT-rig_upper_arm_fk.L', 1.0, 'body.l'),
            ('mmd_uuunyaa_upper_arm_twist_fk.r', 'WGT-rig_upper_arm_fk.R', 1.0, 'body.r'),
            ('mmd_uuunyaa_wrist_twist_fk.l', 'WGT-rig_forearm_fk.L', 1.0, 'body.l'),
            ('mmd_uuunyaa_wrist_twist_fk.r', 'WGT-rig_forearm_fk.R', 1.0, 'body.r'),
            ('mmd_uuunyaa_leg_ik_parent.l', 'WGT-Bowl.Horizontal.001', 20.0, 'body.l'),
            ('mmd_uuunyaa_leg_ik_parent.r', 'WGT-Bowl.Horizontal.001', 20.0, 'body.r'),
            ('mmd_uuunyaa_toe_ik.l', 'WGT-Visor.Wide', 1.0, 'body.l'),
            ('mmd_uuunyaa_toe_ik.r', 'WGT-Visor.Wide', 1.0, 'body.r'),
        ]

        rig_bone_groups = self.pose_bone_groups

        insufficient_custom_shapes = list({custom_shape_name for _, custom_shape_name, _, _ in bone_widgets} - set(bpy.data.objects.keys()))
        self.load_custom_shapes(insufficient_custom_shapes)

        for bone_name, custom_shape_name, custom_shape_scale, bone_group_name in bone_widgets:
            pose_bones[bone_name].custom_shape = bpy.data.objects[custom_shape_name]
            if hasattr(pose_bones[bone_name], 'custom_shape_scale_xyz'):
                pose_bones[bone_name].custom_shape_scale_xyz = [custom_shape_scale, custom_shape_scale, custom_shape_scale]
            else: # SUPPORT_UNTIL: 3.3 LTS
                pose_bones[bone_name].custom_shape_scale = custom_shape_scale
            pose_bones[bone_name].bone_group = rig_bone_groups[bone_group_name]

        if not self.has_face_bones():
            return

        pose_bones['mmd_uuunyaa_eyes_fk'].bone_group = rig_bone_groups['body.x']
        pose_bones['mmd_uuunyaa_eye_fk.l'].bone_group = rig_bone_groups['body.l']
        pose_bones['mmd_uuunyaa_eye_fk.r'].bone_group = rig_bone_groups['body.r']

    def _imitate_mmd_eye_behavior(self, pose_bones: Dict[str, bpy.types.PoseBone]):
        if not self.has_face_bones():
            return

        self._add_eye_constraints(
            pose_bones['c_eye.l'], pose_bones['c_eye.r'],
            pose_bones['mmd_uuunyaa_eye_fk.l'], pose_bones['mmd_uuunyaa_eye_fk.r'],
            pose_bones['mmd_uuunyaa_eyes_fk']
        )

        eye_mmd_uuunyaa_data_path = f'pose.bones{self.datapaths[ControlType.EYE_MMD_UUUNYAA].data_path}'

        def update_influence_drivers(pose_bone: bpy.types.PoseBone, influence_data_path: str, invert_influence=False):
            for constraint in pose_bone.constraints:
                self.update_influence_driver(constraint, self.raw_object, influence_data_path, invert_influence=invert_influence)

        update_influence_drivers(pose_bones['c_eye.l'], eye_mmd_uuunyaa_data_path, invert_influence=True)
        update_influence_drivers(pose_bones['c_eye.r'], eye_mmd_uuunyaa_data_path, invert_influence=True)

    def pose_mmd_rest(self, dependency_graph: bpy.types.Depsgraph, iterations: int, pose_arms: bool, pose_legs: bool, pose_fingers: bool):
        # pylint: disable=too-many-arguments, too-many-locals
        pose_bones = self.pose_bones

        def set_rotation(pose_bone: bpy.types.PoseBone, rotation_matrix: Matrix):
            pose_bone.matrix = Matrix.Translation(pose_bone.matrix.to_translation()) @ rotation_matrix

        def to_rotation_matrix(pose_bone: bpy.types.PoseBone) -> Matrix:
            return pose_bone.matrix.to_euler().to_matrix().to_4x4()

        arm_l_target_rotation = Euler([math.radians(+123+90), math.radians(0), math.radians(+90)]).to_matrix().to_4x4()
        hand_l_target_rotation = Euler([math.radians(-123+90), math.radians(0), math.radians(-90)]).to_matrix().to_4x4()

        arm_r_target_rotation = Euler([math.radians(+123-270), math.radians(0), math.radians(-90)]).to_matrix().to_4x4()
        hand_r_target_rotation = Euler([math.radians(-123+90), math.radians(0), math.radians(+90)]).to_matrix().to_4x4()

        for _ in range(iterations):
            if pose_arms:
                # arm.L
                for bone_name in ['c_arm_fk.l', 'c_forearm_fk.l', ]:
                    set_rotation(pose_bones[bone_name], arm_l_target_rotation)

                for bone_name in ['c_hand_fk.l', ]:
                    set_rotation(pose_bones[bone_name], hand_l_target_rotation)

                # arm.R
                for bone_name in ['c_arm_fk.r', 'c_forearm_fk.r', ]:
                    set_rotation(pose_bones[bone_name], arm_r_target_rotation)

                for bone_name in ['c_hand_fk.r', ]:
                    set_rotation(pose_bones[bone_name], hand_r_target_rotation)

            if pose_legs:
                # foot.L
                pose_bones['mmd_uuunyaa_leg_ik_parent.l'].location.x += pose_bones['thigh.l'].head[0]-pose_bones['foot.l'].head[0]
                pose_bones['c_thigh_b.l'].rotation_euler.y -= math.radians(180)+math.atan2(*pose_bones['c_thigh_b.l'].x_axis[0: 2])

                pose_bones['c_foot_ik.l'].matrix = (
                    pose_bones['c_foot_ik.l'].matrix
                    @ Matrix.Rotation(math.radians(180)+pose_bones['foot.l'].matrix.to_euler().z, 4, 'Z')
                )
                pose_bones['c_leg_pole.l'].location.x += pose_bones['thigh.l'].head[0]-pose_bones['c_leg_pole.l'].head[0]

                # foot.R
                pose_bones['mmd_uuunyaa_leg_ik_parent.r'].location.x += pose_bones['thigh.r'].head[0]-pose_bones['foot.r'].head[0]
                pose_bones['c_thigh_b.r'].rotation_euler.y -= math.radians(0)+math.atan2(*pose_bones['c_thigh_b.r'].x_axis[0:2])
                pose_bones['c_foot_ik.r'].matrix = (
                    pose_bones['c_foot_ik.r'].matrix
                    @ Matrix.Rotation(math.radians(180)+pose_bones['foot.r'].matrix.to_euler().z, 4, 'Z')
                )
                pose_bones['c_leg_pole.r'].location.x += pose_bones['thigh.r'].head[0]-pose_bones['c_leg_pole.r'].head[0]

            if pose_fingers:
                # finger.L
                target_rotation = to_rotation_matrix(pose_bones['f_middle.01.l'])
                for bone_name in [
                    'c_index1.l', 'c_index2.l', 'c_index3.l',
                    'c_middle1.l', 'c_middle2.l', 'c_middle3.l',
                    'c_ring1.l', 'c_ring2.l', 'c_ring3.l',
                    'c_pinky1.l', 'c_pinky2.l', 'c_pinky3.l',
                ]:
                    set_rotation(pose_bones[bone_name], target_rotation)

                # finger.R
                target_rotation = to_rotation_matrix(pose_bones['c_middle1.r'])
                for bone_name in [
                    'c_index1.r', 'c_index2.r', 'c_index3.r',
                    'c_middle1.r', 'c_middle2.r', 'c_middle3.r',
                    'c_ring1.r', 'c_ring2.r', 'c_ring3.r',
                    'c_pinky1.r', 'c_pinky2.r', 'c_pinky3.r',
                ]:
                    set_rotation(pose_bones[bone_name], target_rotation)

            dependency_graph.update()
