# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

from typing import Iterable, Optional, Tuple

import bpy
from bpy.app.translations import pgettext as _

from ...utilities import MessageException, import_mmd_tools
from .autorig import AutoRigArmatureObject
from .humanoid import HumanoidEditor
from .metarig import MetarigArmatureObject
from .mmd import MMDArmatureObject
from .rigify import MMDRigifyArmatureObject, RigifyArmatureObject


class MMDArmatureAddMetarig(bpy.types.Operator):
    bl_idname = "mmd_tools_append.mmd_armature_add_metarig"
    bl_label = "Add Human (metarig) from MMD Armature"
    bl_description = "Generate Human (metarig) from MMD Armature"
    bl_options = {"REGISTER", "UNDO"}

    use_mmd_orientation: bpy.props.BoolProperty(name="Align to MMD orientation", description="Adjust bone rolls to fit common MMD arm and finger orientations", default=True)
    is_clean_armature: bpy.props.BoolProperty(name="Clean Armature", default=True)
    is_clean_koikatsu_armature: bpy.props.BoolProperty(name="Clean Koikatsu Armature", default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != "OBJECT":
            return False

        if len(context.selected_objects) != 1:
            return False

        return MMDArmatureObject.is_mmd_armature_object(context.active_object)

    def _create_metarig_object(self) -> bpy.types.Object:
        original_cursor_location = bpy.context.scene.cursor.location
        try:
            # Rigifyのメタリグはどこに置いたとしても、
            # 生成ボタンをおすと(0, 0, 0)にRigifyArmatureが生成される。
            # よってメタリグも(0, 0, 0)に生成するようにする。
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.ops.object.armature_human_metarig_add()
            return bpy.context.object
        except AttributeError as ex:
            if str(ex) != 'Calling operator "bpy.ops.object.armature_human_metarig_add" error, could not be found':
                raise
            raise MessageException(_("Failed to invoke Rigify\nPlease enable Rigify add-on.")) from None
        finally:
            bpy.context.scene.cursor.location = original_cursor_location

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        mmd_object = context.active_object

        try:
            metarig_object = MetarigArmatureObject(self._create_metarig_object())
        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        try:
            mmd_armature_object = MMDArmatureObject(mmd_object)
            metarig_object.fit_scale(mmd_armature_object)

            mmd_object.select = True
            metarig_object.select = True

            if self.is_clean_koikatsu_armature:
                mmd_armature_object.clean_koikatsu_armature_prepare()
                mmd_armature_object = MMDArmatureObject(mmd_object)

            bpy.ops.object.mode_set(mode="EDIT")

            if self.is_clean_koikatsu_armature:
                mmd_armature_object.clean_koikatsu_armature()

            if self.is_clean_armature:
                mmd_armature_object.clean_armature()

            if not mmd_armature_object.has_face_bones():
                metarig_object.remove_face_bones()

            metarig_object.fit_bones(mmd_armature_object, self.use_mmd_orientation)

            bpy.ops.object.mode_set(mode="POSE")
            metarig_object.set_rigify_parameters(mmd_armature_object)

            bpy.ops.object.mode_set(mode="OBJECT")

            return {"FINISHED"}

        except KeyError as e:
            self.report(type={"ERROR"}, message=f"This armature does not have required MMD bone: {e}")
            return {"CANCELLED"}


class MMDRigifyOperatorABC:
    @classmethod
    def find_armature_objects(cls, objects: Iterable[bpy.types.Object]) -> Tuple[Optional[bpy.types.Object], Optional[bpy.types.Object]]:
        mmd_tools = import_mmd_tools()

        rigify_object: Optional[bpy.types.Object] = None
        mmd_object: Optional[bpy.types.Object] = None

        for obj in objects:
            if obj.type != "ARMATURE":
                continue

            if "rig_id" in obj.data:
                rigify_object = obj
                continue

            mmd_root = mmd_tools.core.model.FnModel.find_root_object(obj)
            if mmd_root is not None:
                mmd_object = obj
                continue

        return (rigify_object, mmd_object)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != "OBJECT":
            return False

        selected_objects = bpy.context.selected_objects
        if len(selected_objects) != 2:
            return False

        rigify_armature_object, mmd_armature_object = cls.find_armature_objects(selected_objects)

        return rigify_armature_object is not None and mmd_armature_object is not None

    @staticmethod
    def adjust_bone_collections(
        rigify_armature_object: RigifyArmatureObject,
        mmd_armature_object: MMDArmatureObject,
    ):
        # rename MMD bone collection already exists in Rigify bone collection
        rig_bone_collections = rigify_armature_object.bone_collections
        rig_bone_collection_names = rig_bone_collections.keys()

        mmd_bone_collections = mmd_armature_object.bone_collections
        for mmd_bone_collection_name in mmd_bone_collections.keys():
            if "mmd_" in mmd_bone_collection_name:
                # ignore "mmd_shadow" and "mmd_dummy"
                # "mmd_shadow" and "mmd_dummy" in Rigify armature will be integrated to that of MMD armature.
                continue
            if mmd_bone_collection_name in rig_bone_collection_names:
                mmd_bone_collections[mmd_bone_collection_name].name = mmd_bone_collection_name + " (MMD)"

    @staticmethod
    def join_armatures(
        rigify_armature_object: RigifyArmatureObject,
        mmd_armature_object: MMDArmatureObject,
    ):
        mmd_armature = mmd_armature_object.raw_armature
        mmd_bind_bones = mmd_armature_object.exist_actual_bone_names

        bcol_prop_name = rigify_armature_object.prop_name_mmd_bcol_category
        bcol_categories = rigify_armature_object.mmd_bcol_categories

        # show "Others" bones only
        show_bone_collection_names: list[str] = []
        for bone_collection in mmd_armature.collections:
            if not bone_collection.bones:
                # if Collection is empty
                continue

            if "mmd_" in bone_collection.name:
                # mmd_shadow/mmd_dummy or Collection is empty
                bone_collection[bcol_prop_name] = bcol_categories["S/D"]
                continue

            bone_names = [s.name for s in bone_collection.bones]
            if set(bone_names).isdisjoint(mmd_bind_bones):
                # if Collection doesn't contain "Main" bones
                show_bone_collection_names.append(bone_collection.name)
                bone_collection[bcol_prop_name] = bcol_categories["O"]  # Others
            else:
                bone_collection[bcol_prop_name] = bcol_categories["M"]  # Main

        # join armatures
        rigify_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        rig_id = rigify_armature["rig_id"]

        bpy.context.view_layer.objects.active = mmd_armature_object.raw_object
        bpy.ops.object.join()
        mmd_armature["rig_id"] = rig_id
        mmd_armature_object.raw_object.display_type = "WIRE"

        SKIP_COLLECTION_NAMES = [
            "Face",
            "Torso",
            "Torso (Tweak)",
            "Fingers",
            "Arm.L (IK)",
            "Arm.R (IK)",
            "Arm.L (FK)",
            "Arm.R (FK)",
            "Leg.L (IK)",
            "Leg.R (IK)",
            "Root",
        ]

        for bone_collection in mmd_armature.collections:
            if bone_collection.name in show_bone_collection_names:
                bone_collection.is_visible = True
            elif bone_collection.name not in SKIP_COLLECTION_NAMES:
                bone_collection.is_visible = False

        mmd_armature_object.raw_object.show_in_front = True

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)


