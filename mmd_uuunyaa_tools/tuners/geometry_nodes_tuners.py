# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Optional

import bpy
from ..m17n import _
from ..tuners import TunerABC, TunerRegistry

try:
    from ..editors.geometry_nodes import GeometryEditor

    class GeometryNodesUtilities:
        @staticmethod
        def find_geometry_node_tree(obj: bpy.types.Object) -> Optional[bpy.types.GeometryNodeTree]:
            modifier = GeometryNodesUtilities.find_geometry_node_modifier(obj)
            if modifier:
                return modifier.node_group
            return None

        @staticmethod
        def find_geometry_node_modifier(obj: bpy.types.Object) -> Optional[bpy.types.NodesModifier]:
            modifier: bpy.types.Modifier
            for modifier in obj.modifiers:
                if not modifier.is_active:
                    continue
                if modifier.type == 'NODES':
                    return modifier
                return None
            return None

    class GeometryTunerABC(TunerABC, GeometryEditor):
        pass

    class ResetGeometryTuner(GeometryTunerABC):
        @classmethod
        def get_id(cls) -> str:
            return 'GEOMETRY_RESET'

        @classmethod
        def get_name(cls) -> str:
            return _('Reset')

        def execute(self):
            self.reset()
            self.edit(self.get_output_node(), {
                'Geometry': self.get_input_node().outputs['Geometry'],
            }, force=True)

    class SequinsGeometryTuner(GeometryTunerABC):
        @classmethod
        def get_id(cls) -> str:
            return 'GEOMETRY_SEQUINS'

        @classmethod
        def get_name(cls) -> str:
            return _('Sequins')

        def execute(self):
            self.reset()
            node_frame = self.get_node_frame(self.get_name())

            node_random_rotation_point_instance = self.get_random_rotation_point_instance_node()
            target_collection = bpy.context.view_layer.active_layer_collection.collection
            if 'Sequin Piece' not in target_collection.objects:
                object_sequin_piece = bpy.data.objects['Sequin Piece']
                target_collection.objects.link(object_sequin_piece)
                object_sequin_piece.hide_set(True)
                object_sequin_piece.hide_viewport = False
                object_sequin_piece.hide_render = True

            self.edit(self.get_output_node(), {
                'Geometry': self.edit(node_random_rotation_point_instance, {
                    'Geometry': self.get_input_node().outputs['Geometry'],
                }, {'location': self.grid_to_position(+1, +0), 'parent': node_frame}).outputs['Geometry'],
            }, {'location': self.grid_to_position(+3, +0)}, force=True)

    TUNERS = TunerRegistry(
        (0, ResetGeometryTuner),
        (1, SequinsGeometryTuner),
    )
except ImportError:
    print('[WARN] Geometry Nodes do not exist. Ignore it.')
