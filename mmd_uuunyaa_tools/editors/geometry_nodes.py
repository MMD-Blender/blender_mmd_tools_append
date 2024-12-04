# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import os
from typing import Iterable

import bpy
from .. import PACKAGE_PATH
from ..editors.nodes import NodeEditor
from ..m17n import _

try:
    from bpy.types import (GeometryNode, GeometryNodeAlignRotationToVector,
                           GeometryNodeGroup, GeometryNodePointInstance,
                           NodeGroupInput, NodeGroupOutput, NodeSocketGeometry,
                           ShaderNodeGroup, ShaderNodeValue)

    PATH_BLENDS_UUUNYAA_GEOMETRIES = os.path.join(PACKAGE_PATH, 'blends', 'UuuNyaa_Geometries.blend')

    class GeometryEditor(NodeEditor):
        # pylint: disable=too-many-public-methods

        _library_blend_file_path = PATH_BLENDS_UUUNYAA_GEOMETRIES
        _node_group_type = GeometryNodeGroup

        def __init__(self, geometry: bpy.types.GeometryNodeTree):
            super().__init__(geometry)

        def get_output_node(self) -> NodeGroupOutput:
            node_output: NodeGroupOutput = next((n for n in self.nodes if isinstance(n, NodeGroupOutput) and n.is_active_output), None)
            if node_output is None:
                node_output = self.nodes.new(NodeGroupOutput.__name__)
                node_output.is_active_output = True
            return node_output

        def get_input_node(self) -> NodeGroupInput:
            node_input: NodeGroupInput = next((n for n in self.nodes if isinstance(n, NodeGroupInput)), None)
            if node_input is None:
                node_input = self.nodes.new(NodeGroupInput.__name__)
            return node_input

        def new_align_rotation_to_vector_node(self) -> GeometryNodeAlignRotationToVector:
            return self.new_node(GeometryNodeAlignRotationToVector, label='Align Rotation to Vector')

        def new_point_instance_node(self) -> GeometryNodePointInstance:
            return self.new_node(GeometryNodePointInstance, label='Point Instance')

        def get_point_random_rotation_node(self) -> ShaderNodeGroup:
            return self.get_node_group(_('Point Random Rotation'), label='Point Random Rotation')

        def get_random_rotation_point_instance_node(self) -> ShaderNodeGroup:
            return self.get_node_group(_('Random Rotation Point Instance'), label='Random Rotation Point Instance')

        def reset(self):
            node_frame = self.find_adjusters_node_frame()
            if node_frame is not None:
                self.remove_node_frame(node_frame)

            node_frame = self.find_node_frame()
            if node_frame is None:
                return

            self.remove_node_frame(node_frame)

        def draw_setting_shader_node_properties(self, layout: bpy.types.UILayout, nodes: Iterable[GeometryNode]):
            for node in nodes:
                if isinstance(node, GeometryNodeGroup):
                    pass
                elif self.check_setting_node(node):
                    pass
                else:
                    continue
                col = layout.box().column(align=True)
                col.label(text=node.label)
                if isinstance(node, ShaderNodeValue):
                    for node_output in node.outputs:
                        col.prop(node_output, 'default_value', text=node_output.name)
                else:
                    for node_input in node.inputs:
                        if node_input.is_linked:
                            continue
                        if isinstance(node_input, NodeSocketGeometry):
                            continue
                        col.prop(node_input, 'default_value', text=node_input.name)
except ImportError:
    print('[WARN] Geometry Nodes do not exist. Ignore it.')