class MMDRigifyIntegrateFocusOnMMD(MMDRigifyOperatorABC, bpy.types.Operator):
    bl_idname = "mmd_tools_append.mmd_rigify_mmd_focused_integrate"
    bl_label = "MMD compatibility focused Integrate"
    bl_description = "Combine Rigify rig and MMD armature"
    bl_options = {"REGISTER", "UNDO"}

    is_join_armatures: bpy.props.BoolProperty(
        name="Join Armatures",
        description="Join MMD and Rigify armatures",
        default=True,
    )
    bind_leg_d: bpy.props.BoolProperty(
        name="Bind Leg D bones",
        description="Bind leg bones to leg D bones (e.g. 足首D) to prevent leg IK shifting",
        default=False,
    )

    @staticmethod
    def set_bone_collections(rigify_armature_object: bpy.types.Object):
        rig_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        for collection in rig_armature.collections:
            if collection.name in {
                "Face",
                "Torso",
                "Torso (Tweak)",
                "Fingers",
                "Arm.L (FK)",
                "Arm.R (FK)",
                "Leg.L (IK)",
                "Leg.R (IK)",
                "Root",
            }:
                collection.is_visible = True
            else:
                collection.is_visible = False

    def execute(self, context: bpy.types.Context):
        rigify_armature_raw_object, mmd_armature_raw_object = self.find_armature_objects(context.selected_objects)

        rigify_armature_object = MMDRigifyArmatureObject(rigify_armature_raw_object)
        mmd_armature_object = MMDArmatureObject(mmd_armature_raw_object)

        rigify_armature_object.bone_collections.new("mmd_dummy")
        rigify_armature_object.bone_collections.new("mmd_shadow")

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.remove_unused_face_bones()
        rigify_armature_object.fit_bone_rotations(mmd_armature_object)
        rigify_armature_object.imitate_mmd_bone_structure_focus_on_mmd(mmd_armature_object)

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior_focus_on_mmd()
        rigify_armature_object.bind_bones(mmd_armature_object, self.bind_leg_d)

        bpy.ops.object.mode_set(mode="OBJECT")
        self.set_bone_collections(rigify_armature_object)

        if self.is_join_armatures:
            self.adjust_bone_collections(rigify_armature_object, mmd_armature_object)
            self.join_armatures(rigify_armature_object, mmd_armature_object)
            rigify_armature_object = MMDRigifyArmatureObject(mmd_armature_raw_object)

        rigify_armature_object.assign_mmd_bone_names()

        return {"FINISHED"}


