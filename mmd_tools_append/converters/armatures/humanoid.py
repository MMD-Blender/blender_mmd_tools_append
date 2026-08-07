# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

import math
import re
from collections import Counter
from collections.abc import Iterator

import bpy
from mathutils import Vector

from ...editors.armatures import ArmatureEditor
from ...utilities import import_mmd_tools

# constants
MMD_CONTROL = ("センター", "全ての親", "足ＩＫ.L", "足ＩＫ.R", "つま先ＩＫ.L", "つま先ＩＫ.R")

HUMANOID_CATEGORY = [
    ("BODY", "Body", "Spine, arm and leg"),
    ("HEAD", "Head", "Neck, head and eyes"),
    ("HAND_L", "Left Hand", "Left hand fingers"),
    ("HAND_R", "Right Hand", "Right hand fingers"),
]

DISPLAY_TYPE_COLUMNS = {
    "DEFAULT": 1,
    "MIRRORED": 2,
    "FINGER": 3,
}

HUMANOID_DEFAULTS = [
    {
        "name": "Body",
        "name_j": "体(上)",
        "icon": "OUTLINER_OB_ARMATURE",
        "category": "BODY",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Hips", "mmd_j": "下半身", "frame_override": "体(下)"},
            {"name": "Spine", "mmd_j": "上半身"},
            {"name": "Chest", "mmd_j": "上半身2"},
            {"name": "UpperChest", "mmd_j": "上半身3"},
        ],
    },
    {
        "name": "Arm",
        "name_j": "腕",
        "icon": "VIEW_PAN",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "Shoulder", "mmd_j": "肩"},
            {"name": "UpperArm", "mmd_j": "腕"},
            {"name": "LowerArm", "mmd_j": "ひじ"},
            {"name": "Hand", "mmd_j": "手首"},
        ],
    },
    {
        "name": "Leg",
        "name_j": "足",
        "icon": "MOD_DYNAMICPAINT",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "UpperLeg", "mmd_j": "足"},
            {"name": "LowerLeg", "mmd_j": "ひざ"},
            {"name": "Foot", "mmd_j": "足首"},
            {"name": "Toe", "mmd_j": "つま先"},
        ],
    },
    {
        "name": "Head",
        "name_j": "頭",
        "icon": "USER",
        "category": "HEAD",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Neck", "mmd_j": "首"},
            {"name": "Head", "mmd_j": "頭"},
            {"name": "LeftEye", "mmd_j": "左目"},
            {"name": "RightEye", "mmd_j": "右目"},
        ],
    },
    {
        "name": "Left Hand",
        "name_j": "指",
        "icon": "VIEW_PAN",
        "category": "HAND_L",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb", "mmd_j": "左親指"},
            {"name": "Index", "mmd_j": "左人指"},
            {"name": "Middle", "mmd_j": "左中指"},
            {"name": "Ring", "mmd_j": "左薬指"},
            {"name": "Little", "mmd_j": "左小指"},
        ],
    },
    {
        "name": "Right Hand",
        "name_j": "指",
        "icon": "VIEW_PAN",
        "category": "HAND_R",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb", "mmd_j": "右親指"},
            {"name": "Index", "mmd_j": "右人指"},
            {"name": "Middle", "mmd_j": "右中指"},
            {"name": "Ring", "mmd_j": "右薬指"},
            {"name": "Little", "mmd_j": "右小指"},
        ],
    },
]


# property groups
class HumanoidBoneSlot(bpy.types.PropertyGroup):
    bone_name: bpy.props.StringProperty(name="Bone")

    def info(self):
        return f'HumanoidBoneSlot("{self.bone_name}")'


