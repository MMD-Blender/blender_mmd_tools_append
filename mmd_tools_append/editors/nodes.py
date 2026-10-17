# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import os
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

import bpy

from .. import PACKAGE_PATH
from ..utilities import raise_installation_error

PATH_BLENDS_MMD_APPEND_MATERIALS = os.path.join(PACKAGE_PATH, "blends", "MMDAppend_Materials.blend")


class NodeEditor(ABC):
    def __init__(self, node_tree: bpy.types.NodeTree) -> None:
        super().__init__()
        self.node_tree = node_tree
        self.nodes = node_tree.nodes
        self.links = node_tree.links

    @staticmethod
    def to_name(label: str) -> str:
        return label.replace(" ", "_").lower()

    @staticmethod
    def grid_to_position(grid_x: int, grid_y: int) -> tuple[int, int]:
        return (grid_x * 100, (grid_y - 3) * 100)

    _library_blend_file_path = str
    _node_group_type = type

    def append_node_group(self, name: str):
        if name in bpy.data.node_groups:
            return

        try:
            with bpy.data.libraries.load(self._library_blend_file_path, link=False) as (_, data_to):
                data_to.node_groups = [name]
        except OSError as exception:
            raise_installation_error(exception)

    @abstractmethod
    def get_output_node(self) -> bpy.types.Node:
        pass

    def list_nodes(self, node_type: type = None, label: str = None, name: str = None, node_frame: bpy.types.NodeFrame = None) -> Iterable[bpy.types.Node]:
        node: bpy.types.Node
        for node in self.nodes:
            if node_type is not None and not isinstance(node, node_type):
                continue

            if label is not None and node.label != label:
                continue

            if name is not None and node.name != name:
                continue

            if node_frame is not None and node.parent != node_frame:
                continue

            yield node

    @staticmethod
    def check_setting_node(node: bpy.types.Node) -> bool:
        return node.label

    @staticmethod
    def to_link_or_value(node_socket: bpy.types.NodeSocket):
        if not node_socket.is_linked:
            return node_socket.default_value

        return node_socket.links[0].from_socket

    def find_node(self, node_type: type, label: str = None, name: str = None, node_frame: bpy.types.NodeFrame = None) -> bpy.types.Node:
        return next(self.list_nodes(node_type, label, name, node_frame), None)

    def new_node(self, node_type: type, label: str = None, name: str = None) -> bpy.types.Node:
        node = self.nodes.new(node_type.__name__)
        node.label = label if label is not None else ""
        node.name = name if name is not None else self.to_name(label)
        return node

    def get_node(self, node_type: type, label: str = None, name: str = None) -> bpy.types.Node:
        node = self.find_node(node_type, label, name)
        if node is not None:
            return node

        return self.new_node(node_type, label, name)

    def get_node_frame(self, label: str = None, names: list[str] = ["mmd_append_node_frame", "uuunyaa_node_frame"]) -> bpy.types.NodeFrame:
        for name in names:
            node = self.get_node(bpy.types.NodeFrame, label=label, name=name)
            if node:
                return node

    def find_node_frame(self, label: str = None, names: list[str] = ["mmd_append_node_frame", "uuunyaa_node_frame"]) -> bpy.types.NodeFrame:
        for name in names:
            node = self.find_node(bpy.types.NodeFrame, label=label, name=name)
            if node:
                return node

    def remove_node_frame(self, node_frame: bpy.types.NodeFrame):
        for node in self.list_nodes(node_frame=node_frame):
            self.nodes.remove(node)
        self.nodes.remove(node_frame)

    def get_node_group(self, group_name: str, label: str = None, name: str = None) -> bpy.types.NodeGroup:
        self.append_node_group(group_name)
        node: bpy.types.NodeGroup = self.get_node(self._node_group_type, label, name)
        node.node_tree = bpy.data.node_groups[group_name]
        return node

    def edit(self, node: bpy.types.Node, inputs: dict[str, Any] = {}, properties: dict[str, Any] = {}, force=False) -> bpy.types.Node:
        # pylint: disable=dangerous-default-value
        # because readonly
        if node is None:
            return None

        self.set_node_inputs(node, inputs, force)
        for name, value in properties.items():
            setattr(node, name, value)
        return node

    def set_node_inputs(self, node: bpy.types.Node, values: dict[str, Any], force=False) -> bpy.types.Node:
        for key, value in values.items():
            if isinstance(value, bpy.types.NodeSocket):
                if force or not node.inputs[key].is_linked:
                    self.links.new(value, node.inputs[key])
            else:
                node.inputs[key].default_value = value
        return node

    _adjusters_node_frame_label = "MMD Append Adjusters"
    _adjusters_node_frame_name = ["mmd_append_adjusters_node_frame", "uuunyaa_adjusters_node_frame"]

    def find_adjusters_node_frame(self) -> bpy.types.NodeFrame:
        return self.find_node_frame(label=self._adjusters_node_frame_label, names=self._adjusters_node_frame_name)

    def get_adjusters_node_frame(self) -> bpy.types.NodeFrame:
        return self.get_node_frame(label=self._adjusters_node_frame_label, names=self._adjusters_node_frame_name)