class MMDRigifyIntegrateFocusOnRigify(MMDRigifyOperatorABC, bpy.types.Operator):
    bl_idname = "mmd_tools_append.mmd_rigify_rigify_focused_integrate"
    bl_label = "Rigify operability focused Integrate"
    bl_description = "Combine Rigify rig and MMD armature"
    bl_options = {"REGISTER", "UNDO"}

    is_join_armatures: bpy.props.BoolProperty(
        name="Join Armatures",
        description="Join MMD and Rigify armatures",
        default=True,
    )
    bind_leg_d: bpy.props.BoolProperty(
        name="Bind Leg D bones",
        description="Bind leg bones to leg D bones (e.g. 足首D) to prevent leg IK shifting",
        default=True,
    )
    rename_mmd_bones: bpy.props.BoolProperty(
        name="Rename MMD bones",
        description="Add MMD bone names to Rigify armatures",
        default=False,
    )

    @staticmethod
    def set_bone_collections(rigify_armature_object: bpy.types.Object):
        rig_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        for collection in rig_armature.collections:
            if collection.name in {
                "Face",
                "Torso",
                "Fingers",
                "Arm.L (IK)",
                "Arm.R (IK)",
                "Leg.L (IK)",
                "Leg.R (IK)",
                "Root",
            }:
                collection.is_visible = True
            else:
                collection.is_visible = False

    def execute(self, context: bpy.types.Context):
        rigify_armature_raw_object, mmd_armature_raw_object = self.find_armature_objects(context.selected_objects)

        rigify_armature_object = MMDRigifyArmatureObject(rigify_armature_raw_object)
        mmd_armature_object = MMDArmatureObject(mmd_armature_raw_object)

        # for foot dummy bone
        rigify_armature_object.bone_collections.new("mmd_dummy")

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.remove_unused_face_bones()
        rigify_armature_object.fit_bone_rotations(mmd_armature_object)
        rigify_armature_object.imitate_mmd_bone_structure_focus_on_rigify(mmd_armature_object)

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior_focus_on_rigify()
        rigify_armature_object.bind_bones(mmd_armature_object, self.bind_leg_d)

        bpy.ops.object.mode_set(mode="OBJECT")
        self.set_bone_collections(rigify_armature_object)

        if self.is_join_armatures:
            self.adjust_bone_collections(rigify_armature_object, mmd_armature_object)
            self.join_armatures(
                rigify_armature_object,
                mmd_armature_object,
            )
            rigify_armature_object = MMDRigifyArmatureObject(mmd_armature_raw_object)

        if self.rename_mmd_bones:
            rigify_armature_object.assign_mmd_bone_names()

        return {"FINISHED"}


