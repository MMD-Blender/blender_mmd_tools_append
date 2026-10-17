# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import os

import bpy

from .. import PACKAGE_PATH
from ..tuners import TunerABC, TunerRegistry
from ..tuners.utilities import ObjectAppender, ObjectMarker

PATH_BLENDS_MMD_APPEND_LIGHTINGS = os.path.join(PACKAGE_PATH, "blends", "MMDAppend_Lightings.blend")


class LightingUtilities:
    def __init__(self, collection):
        self.collection = collection
        self.object_appender = ObjectAppender("mmd_tools_append_lighting_mark", PATH_BLENDS_MMD_APPEND_LIGHTINGS)

    @property
    def object_marker(self) -> ObjectMarker:
        return self.object_appender

    def find_active_lighting(self) -> bpy.types.Object | None:
        for obj in self.collection.objects.values():
            if obj.type != "EMPTY" or obj.parent is not None or not self.object_marker.is_marked(obj):
                continue
            return obj

        return None


class LightingTunerABC(TunerABC, LightingUtilities):
    def reset(self):
        self.object_appender.remove_objects(self.collection)

    def add_lights(self, name: str):
        self.object_appender.append_objects_from_collection(name, self.collection)


class ResetLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_RESET"

    @classmethod
    def get_name(cls) -> str:
        return "Reset"

    def execute(self):
        self.reset()


class LeftAccentLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_LEFT_ACCENT"

    @classmethod
    def get_name(cls) -> str:
        return "Left Accent"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


class DoubleSideAccentLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_DOUBLE_SIDE_ACCENT"

    @classmethod
    def get_name(cls) -> str:
        return "Double Side Accent"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


class GodRayLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_GOD_RAY"

    @classmethod
    def get_name(cls) -> str:
        return "God Ray"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


class BacklightLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_BACKLIGHT"

    @classmethod
    def get_name(cls) -> str:
        return "Backlight"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


class LightProbeGridLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_LIGHT_PROBE_GRID"

    @classmethod
    def get_name(cls) -> str:
        return "Light Probe Grid"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


class ShadowlessLightingTuner(LightingTunerABC):
    @classmethod
    def get_id(cls) -> str:
        return "LIGHTING_SHADOWLESS"

    @classmethod
    def get_name(cls) -> str:
        return "Shadowless"

    def execute(self):
        self.reset()
        self.add_lights(self.get_id())


TUNERS = TunerRegistry(
    (0, ResetLightingTuner),
    (1, LeftAccentLightingTuner),
    (5, DoubleSideAccentLightingTuner),
    (2, GodRayLightingTuner),
    (3, BacklightLightingTuner),
    (6, ShadowlessLightingTuner),
    (4, LightProbeGridLightingTuner),
)