class HumanoidItem(bpy.types.PropertyGroup):
    """
    Each element of humanoid bones.

    Mirrored element (.L/.R) and finger bones (1-3) will be processed together.
    """

    def _update_slot_size(self, _context):
        """keep slots at a fixed size. (at least 1)"""

        while len(self.slots) > self.column_count:
            if len(self.slots) <= 1:
                break
            self.slots.remove(len(self.slots) - 1)

        while len(self.slots) < self.column_count:
            self.slots.add()

    def auto(self, editor, display_type):
        """Auto fills empty slots based on existing selection."""

        def flip_name(name: str) -> str:
            """Convert names like Arm.L, Arm_L, LeftArm, ArmLeft to right."""

            suffix_pattern = r"([._-])([LRlr])$"
            match = re.search(suffix_pattern, name)
            if match:
                delim = match.group(1)
                suffix = match.group(2)
                flipped = {"L": "R", "R": "L", "l": "r", "r": "l"}[suffix]
                return name[:-2] + delim + flipped
            else:
                mappings = {}
                LR = [("left", "right"), ("Left", "Right"), ("LEFT", "RIGHT"), ("J_Bip_L", "J_Bip_R")]
                for k, v in LR:
                    mappings[k] = v
                    mappings[v] = k
                pattern = re.compile("|".join(re.escape(k) for k in mappings.keys()))
                return pattern.sub(lambda m: mappings[m.group(0)], name)

        def get_lineal(name: str) -> tuple[str, str]:
            """Get parent and first child."""

            parent = ""
            child = ""
            if name in editor.bones:
                bone = editor.bones[name]
                parent = bone.parent.name if bone.parent else ""
                child = bone.children[0].name if bone.children else ""
            return parent, child

        match display_type:
            case "MIRRORED":
                for i in range(len(self.slots)):
                    if not self.slots[i].bone_name:
                        self.slots[i].bone_name = flip_name(self.slots[i - 1].bone_name)
            case "FINGER":
                for i in reversed(range(len(self.slots))):
                    if i < len(self.slots) - 1 and not self.slots[i].bone_name:
                        self.slots[i].bone_name = get_lineal(self.slots[i + 1].bone_name)[0]
                for i in range(len(self.slots)):
                    if i > 0 and not self.slots[i].bone_name:
                        self.slots[i].bone_name = get_lineal(self.slots[i - 1].bone_name)[1]

    name: bpy.props.StringProperty()
    mmd_j: bpy.props.StringProperty()
    mmd_e: bpy.props.StringProperty()
    frame_override: bpy.props.StringProperty()
    column_count: bpy.props.IntProperty(default=1, min=1, update=_update_slot_size)
    slots: bpy.props.CollectionProperty(type=HumanoidBoneSlot)


class HumanoidDisplayFrame(bpy.types.PropertyGroup):
    def _check_category(self, _context):
        if self.category not in [item[0] for item in HUMANOID_CATEGORY]:
            print("Invalid DisplayFrame category")

    def sync_display_type(self, _context):
        column = DISPLAY_TYPE_COLUMNS.get(self.display_type, 1)
        for item in self.items:
            item.column_count = column

    def _ensure_icon(self, _context):
        if not self.icon:
            self.icon = "NONE"

    name: bpy.props.StringProperty(translation_context="MMD_HUMANOID")
    name_j: bpy.props.StringProperty()
    """actual name used for MMD DisplayFrame"""

    icon: bpy.props.StringProperty(update=_ensure_icon)
    category: bpy.props.StringProperty(update=_check_category)
    """must be one of IDs in HUMANOID_CATEGORY"""

    display_type: bpy.props.EnumProperty(
        items=[
            ("DEFAULT", "Default", "1 slot (default)"),
            ("MIRRORED", "Mirrored", "2 slots for Left/Right"),
            ("FINGER", "Finger", "3 slots for finger"),
        ],
        update=sync_display_type,
    )
    split_factor: bpy.props.FloatProperty(default=0.2)
    items: bpy.props.CollectionProperty(type=HumanoidItem)


class HumanoidTree(bpy.types.PropertyGroup):
    frames: bpy.props.CollectionProperty(type=HumanoidDisplayFrame)

    def initialize_humanoid(self, data: dict = HUMANOID_DEFAULTS):
        if self.frames:
            return

        self.reset_humanoid(data)

    def reset_humanoid(self, data: dict = HUMANOID_DEFAULTS):
        self.frames.clear()

        for frame_data in data:
            frame = self.frames.add()
            frame.name = frame_data["name"]
            frame.name_j = frame_data["name_j"]
            frame.icon = frame_data["icon"]
            frame.category = frame_data["category"]
            frame.display_type = frame_data.get("display_type", "DEFAULT")

            for item_data in frame_data.get("items", []):
                item = frame.items.add()
                item.name = item_data["name"]
                item.mmd_j = item_data.get("mmd_j", "")
                item.mmd_e = item_data.get("mmd_e", "")
                item.frame_override = item_data.get("frame_override", "")

            frame.sync_display_type(None)

    def iter_items(self) -> Iterator[tuple[HumanoidDisplayFrame, HumanoidItem]]:
        """access HumanoidItem as iterator"""

        for frame in self.frames:
            for item in frame.items:
                yield frame, item

    def iter_slots(self) -> Iterator[HumanoidBoneSlot]:
        for _, item in self.iter_items():
            for slot in item.slots:
                yield slot

    def get_duplicates(self) -> dict[str, int]:
        """Find bones that have been selected more than once."""
        c = Counter(s.bone_name for s in self.iter_slots() if s.bone_name)
        return {k: v for k, v in c.items() if v > 1}

    @staticmethod
    def register():
        bpy.types.Object.mmd_tools_append_humanoid_settings = bpy.props.PointerProperty(type=HumanoidTree)
        bpy.types.WindowManager.mmd_humanoid_category = bpy.props.EnumProperty(
            name="Append Humanoid Category",
            items=HUMANOID_CATEGORY,
            default="BODY",
            translation_context="MMD_HUMANOID",
        )

    @staticmethod
    def unregister():
        del bpy.types.WindowManager.mmd_humanoid_category
        del bpy.types.Object.mmd_tools_append_humanoid_settings