class MMDRigifyConvert(bpy.types.Operator):
    bl_idname = "mmd_tools_append.rigify_to_mmd_compatible"
    bl_label = "Convert Rigify Armature to MMD compatible"
    bl_options = {"REGISTER", "UNDO"}

    upper_body2_bind_bone: bpy.props.EnumProperty(
        name="Upper Body2 as",
        items=[
            ("spine_fk.002", "spine_fk.002", ""),
            ("spine_fk.003", "spine_fk.003", ""),
            ("chest", "chest", ""),
        ],
        default="spine_fk.002",
    )

    lower_body_bind_bone: bpy.props.EnumProperty(
        name="Lower Body as",
        items=[
            ("spine_fk", "spine_fk", ""),
            ("hips", "hips", ""),
        ],
        default="spine_fk",
    )

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False

        active_object = context.active_object

        return RigifyArmatureObject.is_rigify_armature_object(active_object) and not MMDRigifyArmatureObject.is_mmd_integrated_object(active_object)

    def execute(self, context: bpy.types.Context):
        rigify_armature_object = RigifyArmatureObject(context.active_object)

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.imitate_mmd_bone_structure()

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior()

        bpy.ops.object.mode_set(mode="OBJECT")
        rigify_armature_object.assign_mmd_bone_names(
            mmd2pose_bone_name_overrides={
                "上半身2": self.upper_body2_bind_bone,
                "下半身": self.lower_body_bind_bone,
            }
        )
        return {"FINISHED"}