class MaterialEditor(NodeEditor):
    # pylint: disable=too-many-public-methods

    @staticmethod
    def srgb_to_linearrgb(color: float) -> float:
        if color < 0:
            return 0
        if color < 0.04045:
            return color / 12.92
        return ((color + 0.055) / 1.055) ** 2.4

    @staticmethod
    def to_link_or_rgb(color: bpy.types.NodeSocket | tuple[float, float, float, float]) -> bpy.types.NodeSocket | tuple[float, float, float]:
        if isinstance(color, bpy.types.NodeSocket):
            return color

        if len(color) >= 3:
            return tuple(MaterialEditor.srgb_to_linearrgb(c) for c in color[:3])

        raise ValueError("color must be a NodeSocket or a sequence of at least three floats")

    @staticmethod
    def to_link_or_rgba(color: bpy.types.NodeSocket | tuple[float, float, float], alpha=1.0) -> bpy.types.NodeSocket | tuple[float, float, float, float]:
        if isinstance(color, bpy.types.NodeSocket):
            return color

        if len(color) >= 3:
            return tuple([MaterialEditor.srgb_to_linearrgb(c) for c in color[:3]] + [alpha])

        raise ValueError("color must be a NodeSocket or a sequence of at least three floats")

    @staticmethod
    def hex_to_rgb(hex_int: int) -> tuple[float, float, float]:
        # pylint: disable=invalid-name
        # r,g,b is commonly used
        r = (hex_int & 0xFF0000) >> 16
        g = (hex_int & 0x00FF00) >> 8
        b = hex_int & 0x0000FF
        return tuple(MaterialEditor.srgb_to_linearrgb(c / 0xFF) for c in (r, g, b))

    @staticmethod
    def hex_to_rgba(hex_int: int, alpha=1.0) -> tuple[float, float, float, float]:
        # pylint: disable=invalid-name
        # r,g,b is commonly used
        r = (hex_int & 0xFF0000) >> 16
        g = (hex_int & 0x00FF00) >> 8
        b = hex_int & 0x0000FF
        return tuple([MaterialEditor.srgb_to_linearrgb(c / 0xFF) for c in (r, g, b)] + [alpha])

    _library_blend_file_path = PATH_BLENDS_MMD_APPEND_MATERIALS
    _node_group_type = bpy.types.ShaderNodeGroup

    def __init__(self, material: bpy.types.Material):
        super().__init__(material.node_tree)
        self.material = material

    def get_output_node(self) -> bpy.types.ShaderNodeOutputMaterial:
        node_output = next((n for n in self.nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial) and n.is_active_output), None)
        if node_output is None:
            node_output = self.nodes.new(bpy.types.ShaderNodeOutputMaterial.__name__)
            node_output.is_active_output = True
        return node_output

    def get_shader_node(self) -> bpy.types.ShaderNodeBsdfPrincipled:
        return self.get_node(bpy.types.ShaderNodeBsdfPrincipled, label="Principled BSDF")

    def get_glass_bsdf_node(self) -> bpy.types.ShaderNodeBsdfGlass:
        return self.get_node(bpy.types.ShaderNodeBsdfGlass, label="Glass BSDF")

    def get_transparent_bsdf_node(self) -> bpy.types.ShaderNodeBsdfTransparent:
        return self.get_node(bpy.types.ShaderNodeBsdfTransparent, label="Transparent BSDF")

    def get_mix_shader_node(self) -> bpy.types.ShaderNodeMixShader:
        return self.get_node(bpy.types.ShaderNodeMixShader, label="Mix Shader")

    def find_mmd_shader_node(self) -> bpy.types.ShaderNodeGroup:
        return self.find_node(bpy.types.ShaderNodeGroup, name="mmd_shader")

    def find_principled_shader_node(self) -> bpy.types.ShaderNodeBsdfPrincipled:
        return self.find_node(bpy.types.ShaderNodeBsdfPrincipled, label="", name="Principled BSDF")

    def find_active_principled_shader_node(self) -> bpy.types.ShaderNodeBsdfPrincipled | None:
        node_output = self.get_output_node()
        node_socket = node_output.inputs["Surface"]
        node_socket_links = node_socket.links

        if len(node_socket_links) == 0:
            return None

        node_from = node_socket_links[0].from_node

        if isinstance(node_from, bpy.types.ShaderNodeBsdfPrincipled):
            return node_from

        return None

    def new_bump_node(self) -> bpy.types.ShaderNodeBump:
        return self.new_node(bpy.types.ShaderNodeBump, label="Bump")

    def new_math_node(self) -> bpy.types.ShaderNodeMath:
        return self.new_node(bpy.types.ShaderNodeMath, label="Math")

    def get_vertex_color_node(self) -> bpy.types.ShaderNodeVertexColor:
        return self.get_node(bpy.types.ShaderNodeVertexColor, label="Vertex Color")

    def get_mmd_shader_node(self) -> bpy.types.ShaderNodeGroup:
        return self.find_node(bpy.types.ShaderNodeGroup, name="mmd_shader")

    def get_base_texture_node(self) -> bpy.types.ShaderNodeTexImage:
        return self.find_node(bpy.types.ShaderNodeTexImage, label="Mmd Base Tex")

    def get_diffuse_color_node(self) -> bpy.types.ShaderNodeGroup | bpy.types.ShaderNodeTexImage | None:
        mmd_shader_node = self.get_mmd_shader_node()
        if mmd_shader_node and "Color" in mmd_shader_node.outputs:
            return mmd_shader_node

        return self.get_base_texture_node()

    def get_skin_color_adjust_node(self) -> bpy.types.ShaderNodeRGBCurve:
        return self.get_node_group("Skin Color Adjust", label="Skin Color Adjust")

    def get_skin_bump_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Skin Bump", label="Skin Bump")

    def get_fabric_woven_texture_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Fabric Woven Texture", label="Fabric Woven Texture")

    def get_fabric_bump_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Fabric Bump", label="Fabric Bump")

    def get_wave_bump_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Wave Bump", label="Wave Bump")

    def get_magic_bump_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Magic Bump", label="Magic Bump")

    def get_shadowless_bsdf_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Shadowless BSDF", label="Shadowless BSDF")

    def get_gem_bsdf_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Gem BSDF", label="Gem BSDF")

    def get_liquid_bsdf_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Liquid BSDF", label="Liquid BSDF")

    def get_knit_texture_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Knit Texture", label="Knit Texture")

    def get_leather_texture_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Leather Texture", label="Leather Texture")

    def get_watercolor_texture_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Watercolor Texture", label="Watercolor Texture")

    def get_toon_shader_texture_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Toon Shader Texture", label="Toon Shader Texture")

    def get_tex_uv(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("MMDTexUV", name="mmd_tex_uv")

    def get_subsurface_adjuster_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Subsurface Adjuster", label="Subsurface Adjuster")

    def get_wet_adjuster_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Wet Adjuster", label="Wet Adjuster")

    def get_emission_adjuster_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Emission Adjuster", label="Emission Adjuster")

    def get_glitter_adjuster_node(self) -> bpy.types.ShaderNodeGroup:
        return self.get_node_group("Glitter Adjuster", label="Glitter Adjuster")

    def reset(self):
        node_frame = self.find_adjusters_node_frame()
        if node_frame is not None:
            self.remove_node_frame(node_frame)

        node_frame = self.find_node_frame()
        if node_frame is None:
            return

        self.remove_node_frame(node_frame)

        self.set_material_properties(
            {
                "blend_method": "HASHED",
                "use_screen_refraction": False,
                "refraction_depth": 0.000,
            }
        )

    def set_material_properties(self, properties: dict[str, Any] = {}):
        # pylint: disable=dangerous-default-value
        # because readonly
        for name, value in properties.items():
            setattr(self.material, name, value)
        return self

    def set_mmd_toon_fac(self, value: float):
        mmd_shader_node = self.get_mmd_shader_node()
        if mmd_shader_node and "Toon Tex Fac" in mmd_shader_node.inputs:
            mmd_shader_node.inputs["Toon Tex Fac"].default_value = value

    def set_mmd_sphere_fac(self, value: float):
        mmd_shader_node = self.get_mmd_shader_node()
        if mmd_shader_node and "Sphere Tex Fac" in mmd_shader_node.inputs:
            mmd_shader_node.inputs["Sphere Tex Fac"].default_value = value

    def draw_setting_shader_node_properties(self, layout: bpy.types.UILayout, nodes: Iterable[bpy.types.ShaderNode]):
        for node in nodes:
            if isinstance(node, bpy.types.ShaderNodeGroup):
                pass
            elif self.check_setting_node(node):
                pass
            else:
                continue
            col = layout.box().column(align=True)
            col.label(text=node.label)
            if isinstance(node, bpy.types.ShaderNodeValue):
                for node_output in node.outputs:
                    col.prop(node_output, "default_value", text=node_output.name)
            elif isinstance(node, bpy.types.ShaderNodeTexSky):
                if node.sky_type == "HOSEK_WILKIE":
                    col.label(text="Sun Direction")
                    col.prop(node, "sun_direction", text="")
                    col.prop(node, "turbidity")
                    col.prop(node, "ground_albedo")
            else:
                for node_input in node.inputs:
                    if node_input.is_linked:
                        continue
                    col.prop(node_input, "default_value", text=node_input.name)

    def copy_node_group_inputs(self, source):
        src_editor = MaterialEditor(source)

        dst_node_frame = self.find_node_frame()
        src_node_frame = src_editor.find_node_frame()
        if src_node_frame is None or dst_node_frame is None:
            return

        src_groups = list(src_editor.list_nodes(node_type=bpy.types.ShaderNodeGroup, node_frame=src_node_frame))
        dst_groups = list(self.list_nodes(node_type=bpy.types.ShaderNodeGroup, node_frame=dst_node_frame))

        src_dict = {node.name: node for node in src_groups}
        for dst_node in dst_groups:
            src_node = src_dict.get(dst_node.name)
            if src_node is None:
                continue
            for src_input, dst_input in zip(src_node.inputs, dst_node.inputs):
                try:
                    dst_input.default_value = src_input.default_value
                except Exception as e:
                    print(f"WARNING: skipped copying node value due to an exception: {e}")