class HumanoidEditor(ArmatureEditor):
    tree: HumanoidTree

    def __init__(self, armature_object: bpy.types.Object):
        super().__init__(armature_object)
        self.tree = armature_object.mmd_tools_append_humanoid_settings

    def _get_deform_bones(self) -> list[str]:
        """Get vertex group names that have non-zero weights."""
        meshes = self._get_related_mesh()
        vg_names = set()

        for m in meshes:
            if not m.data or not m.vertex_groups:
                continue

            vg_map = {vg.index: vg.name for vg in m.vertex_groups}
            vg_sets = set()

            for v in m.data.vertices:
                for g in v.groups:
                    if g.weight > 0.0:
                        vg_sets.add(g.group)

                if len(vg_sets) == len(vg_map):
                    break

            for idx in vg_sets:
                name = vg_map.get(idx)
                if name and name in self.bones and self.bones[name].use_deform:
                    vg_names.add(name)

        return list(vg_names)

    @property
    def is_mmd_armature_object(self) -> bool:
        if self.raw_object is None:
            return False

        if self.raw_object.type != "ARMATURE":
            return False

        if import_mmd_tools().core.model.FnModel.find_root_object(self.raw_object) is None:
            return False

        return True

    @staticmethod
    def convert_mmd_prefix(name: str) -> str:
        """左右 prefix to .LR suffix"""
        if name.startswith("左"):
            return name[1:] + ".L"
        if name.startswith("右"):
            return name[1:] + ".R"
        return name

    def to_mmd_pose(self, use_local=False, use_apose=False):
        """Convert bones to MMD. This function expects MMD naming convention."""

        def create_root(center_length: float = 0.7):
            """Create MMD center and root bone."""
            bpy.ops.object.mode_set(mode="EDIT")
            center_coll = self.get_or_create_bone_collection(self.bone_collections, "センター")
            root_coll = self.get_or_create_bone_collection(self.bone_collections, "Root")

            upper_body = self.edit_bones["上半身"]
            lower_body = self.edit_bones["下半身"]
            parent = lower_body.parent
            if parent is None or not math.isclose(parent.head.length, 0):
                parent = self.create_bone_pos("全ての親", root_coll, (0.0, 0.0, 0.0), (0.0, 0.0, center_length))
            else:
                parent.name = "全ての親"
                root_coll.assign(parent)

            center = self.create_bone_pos("センター", center_coll, (0.0, 0.0, center_length), (0.0, 0.0, 0.0), parent)
            upper_body.use_connect = False
            lower_body.use_connect = False
            upper_body.parent = center
            lower_body.parent = center
            if lower_body.vector.z > 0:
                lower_body.tail = lower_body.head
                lower_body.head = upper_body.head

            bpy.ops.object.mode_set(mode="POSE")

        def to_mmd_bone():
            """Locks positions of the bones and changes display connection to child bone."""
            for pbone in self.pose_bones:
                if pbone.name not in MMD_CONTROL:
                    pbone.lock_location = [True, True, True]
                    pbone.lock_rotation_w = False
                if len(pbone.children) == 1:
                    pbone.mmd_bone.display_connection_type = "BONE"
                    pbone.mmd_bone.display_connection_bone = pbone.children[0].name

        def is_tpose(tpose_angle: float = 5.0) -> bool:
            """Check if the model is in T-pose."""
            arm_vec = self.pose_bones["腕.L"].vector.normalized()
            angle = self.to_angle(arm_vec, "XZ")
            return math.degrees(abs(angle)) < tpose_angle

        def remove_deform():
            """Disables `use_deform` to exclude from Automatic Weights."""
            for bone in self.bones:
                if bone.name in MMD_CONTROL:
                    bone.use_deform = False

        def apply_local():
            """Adds local axis to arm bones."""
            bpy.ops.pose.select_all(action="DESELECT")
            for bone in self.bone_collections["指"].bones:
                pbone = self.pose_bones[bone.name]
                pbone.select = True
                pbone.mmd_bone.enabled_local_axes = True

            for bone in self.bone_collections["腕"].bones:
                if "肩" not in bone.name:
                    pbone = self.pose_bones[bone.name]
                    pbone.select = True
                    pbone.mmd_bone.enabled_local_axes = True

            bpy.ops.mmd_tools.bone_local_axes_setup(type="LOAD")
            bpy.ops.mmd_tools.bone_local_axes_setup(type="APPLY")

        def apply_fixed_axis():
            """Adds fixed axis to arm twist bones."""
            bpy.ops.pose.select_all(action="DESELECT")
            for bone in self.bone_collections["腕"].bones:
                if "捩" in bone.name:
                    pbone = self.pose_bones[bone.name]
                    pbone.select = True
                    pbone.mmd_bone.enabled_fixed_axis = True

            bpy.ops.mmd_tools.bone_fixed_axis_setup(type="LOAD")
            bpy.ops.mmd_tools.bone_fixed_axis_setup(type="APPLY")

        bpy.ops.object.mode_set(mode="POSE")
        if not self.pose_bones.get("センター") or not self.pose_bones.get("全ての親"):
            create_root()

        if use_apose and is_tpose():
            angle = math.radians(45)

            pb = self.pose_bones["腕.L"]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler[0] = -angle

            pb = self.pose_bones["腕.R"]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler[0] = -angle

            bpy.ops.pose.armature_apply()

        to_mmd_bone()
        remove_deform()
        apply_fixed_axis()
        if use_local:
            apply_local()

    def auto_orientation(self):
        """Automatic Orientation, similar to legacy FBX importer"""

        def sign(num) -> int:
            return (num > 0) - (num < 0)

        def find_major_axis(bone: bpy.types.EditBone) -> tuple[int, int]:
            child_dir = (bone.children[0].head - bone.head).normalized()
            prev_axes = bone.matrix.to_3x3().col
            scores = [(abs(child_dir.dot(axis)), idx, sign(child_dir.dot(axis))) for idx, axis in enumerate(prev_axes)]
            _, axis_idx, axis_sign = max(scores)
            return axis_idx, axis_sign

        axis_votes = [find_major_axis(bone) for bone in self.edit_bones if bone.children and len(bone.children) == 1]
        if not axis_votes:
            return

        (g_axis_idx, g_axis_sign), _ = Counter(axis_votes).most_common(1)[0]
        for bone in self.edit_bones:
            col = bone.matrix.to_3x3().col
            new_dir = col[g_axis_idx] * g_axis_sign

            prev_roll = bone.z_axis.copy()
            if abs(new_dir.dot(prev_roll.normalized())) > 0.99:
                prev_roll = bone.x_axis.copy()

            bone.tail = bone.head + new_dir * bone.length
            bone.align_roll(prev_roll)

            if bone.children and len(bone.children) == 1:
                child = bone.children[0]
                if abs(bone.length - (child.head - bone.head).length) < 0.0001:
                    bone.tail = child.head

    def add_leg_ik(self):
        """Leg IK maker. Adapted from MMD Tools Helper"""

        def add_limit_rot(pbone: bpy.types.PoseBone):
            self.add_constraint(
                pbone,
                "LIMIT_ROTATION",
                "mmd_ik_limit_override",
                use_limit_x=True,
                use_limit_y=False,
                use_limit_z=False,
                min_x=math.pi / 360,  # radians=0.5 degrees
                max_x=math.pi,  # radians=180 degrees
                min_y=0,
                max_y=0,
                min_z=0,
                max_z=0,
                owner_space="LOCAL",
            )

        def add_ik_limit(pbone: bpy.types.PoseBone):
            pbone.use_ik_limit_x = True
            pbone.use_ik_limit_y = True
            pbone.use_ik_limit_z = True
            pbone.ik_min_x = 0
            pbone.ik_max_x = math.pi
            pbone.ik_min_y = 0
            pbone.ik_max_y = 0
            pbone.ik_min_z = 0
            pbone.ik_max_z = 0

        def create_ik_bone(name: str, target: str, parent: str) -> bpy.types.EditBone:
            bone = self.edit_bones.new(name)
            bone.head = self.edit_bones[target].head
            bone.tail = self.edit_bones[target].head
            bone.parent = self.edit_bones[parent]
            bone.use_deform = False
            return bone

        ROOT = "全ての親"
        LEG_IK_L = "足ＩＫ.L"
        LEG_IK_R = "足ＩＫ.R"
        TOE_IK_L = "つま先ＩＫ.L"
        TOE_IK_R = "つま先ＩＫ.R"

        LEG_L = "足.L"
        LEG_R = "足.R"
        KNEE_L = "ひざ.L"
        KNEE_R = "ひざ.R"
        ANKLE_L = "足首.L"
        ANKLE_R = "足首.R"
        TOE_L = "つま先.L"
        TOE_R = "つま先.R"

        # checks
        if self.pose_bones.get(LEG_IK_L) or self.pose_bones.get(LEG_IK_R):
            print("This armature already has Leg IK.")
            return
        if not self.pose_bones.get(ROOT) or not self.pose_bones.get(ANKLE_L) or not self.pose_bones.get(ANKLE_R):
            print("This armature does not have MMD bones.")
            return

        bpy.ops.object.mode_set(mode="POSE")

        add_ik_limit(self.pose_bones[KNEE_L])
        add_ik_limit(self.pose_bones[KNEE_R])

        # used for IK bone length
        FOOT_LENGTH = self.bones[ANKLE_L].length

        bpy.ops.object.mode_set(mode="EDIT")

        # merge leg twist bones if they exist (LowerLeg & UpperLeg)
        if self.edit_bones[KNEE_L].parent != self.edit_bones[LEG_L]:
            self.dissolve_bone(self.edit_bones[KNEE_L].parent)
        if self.edit_bones[KNEE_R].parent != self.edit_bones[LEG_R]:
            self.dissolve_bone(self.edit_bones[KNEE_R].parent)
        if self.edit_bones[ANKLE_L].parent != self.edit_bones[KNEE_L]:
            self.dissolve_bone(self.edit_bones[ANKLE_L].parent)
        if self.edit_bones[ANKLE_R].parent != self.edit_bones[KNEE_R]:
            self.dissolve_bone(self.edit_bones[ANKLE_R].parent)

        # move knees forward a little to prevent glitches
        if math.isclose(self.edit_bones[LEG_L].vector.angle(self.edit_bones[KNEE_L].vector), 0):
            self.edit_bones[LEG_L].tail.y = -0.005
            self.edit_bones[LEG_R].tail.y = -0.005

        # reset bone rolls
        self.edit_bones[LEG_L].roll = 0
        self.edit_bones[LEG_R].roll = 0
        self.edit_bones[KNEE_L].roll = 0
        self.edit_bones[KNEE_R].roll = 0
        self.edit_bones[ANKLE_L].roll = 0
        self.edit_bones[ANKLE_R].roll = 0
        self.edit_bones[TOE_L].roll = 0
        self.edit_bones[TOE_R].roll = 0

        # Add IK bones
        bone = create_ik_bone(LEG_IK_L, ANKLE_L, ROOT)
        bone.tail.y = self.edit_bones[ANKLE_L].head.y + FOOT_LENGTH

        bone = create_ik_bone(LEG_IK_R, ANKLE_R, ROOT)
        bone.tail.y = self.edit_bones[ANKLE_R].head.y + FOOT_LENGTH

        bone = create_ik_bone(TOE_IK_L, TOE_L, LEG_IK_L)
        bone.tail.z = self.edit_bones[TOE_L].head.z - FOOT_LENGTH / 2

        bone = create_ik_bone(TOE_IK_R, TOE_R, LEG_IK_R)
        bone.tail.z = self.edit_bones[TOE_R].head.z - FOOT_LENGTH / 2

        bpy.ops.object.mode_set(mode="POSE")

        self.pose_bones[LEG_IK_L].mmd_bone.name_j = "左足ＩＫ"
        self.pose_bones[LEG_IK_R].mmd_bone.name_j = "右足ＩＫ"
        self.pose_bones[TOE_IK_L].mmd_bone.name_j = "左つま先ＩＫ"
        self.pose_bones[TOE_IK_R].mmd_bone.name_j = "右つま先ＩＫ"
        self.pose_bones[LEG_IK_L].mmd_bone.name_e = "LegIK.L"
        self.pose_bones[LEG_IK_R].mmd_bone.name_e = "LegIK.R"
        self.pose_bones[TOE_IK_L].mmd_bone.name_e = "ToeIK.L"
        self.pose_bones[TOE_IK_R].mmd_bone.name_e = "ToeIK.R"

        # Add bone constraints
        self.add_ik_constraint(self.pose_bones[KNEE_L], self.raw_object, LEG_IK_L, 2, 200)
        self.add_ik_constraint(self.pose_bones[KNEE_R], self.raw_object, LEG_IK_R, 2, 200)
        self.add_ik_constraint(self.pose_bones[ANKLE_L], self.raw_object, TOE_IK_L, 1, 15)
        self.add_ik_constraint(self.pose_bones[ANKLE_R], self.raw_object, TOE_IK_R, 1, 15)

        self.pose_bones[KNEE_L].mmd_bone.ik_rotation_constraint = 2  # 180*2/math.pi, 114.5916
        self.pose_bones[KNEE_R].mmd_bone.ik_rotation_constraint = 2
        self.pose_bones[ANKLE_L].mmd_bone.ik_rotation_constraint = 4  # 180*4/math.pi, 229.1831
        self.pose_bones[ANKLE_R].mmd_bone.ik_rotation_constraint = 4

        add_limit_rot(self.pose_bones[KNEE_L])
        add_limit_rot(self.pose_bones[KNEE_R])

        # Add to Bone Collection
        ik_col = self.get_or_create_bone_collection(self.bone_collections, "IK")
        ik_col.assign(self.pose_bones[LEG_IK_L])
        ik_col.assign(self.pose_bones[LEG_IK_R])
        ik_col.assign(self.pose_bones[TOE_IK_L])
        ik_col.assign(self.pose_bones[TOE_IK_R])

    def add_eyes_bone(self):
        """Adds 両目 bone to MMD rig."""

        HEAD = "頭"
        EYES = "両目"
        EYE_L = "目.L"
        EYE_R = "目.R"

        # checks
        if self.pose_bones.get(EYES):
            print("This armature already has eyes bone.")
            return
        if not self.pose_bones.get(EYE_L) or not self.pose_bones.get(EYE_R) or not self.pose_bones.get(HEAD):
            print("This armature does not have eye bones.")
            return

        bpy.ops.object.mode_set(mode="EDIT")
        bone = self.edit_bones.new(EYES)
        bone.head = self.edit_bones[HEAD].tail + Vector((0, 0, 0.2))
        bone.tail = bone.head + Vector((0, -0.05, 0))
        bone.parent = self.edit_bones[HEAD]
        bone.use_deform = False

        bpy.ops.object.mode_set(mode="POSE")
        self.pose_bones[EYES].lock_location = [True, True, True]
        self.pose_bones[EYES].lock_rotation_w = False
        self.pose_bones[EYES].mmd_bone.name_j = "両目"
        self.pose_bones[EYES].mmd_bone.name_e = "Eyes"
        self.pose_bones[EYE_L].mmd_bone.additional_transform_bone = EYES
        self.pose_bones[EYE_R].mmd_bone.additional_transform_bone = EYES
        self.pose_bones[EYE_L].mmd_bone.has_additional_rotation = True
        self.pose_bones[EYE_R].mmd_bone.has_additional_rotation = True

        upper_body = self.get_or_create_bone_collection(self.bone_collections, "体(上)")
        upper_body.assign(self.pose_bones[EYES])

    def rename(self) -> int:
        count = 0

        LR_MAP_MMD = {0: "左", 1: "右"}
        LR_MAP_BLENDER = {0: ".L", 1: ".R"}
        HALF_FULL = str.maketrans("0123456789", "０１２３４５６７８９")

        for frame, item in self.tree.iter_items():
            col = self.get_or_create_bone_collection(self.bone_collections, frame.name_j)

            for idx, slot in enumerate(item.slots):
                if not slot.bone_name:
                    continue

                bone = self.edit_bones.get(slot.bone_name)
                if not bone:
                    continue

                pbone = self.pose_bones[slot.bone_name]
                original = bone.name
                target_j = item.mmd_j
                target_e = item.mmd_e

                match frame.display_type:
                    case "MIRRORED":
                        target_j = f"{LR_MAP_MMD.get(idx, '')}{target_j}"
                        if target_e:
                            target_e = f"{target_e}{LR_MAP_BLENDER.get(idx, '')}"
                    case "FINGER":
                        # 親指ならbaseから0, 1, 2 (全角)
                        init_n = 0 if item.name == "Thumb" else 1
                        target_j += str(idx + init_n).translate(HALF_FULL)
                        if target_e:
                            target_e += str(idx + init_n)

                # rename!
                bone.name = self.convert_mmd_prefix(target_j)
                pbone.mmd_bone.name_j = target_j
                if not pbone.mmd_bone.name_e:
                    pbone.mmd_bone.name_e = target_e or original

                if item.frame_override:
                    col = self.get_or_create_bone_collection(self.bone_collections, item.frame_override)
                    col.assign(bone)
                else:
                    col.assign(bone)

                # update
                slot.bone_name = bone.name
                count += 1

        return count

    def detect(self, finger_count: int = 5, fine_precision: float = 0.0001, rough_precision: float = 0.1):
        """
        Analyze the bone position, direction, structure and name to find Humanoid structure.
        Intended for non-MMD models, and the model must face Y- direction.
        """

        def isclose_abs(a: float, b: float, tol: float) -> bool:
            """Returns if the absolute values of a and b are close."""
            return math.isclose(abs(a), abs(b), abs_tol=tol)

        def traverse_parent_chain(
            bone: bpy.types.EditBone,
            threshold: float = 0.8,
            check_root: bool = False,
            allow_inverse: bool = False,
            chain: list[str] = None,
        ) -> list[str]:
            """
            Find connected parents that are pointing in a similar direction (bone chain).
            threshold = 1 means it will treat 90deg as part of the chain.
            """

            parent = bone.parent
            if not parent or not parent.use_deform:
                return chain if chain else []

            if chain is None:
                chain = []

            angle = bone.vector.angle(parent.vector)

            if allow_inverse:
                angle = min(angle, math.pi - angle)

            if angle < math.pi * 0.5 * threshold and (not check_root or parent.head.length >= 0.001):
                chain.append(parent.name)
                return traverse_parent_chain(parent, threshold=threshold, check_root=check_root, allow_inverse=allow_inverse, chain=chain)
            else:
                return chain

        def traverse_child_chain(bone: bpy.types.EditBone, threshold: float = 0.8, chain: list[str] = None) -> list[str]:
            """
            Find connected children that are pointing in a similar direction (bone chain).
            threshold = 1 means it will treat 90deg as part of the chain.
            """
            deform_children = [b for b in bone.children if b.use_deform]

            if not deform_children:
                return chain if chain else []

            if chain is None:
                chain = []

            child = min(deform_children, key=lambda b: (b.head - bone.tail).length)
            angle = bone.vector.angle(child.vector)
            distance = (child.head - bone.tail).length

            if angle < math.pi * 0.5 * threshold and distance < child.vector.length:
                chain.append(child.name)
                return traverse_child_chain(child, threshold=threshold, chain=chain)
            else:
                return chain

        def find_mutual_parent(bone_names: list[str]) -> bpy.types.EditBone:
            """Find the lowest common ancestor of the given bones."""
            if not bone_names:
                return None

            ancestors_sets = [set(self.edit_bones[n].parent_recursive) for n in bone_names]
            common_ancestors = set.intersection(*ancestors_sets)

            if not common_ancestors:
                return None

            return max(common_ancestors, key=lambda b: len(b.parent_recursive))

        def is_left(bone_name: str) -> bool:
            return bone_map[bone_name]["head"].x > 0

        def is_hidden(bone_name: str) -> bool:
            pbone = self.pose_bones[bone_name]
            if hasattr(pbone, "hide"):
                return pbone.hide
            else:
                return pbone.bone.hide

        def is_deform(bone: bpy.types.Bone | bpy.types.EditBone) -> bool:
            """Check if the bone actually deforms the mesh (weight check)."""
            if deform_list:
                return bone.name in deform_list
            else:
                # armature with no mesh
                return bone.use_deform

        def assign_bone(key: str, bone_name: str, index: int = None):
            if index is None:
                index = 0 if is_left(bone_name) else 1
            item_map[key].slots[index].bone_name = bone_name

        # finders
        def _find_hands(finger_count: int, fine_precision: float) -> list[str]:
            """finger count & furthest bone: thumb and index might be in the same parent. (5 finger but 4 children)"""
            hands = []
            finger_parent = [k for k, v in children_map.items() if len(v) >= finger_count - 1]
            if finger_parent:
                hand_pos = max(abs(bone_map[n]["head"].x) for n in finger_parent)
                hands = [n for n in finger_parent if isclose_abs(hand_pos, bone_map[n]["head"].x, fine_precision)]
                for h in hands:
                    assign_bone("Arm.Hand", h)
            return hands

        def _find_fingers(hands: list[str]):
            """tip: the bottom children of hands. (HumanoidItem.auto will do the rest)"""
            for h in hands:
                prefix = "Left Hand" if is_left(h) else "Right Hand"
                dummies = {bone for bone in self.edit_bones[h].children if not bone.children}
                fingers = [bone for bone in self.edit_bones[h].children_recursive if is_deform(bone) and bone not in dummies]
                finger_tips = sorted([f for f in fingers if f.name in children_map and not children_map.get(f.name)], key=lambda a: a.head.y)
                if len(finger_tips) != finger_count:
                    print(f"The finger count does not match ({len(finger_tips)}).")
                    continue

                ordered_names = ["Thumb", "Index", "Middle", "Ring", "Little"]
                for idx, f in enumerate(finger_tips):
                    assign_bone(f"{prefix}.{ordered_names[idx]}", f.name, 2)

        def _find_arms(hands: list[str]):
            for h in hands:
                arms = list(reversed(traverse_parent_chain(self.edit_bones[h])))
                if len(arms) >= 2:
                    shoulder_name = arms[0]
                    hand_head = self.edit_bones[h].head
                    shoulder_tail = self.edit_bones[shoulder_name].tail
                    mid_point = (shoulder_tail + hand_head) * 0.5
                    lower_arm_name = min(arms[1:], key=lambda n: (self.edit_bones[n].head - mid_point).length)

                    assign_bone("Arm.Shoulder", shoulder_name)
                    assign_bone("Arm.LowerArm", lower_arm_name)
                    if children_map.get(shoulder_name):
                        assign_bone("Arm.UpperArm", children_map[shoulder_name][0])

        def _find_spine(hands: list[str], rough_precision: float) -> str:
            """find head & spine using existing arm."""
            chest = find_mutual_parent(hands)

            if not chest:
                shoulder_name = item_map["Arm.Shoulder"].slots[0].bone_name or item_map["Arm.Shoulder"].slots[1].bone_name
                if shoulder_name:
                    chest = self.edit_bones[shoulder_name].parent

            if not chest or abs(chest.vector.x) > rough_precision:
                return None

            upper_spines = list(reversed(traverse_child_chain(chest)))
            lower_spines = list(reversed(traverse_parent_chain(chest, check_root=True, allow_inverse=True)))
            if not lower_spines:
                return None

            hips = lower_spines[0]
            spine = lower_spines[1] if len(lower_spines) > 1 else chest.name
            assign_bone("Body.Hips", hips, 0)
            assign_bone("Body.Spine", spine, 0)
            if len(lower_spines) > 2:
                assign_bone("Body.Chest", lower_spines[2], 0)
                assign_bone("Body.UpperChest", chest.name, 0)
            elif len(lower_spines) > 1:
                assign_bone("Body.Chest", chest.name, 0)

            if not upper_spines:
                return None

            head = upper_spines[0]  # prefer top
            assign_bone("Head.Head", head, 0)
            if len(upper_spines) > 1:
                neck = upper_spines[-1]  # prefer bottom
                assign_bone("Head.Neck", neck, 0)

            return head

        def _find_eyes(head: str):
            """direct children of Head, go straight in y- direction"""
            head_children = self.edit_bones[head].children
            eyes_candidate = [b for b in head_children if abs(b.vector.z) < fine_precision and b.vector.y < 0]
            if eyes_candidate:
                eyes = [b.name for b in eyes_candidate if (self.edit_bones[head].head - b.head).length < 0.3]
                if len(eyes) == 2:
                    for e in eyes:
                        if is_left(e):
                            assign_bone("Head.LeftEye", e, 0)
                        else:
                            assign_bone("Head.RightEye", e, 0)

        def _find_toes(fine_precision: float, rough_precision: float) -> list[str]:
            """lowest & furthest bone: heel bone might get detected as lowest"""
            toes = []
            min_z = min(v["head"].z for v in bone_map.values())
            bottom = [k for k, v in bone_map.items() if abs(v["head"].z - min_z) < rough_precision]
            if bottom:
                toes_vector = min(abs(bone_map[n]["vector"].z) for n in bottom)
                toes = [n for n in bottom if bone_map[n]["tail"].y < 0 and isclose_abs(toes_vector, bone_map[n]["vector"].z, fine_precision)]
                for t in toes:
                    assign_bone("Leg.Toe", t)
            return toes

        def _find_legs(toes: list[str]):
            """(broken on MMD because EX and ToeIK)"""
            for t in toes:
                legs = list(reversed(traverse_parent_chain(self.edit_bones[t])))
                hips = item_map["Body.Hips"].slots[0].bone_name
                if hips and hips in legs:
                    legs.remove(hips)
                if len(legs) >= 2:
                    upper_leg_name = legs[0]
                    foot_head = self.edit_bones[t].parent.head
                    upper_leg_head = self.edit_bones[upper_leg_name].head
                    mid_point = (upper_leg_head + foot_head) * 0.5
                    lower_leg_name = min(legs[1:], key=lambda n: (self.edit_bones[n].head - mid_point).length)

                    assign_bone("Leg.UpperLeg", upper_leg_name)
                    assign_bone("Leg.LowerLeg", lower_leg_name)
                    assign_bone("Leg.Foot", self.edit_bones[t].parent.name)

        # Gather bone and slot data
        deform_list = self._get_deform_bones()
        item_map = {f"{frame.name}.{item.name}": item for frame, item in self.tree.iter_items()}
        children_map = {b.name: [c.name for c in b.children if is_deform(c) and not is_hidden(c.name)] for b in self.bones if b.use_deform and not is_hidden(b.name)}
        bone_map: dict[str, dict[str, Vector]] = {
            b.name: {
                "head": b.head,
                "tail": b.tail,
                "vector": b.vector.normalized(),
            }
            for b in self.edit_bones
            if b.use_deform
        }

        hands = _find_hands(finger_count, fine_precision)
        if not hands:
            print("Couldn't find hands.")
            return

        _find_fingers(hands)
        _find_arms(hands)

        head = _find_spine(hands, rough_precision)
        if head:
            _find_eyes(head)
        else:
            print("Couldn't find head.")

        toes = _find_toes(fine_precision, rough_precision)
        if not toes:
            print("Couldn't find toes.")
            return

        _find_legs(toes)