class MMDRigifyDerigger(bpy.types.Operator):
    bl_idname = "mmd_tools_append.rigify_derigger"
    bl_label = "Remove rig from armature"
    bl_description = "Remove non-deform bones from armature. Works for non-Rigify rigs as well.\nMay break bone structure"
    bl_options = {"REGISTER", "UNDO"}

    remove_constraints: bpy.props.BoolProperty(name="Remove Bone Constraints", default=True)
    remove_driver: bpy.props.BoolProperty(name="Remove all drivers in Armature", default=True)
    remove_prefix: bpy.props.BoolProperty(name="Remove Rigify prefixes", description="Remove Rigify prefixes (DEF-)", default=True)
    cleanup: bpy.props.BoolProperty(name="Fix Rigify Bone structure", description="Only works for Rigify", default=True)
    unlock_bones: bpy.props.BoolProperty(name="Unlock Bones", description="Unlock all bone transformations (translations, rotations, scales)", default=True)

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = RigifyArmatureObject(context.active_object)

            bpy.ops.object.mode_set(mode="EDIT")
            removed_count = rigify_armature_object.derig(self.remove_constraints, self.remove_driver, self.remove_prefix, self.cleanup, self.unlock_bones)

            self.report({"INFO"}, message=f"Removed {removed_count} bones.")

        except Exception as e:
            self.report({"ERROR"}, message=f"Failed to remove rig: {e}")
            return {"CANCELLED"}
        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class MMDRigifyTranslator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.rigify_translator"
    bl_label = "Translate Rigify names to MMD"
    bl_description = "Translate Rigify metarig bone names to MMD"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = RigifyArmatureObject(context.active_object)

            bpy.ops.object.mode_set(mode="EDIT")
            translated_count = rigify_armature_object.translate_rigify()
            self.report({"INFO"}, message=f"Translated {translated_count} bones.")

        except Exception as e:
            self.report({"ERROR"}, message=f"Failed to translate bones: {e}")
            return {"CANCELLED"}
        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class MMDRigifyApplyMMDRestPose(bpy.types.Operator):
    bl_idname = "mmd_tools_append.rigify_apply_mmd_rest_pose"
    bl_label = "Apply MMD Rest Pose"
    bl_options = {"REGISTER", "UNDO"}

    iterations: bpy.props.IntProperty(
        name="Iterations",
        description="Number of solving iterations",
        default=7,
        min=1,
        max=100,
    )
    pose_arms: bpy.props.BoolProperty(name="Pose arms", default=True)
    pose_legs: bpy.props.BoolProperty(name="Pose legs", default=True)
    pose_fingers: bpy.props.BoolProperty(name="Pose fingers", default=False)

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        return RigifyArmatureObject.is_rigify_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = RigifyArmatureObject(context.active_object)
            dependency_graph = context.evaluated_depsgraph_get()

            bpy.ops.object.mode_set(mode="POSE")
            rigify_armature_object.pose_mmd_rest(
                dependency_graph,
                self.iterations,
                pose_arms=self.pose_arms,
                pose_legs=self.pose_legs,
                pose_fingers=self.pose_fingers,
            )

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class MMDAutoRigConvert(bpy.types.Operator):
    bl_idname = "mmd_tools_append.autorig_to_mmd_compatible"
    bl_label = "Convert AutoRig Armature to MMD compatible"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False

        active_object = context.active_object

        return AutoRigArmatureObject.is_autorig_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        autorig_armature_object = AutoRigArmatureObject(context.active_object)

        bpy.ops.object.mode_set(mode="EDIT")
        autorig_armature_object.imitate_mmd_bone_structure()

        bpy.ops.object.mode_set(mode="POSE")
        autorig_armature_object.imitate_mmd_pose_behavior()

        bpy.ops.object.mode_set(mode="OBJECT")
        autorig_armature_object.assign_mmd_bone_names()
        return {"FINISHED"}


