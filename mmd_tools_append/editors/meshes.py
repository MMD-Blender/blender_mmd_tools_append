# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

from collections.abc import Iterable
from typing import Any, Optional

import bpy

SettingsOrNone = Optional[dict[str, Any]]


class MeshEditor:
    # pylint: disable=too-many-public-methods

    def __init__(self, mesh_object: bpy.types.Object):
        self.mesh_object = mesh_object

    def link_to_active_collection(self):
        self.link_to(bpy.context.view_layer.active_layer_collection.collection)

    def link_to(self, collection: bpy.types.Collection):
        collection.objects.link(self.mesh_object)

    @staticmethod
    def edit_modifier(modifier: bpy.types.Modifier, settings: SettingsOrNone = None, **kwargs) -> bpy.types.Modifier:
        for key, value in kwargs.items():
            if not hasattr(modifier, key):
                print(f'WARN: {modifier} modifier has no attribute "{key}"')
                continue

            setattr(modifier, key, value)

        if settings is None:
            return modifier

        for key, value in settings.items():
            if not hasattr(modifier.settings, key):
                print(f'WARN: {modifier.settings} object has no attribute "{key}"')
                continue

            setattr(modifier.settings, key, value)

        return modifier

    def add_modifier(self, modifier_type: str, name: str, settings: SettingsOrNone = None, **kwargs) -> bpy.types.Modifier:
        return self.edit_modifier(self.mesh_object.modifiers.new(name, modifier_type), settings=settings, **kwargs)

    def add_subsurface_modifier(self, name: str, levels: int, render_levels: int, **kwargs) -> bpy.types.SubsurfModifier:
        return self.add_modifier(
            "SUBSURF",
            name,
            levels=levels,
            render_levels=render_levels,
            boundary_smooth="PRESERVE_CORNERS",
            show_only_control_edges=False,
            **kwargs,
        )

    def find_subsurface_modifier(self, name: str) -> bpy.types.SubsurfModifier | None:
        for modifier in self.mesh_object.modifiers:
            if modifier.type == "SUBSURF" and modifier.name == name:
                return modifier
        return None

    def get_subsurface_modifier(self, name: str) -> bpy.types.Modifier:
        modifier = self.find_subsurface_modifier(name)
        if modifier is None:
            modifier = self.add_subsurface_modifier(name=name, levels=0, render_levels=0)
        return modifier

    def add_armature_modifier(self, name: str, armature_object: bpy.types.Object, **kwargs) -> bpy.types.Modifier:
        return self.add_modifier("ARMATURE", name, object=armature_object, **kwargs)

    def find_armature_modifier(self, name: str | None) -> bpy.types.ArmatureModifier | None:
        for modifier in self.mesh_object.modifiers:
            if modifier.type != "ARMATURE":
                continue

            if name is None or modifier.name == name:
                return modifier

        return None

    def add_corrective_smooth_modifier(self, name: str, **kwargs) -> bpy.types.CorrectiveSmoothModifier:
        return self.add_modifier("CORRECTIVE_SMOOTH", name, **kwargs)

    def find_corrective_smooth_modifier(self) -> bpy.types.CorrectiveSmoothModifier | None:
        return self.find_singleton_modifier("CORRECTIVE_SMOOTH")

    def add_surface_deform_modifier(self, name: str, **kwargs) -> bpy.types.SurfaceDeformModifier:
        return self.add_modifier("SURFACE_DEFORM", name, **kwargs)

    def find_singleton_modifier(self, modifier_type: str) -> bpy.types.Modifier | None:
        if modifier_type not in {"CLOTH", "COLLISION", "CORRECTIVE_SMOOTH", "DYNAMIC_PAINT"}:
            raise NotImplementedError(f"{modifier_type} is not supported.")

        for modifier in self.mesh_object.modifiers:
            if modifier.type == modifier_type:
                return modifier

        return None

    def get_singleton_modifier(self, modifier_type: str, name: str) -> bpy.types.Modifier:
        modifier = self.find_singleton_modifier(modifier_type)
        if modifier is None:
            modifier = self.add_modifier(modifier_type, name=name)
        return modifier

    def edit_singleton_modifier(self, modifier: bpy.types.Modifier, **kwargs) -> bpy.types.Modifier:
        return self.edit_modifier(modifier, settings=kwargs)

    def remove_singleton_modifier(self, modifier_type: str):
        modifier = self.find_singleton_modifier(modifier_type)
        if modifier is None:
            return

        self.mesh_object.modifiers.remove(modifier)

    def find_cloth_modifier(self) -> bpy.types.ClothModifier | None:
        return self.find_singleton_modifier("CLOTH")

    def get_cloth_modifier(self, name: str = "Cloth") -> bpy.types.ClothModifier:
        return self.get_singleton_modifier("CLOTH", name)

    def edit_cloth_modifier(self, name: str, **kwargs) -> bpy.types.ClothModifier:
        return self.edit_singleton_modifier(self.get_cloth_modifier(name), **kwargs)

    def find_cloth_settings(self) -> bpy.types.ClothSettings | None:
        modifier = self.find_cloth_modifier()
        if modifier is None:
            return None
        return modifier.settings

    def find_cloth_collision_settings(self) -> bpy.types.ClothCollisionSettings | None:
        modifier = self.find_cloth_modifier()
        if modifier is None:
            return None
        return modifier.collision_settings

    def remove_cloth_modifier(self):
        self.remove_singleton_modifier("CLOTH")

    def find_collision_modifier(self) -> bpy.types.CollisionModifier | None:
        return self.find_singleton_modifier("COLLISION")

    def find_collision_settings(self) -> bpy.types.CollisionSettings | None:
        modifier = self.find_collision_modifier()
        if modifier is None:
            return None
        return modifier.settings

    def get_collision_modifier(self, name: str = "Collision") -> bpy.types.CollisionModifier:
        return self.get_singleton_modifier("COLLISION", name)

    def edit_collision_modifier(
        self,
        name: str,
        damping: float = 0.1,
        thickness_outer: float = 0.001,
        thickness_inner: float = 0.200,
        cloth_friction: float = 5,
        **kwargs,
    ) -> bpy.types.CollisionModifier:
        # pylint: disable=too-many-arguments
        return self.edit_singleton_modifier(
            self.get_collision_modifier(name),
            damping=damping,
            thickness_outer=thickness_outer,
            thickness_inner=thickness_inner,
            cloth_friction=cloth_friction,
            **kwargs,
        )

    def remove_collision_modifier(self):
        self.remove_singleton_modifier("COLLISION")

    def find_dynamic_paint_modifier(self) -> bpy.types.DynamicPaintModifier | None:
        return self.find_singleton_modifier("DYNAMIC_PAINT")

    def get_dynamic_paint_modifier(self, name: str = "Dynamic Paint") -> bpy.types.DynamicPaintModifier:
        return self.get_singleton_modifier("DYNAMIC_PAINT", name)

    def find_dynamic_paint_brush_settings(self) -> bpy.types.DynamicPaintBrushSettings | None:
        modifier = self.find_dynamic_paint_modifier()
        if modifier is None:
            return None
        return modifier.brush_settings

    def edit_dynamic_paint_brush_settings(self, name: str, **kwargs) -> bpy.types.DynamicPaintModifier:
        modifier = self.get_dynamic_paint_modifier(name)

        for key, value in kwargs.items():
            if not hasattr(modifier.brush_settings, key):
                print(f'WARN: {modifier.brush_settings} object has no attribute "{key}"')
                continue

            setattr(modifier.brush_settings, key, value)

        return modifier

    def find_dynamic_paint_canvas_settings(self) -> bpy.types.DynamicPaintCanvasSettings | None:
        modifier = self.find_dynamic_paint_modifier()
        if modifier is None:
            return None
        return modifier.canvas_settings

    def edit_dynamic_paint_canvas_settings(self, name: str, **kwargs) -> bpy.types.DynamicPaintModifier:
        modifier = self.get_dynamic_paint_modifier(name)

        for key, value in kwargs.items():
            if not hasattr(modifier.canvas_settings, key):
                print(f'WARN: {modifier.canvas_settings} object has no attribute "{key}"')
                continue

            setattr(modifier.canvas_settings, key, value)

        return modifier

    def find_rigid_body_object(self) -> bpy.types.RigidBodyObject | None:
        return self.mesh_object.rigid_body

    @staticmethod
    def mesh_object_is_contained_in(objects: Iterable[bpy.types.Object]):
        for obj in objects:
            if obj.type == "MESH":
                return True

        return False

    def find_vertex_group(self, name: str) -> bpy.types.VertexGroup | None:
        return self.mesh_object.vertex_groups.get(name, None)

    def add_vertex_group(self, name: str) -> bpy.types.VertexGroup:
        return self.mesh_object.vertex_groups.new(name=name)

    def get_vertex_group(self, name: str) -> bpy.types.VertexGroup:
        vertex_group = self.find_vertex_group(name)
        if vertex_group is None:
            vertex_group = self.add_vertex_group(name)
        return vertex_group

    def edit_vertex_group(self, name: str, vertex_weight_operations: list[tuple[list[int], float, str]]):
        vertex_group = self.get_vertex_group(name)
        for vertex_weight_operation in vertex_weight_operations:
            vertex_group.add(
                vertex_weight_operation[0],
                vertex_weight_operation[1],
                vertex_weight_operation[2] if len(vertex_weight_operation) >= 3 else "REPLACE",
            )
        return vertex_group

    def find_armature_object(self) -> bpy.types.Object | None:
        return self.mesh_object.find_armature()


class RigidBodyEditor(MeshEditor):
    @staticmethod
    def rigid_body_object_is_contained_in(objects: Iterable[bpy.types.Object]):
        for obj in objects:
            if obj.type != "MESH":
                return False

            if obj.rigid_body:
                return True

        return False