class MMDAutoRigApplyMMDRestPose(bpy.types.Operator):
    bl_idname = "mmd_tools_append.autorig_apply_mmd_rest_pose"
    bl_label = "Apply MMD Rest Pose"
    bl_options = {"REGISTER", "UNDO"}

    iterations: bpy.props.IntProperty(
        name="Iterations",
        description="Number of solving iterations",
        default=7,
        min=1,
        max=100,
    )
    pose_arms: bpy.props.BoolProperty(name="Pose arms", default=True)
    pose_legs: bpy.props.BoolProperty(name="Pose legs", default=True)
    pose_fingers: bpy.props.BoolProperty(name="Pose fingers", default=False)

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        return AutoRigArmatureObject.is_autorig_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = AutoRigArmatureObject(context.active_object)
            dependency_graph = context.evaluated_depsgraph_get()

            bpy.ops.object.mode_set(mode="POSE")
            rigify_armature_object.pose_mmd_rest(
                dependency_graph,
                self.iterations,
                pose_arms=self.pose_arms,
                pose_legs=self.pose_legs,
                pose_fingers=self.pose_fingers,
            )

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class HumanoidInitializeOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_initialize"
    bl_label = "Initialize Humanoid Renamer"
    bl_description = "Initialize MMD compatible Humanoid structure data for renaming bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        try:
            context.active_object.mmd_tools_append_humanoid_settings.initialize_humanoid()
        except MessageException as ex:
            self.report({"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        return {"FINISHED"}


class HumanoidResetOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_reset"
    bl_label = "Reset Humanoid Renamer"
    bl_description = "Reset Humanoid structure data"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        try:
            context.active_object.mmd_tools_append_humanoid_settings.reset_humanoid()
            self.report({"INFO"}, message="Reset Humanoid data.")
        except MessageException as ex:
            self.report({"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        return {"FINISHED"}


class HumanoidAutoOrientationOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_auto_orientation"
    bl_label = "Automatic Orientation"
    bl_description = "Automatically set bone orientation based on child bone"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            editor = HumanoidEditor(context.active_object)

            bpy.ops.object.mode_set(mode="EDIT")
            editor.auto_orientation()

        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class HumanoidDetectOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_detect"
    bl_label = "Automatic Humanoid Detection"
    bl_description = "Analyze the bone position, direction, structure and name to find Humanoid structure.\nIntended for non-MMD models, and the model must face Y- direction"
    bl_options = {"REGISTER", "UNDO"}

    threshold: bpy.props.FloatProperty(
        name="Distance Tolerance",
        description="Determines the precision of the bone distance measurement. Adjust this if the bone detection fails",
        precision=4,
        min=0.0001,
        max=1.0,
        default=0.0001,
    )

    finger_count: bpy.props.IntProperty(
        name="Finger Count",
        description="The number of fingers",
        min=1,
        soft_max=6,
        default=5,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            editor = HumanoidEditor(context.active_object)

            bpy.ops.object.mode_set(mode="EDIT")
            editor.detect(finger_count=self.finger_count, fine_precision=self.threshold)
            for frame, item in editor.tree.iter_items():
                item.auto(editor, frame.display_type)

        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class HumanoidRenameOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_rename"
    bl_label = "Humanoid Rename"
    bl_description = "Rename selected bones to MMD compatible Japanese name"
    bl_options = {"REGISTER", "UNDO"}

    convert_armature: bpy.props.BoolProperty(
        name="Convert Model",
        description="Convert armature to MMD model",
        default=True,
    )
    use_leg_ik: bpy.props.BoolProperty(
        name="Use Leg IK",
        description="Add Leg IK to MMD rig. (ignored if Convert Model is disabled)",
        default=True,
    )
    add_eye: bpy.props.BoolProperty(
        name="Add Eyes Bone",
        description="Add eyes (両目) bone to MMD rig. (ignored if Convert Model is disabled)",
        default=True,
    )
    use_local_axis: bpy.props.BoolProperty(
        name="Use Local axis",
        description="Set up local axis for arms and fingers. (ignored if Convert Model is disabled)",
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object
        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def draw(self, _context: bpy.types.Context):
        layout = self.layout
        layout.use_property_split = True

        col = layout.column(align=False)
        col.prop(self, "convert_armature")
        col = layout.column(align=False)
        col.prop(self, "use_leg_ik")
        col.prop(self, "add_eye")
        col.prop(self, "use_local_axis")
        col.active = self.convert_armature

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            editor = HumanoidEditor(context.active_object)
            dups = editor.tree.get_duplicates()
            if dups:
                for k, v in dups.items():
                    self.report({"WARNING"}, message=f"Bone {k} was selected {v} times.")

            bpy.ops.object.mode_set(mode="EDIT")
            rename_count = editor.rename()

            if self.convert_armature:
                editor.to_mmd_pose(self.use_local_axis)
                if self.use_leg_ik:
                    editor.add_leg_ik()
                if self.add_eye:
                    editor.add_eyes_bone()

                bpy.ops.object.mode_set(mode="OBJECT")
                if not editor.is_mmd_armature_object:
                    bpy.ops.mmd_tools.convert_to_mmd_model(
                        ambient_color_source="DIFFUSE",
                        edge_threshold=0.1,
                        edge_alpha_min=0.5,
                        scale=0.08,
                        convert_material_nodes=True,
                        middle_joint_bones_lock=False,
                    )
                bpy.ops.mmd_tools.display_item_quick_setup(type="GROUP_LOAD")
                bpy.ops.mmd_tools.fix_bone_order()

            if dups:
                self.report({"WARNING"}, message=f"Renamed {rename_count} bones with {len(dups)} duplicates. (click to see details)")
            else:
                self.report({"INFO"}, message=f"Renamed {rename_count} bones.")
        except KeyError as e:
            self.report(type={"ERROR"}, message=f"This armature does not have required MMD bones. {e}")
            return {"CANCELLED"}
        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        finally:
            if context.active_object.type == "ARMATURE":
                bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
