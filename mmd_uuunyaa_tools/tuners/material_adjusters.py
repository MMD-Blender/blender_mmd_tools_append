# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from abc import abstractmethod

from bpy.types import NodeFrame, ShaderNodeGroup
from ..editors.nodes import MaterialEditor
from ..m17n import _


class MaterialAdjusterUtilities(MaterialEditor):

    def check_attached(self, label: str) -> bool:
        return self.find_node(ShaderNodeGroup, label=label) is not None

    def check_attachable(self) -> bool:
        return self.find_active_principled_shader_node() is not None

    def clean_adjusters_node_frame(self) -> NodeFrame:
        node_frame = self.get_adjusters_node_frame()

        if next(self.list_nodes(node_frame=node_frame), None) is not None:
            return

        self.nodes.remove(node_frame)


class MaterialAdjusterABC(MaterialAdjusterUtilities):
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        pass

    @abstractmethod
    def attach(self) -> ShaderNodeGroup:
        pass

    @abstractmethod
    def detach(self):
        pass

    def detach_and_clean(self):
        self.detach()
        self.clean_adjusters_node_frame()

    def is_attached(self) -> bool:
        return self.check_attached(self.get_name())


class WetAdjuster(MaterialAdjusterABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_ADJUSTER_WET'

    @classmethod
    def get_name(cls) -> str:
        return _('Wet Adjuster')

    translation_properties = [
        _('Specular'),
        _('Roughness'),
        _('Wet'),
    ]

    def attach(self):
        node_frame = self.get_adjusters_node_frame()
        node_wet_adjuster = self.find_node(ShaderNodeGroup, label=WetAdjuster.get_name(), node_frame=node_frame)

        node_shader = self.find_active_principled_shader_node()
        node_wet_adjuster = self.edit(self.get_wet_adjuster_node(), {
            'Specular': self.to_link_or_value(node_shader.inputs['Specular']),
            'Roughness': self.to_link_or_value(node_shader.inputs['Roughness']),
            'Wet': self.edit(self.get_vertex_color_node(), {}, {'location': self.grid_to_position(-4, -10), 'parent': node_frame}).outputs['Color'],
        }, {'location': self.grid_to_position(-2, -10), 'parent': node_frame})

        self.edit(node_shader, {
            'Specular': node_wet_adjuster.outputs['Specular'],
            'Roughness': node_wet_adjuster.outputs['Roughness'],
        }, force=True)

        return node_wet_adjuster

    def detach(self):
        node_wet_adjuster = self.get_wet_adjuster_node()

        self.edit(self.find_active_principled_shader_node(), {
            'Specular': self.to_link_or_value(node_wet_adjuster.inputs['Specular']),
            'Roughness': self.to_link_or_value(node_wet_adjuster.inputs['Roughness']),
        }, force=True)

        self.nodes.remove(node_wet_adjuster)
        self.nodes.remove(self.get_vertex_color_node())


class SubsurfaceAdjuster(MaterialAdjusterABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_ADJUSTER_SUBSURFACE'

    @classmethod
    def get_name(cls) -> str:
        return _('Subsurface Adjuster')

    translation_properties = [
        _('Min'),
        _('Max'),
        _('Blood Color'),
        _('Subsurface'),
        _('Subsurface Color'),
    ]

    def attach(self) -> ShaderNodeGroup:
        node_frame = self.get_adjusters_node_frame()
        node_subsurface_adjuster = self.find_node(ShaderNodeGroup, label=self.get_name(), node_frame=node_frame)

        node_shader = self.find_active_principled_shader_node()
        node_subsurface_adjuster = self.edit(self.get_subsurface_adjuster_node(), {
            'Min': self.to_link_or_value(node_shader.inputs['Subsurface']),
            'Max': 0.300,
            'Blood Color': self.to_link_or_value(node_shader.inputs['Subsurface Color']),
        }, {'location': self.grid_to_position(-2, -8), 'parent': node_frame})

        self.edit(node_shader, {
            'Subsurface':  node_subsurface_adjuster.outputs['Subsurface'],
            'Subsurface Color': node_subsurface_adjuster.outputs['Subsurface Color'],
        }, force=True)

        return node_subsurface_adjuster

    def detach(self):
        node_subsurface_adjuster = self.get_subsurface_adjuster_node()

        self.edit(self.find_active_principled_shader_node(), {
            'Subsurface': self.to_link_or_value(node_subsurface_adjuster.inputs['Min']),
            'Subsurface Color': self.to_link_or_value(node_subsurface_adjuster.inputs['Blood Color']),
        }, force=True)

        self.nodes.remove(node_subsurface_adjuster)


class GlitterAdjuster(MaterialAdjusterABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_ADJUSTER_GLITTER'

    @classmethod
    def get_name(cls) -> str:
        return _('Glitter Adjuster')

    translation_properties = [
        _('Specular'),
        _('Roughness'),
        _('Glitter'),
    ]

    def attach(self):
        node_frame = self.get_adjusters_node_frame()
        node_glitter_adjuster = self.find_node(ShaderNodeGroup, label=GlitterAdjuster.get_name(), node_frame=node_frame)

        node_shader = self.find_active_principled_shader_node()
        node_glitter_adjuster = self.edit(self.get_glitter_adjuster_node(), {
            'Specular': self.to_link_or_value(node_shader.inputs['Specular']),
            'Roughness': self.to_link_or_value(node_shader.inputs['Roughness']),
            'Normal': self.to_link_or_value(node_shader.inputs['Normal']),
        }, {'location': self.grid_to_position(-2, -12), 'parent': node_frame})

        self.edit(node_shader, {
            'Specular': node_glitter_adjuster.outputs['Specular'],
            'Roughness': node_glitter_adjuster.outputs['Roughness'],
            'Normal': node_glitter_adjuster.outputs['Normal'],
        }, force=True)

        return node_glitter_adjuster

    def detach(self):
        node_glitter_adjuster = self.get_glitter_adjuster_node()

        self.edit(self.find_active_principled_shader_node(), {
            'Specular': self.to_link_or_value(node_glitter_adjuster.inputs['Specular']),
            'Roughness': self.to_link_or_value(node_glitter_adjuster.inputs['Roughness']),
            'Normal': self.to_link_or_value(node_glitter_adjuster.inputs['Normal']),
        }, force=True)

        self.nodes.remove(node_glitter_adjuster)


class EmissionAdjuster(MaterialAdjusterABC):
    @classmethod
    def get_id(cls) -> str:
        return 'MATERIAL_ADJUSTER_EMISSION'

    @classmethod
    def get_name(cls) -> str:
        return _('Emission Adjuster')

    translation_properties = [
        _('Color'),
        _('Threshold'),
        _('Strength'),
        _('Emission'),
        _('Emission Strength'),
    ]

    def attach(self) -> ShaderNodeGroup:
        node_frame = self.get_adjusters_node_frame()
        node_emission_adjuster = self.find_node(ShaderNodeGroup, label=self.get_name(), node_frame=node_frame)

        node_shader = self.find_active_principled_shader_node()
        node_emission_adjuster = self.edit(self.get_emission_adjuster_node(), {
            'Color': self.to_link_or_value(node_shader.inputs['Base Color']),
            'Threshold': 1.000,
            'Strength': 1.000,
        }, {'location': self.grid_to_position(-2, -14), 'parent': node_frame})

        self.edit(node_shader, {
            'Emission':  node_emission_adjuster.outputs['Emission'],
            'Emission Strength': node_emission_adjuster.outputs['Emission Strength'],
        }, force=True)

        return node_emission_adjuster

    def detach(self):
        node_emission_adjuster = self.get_emission_adjuster_node()

        self.edit(self.find_active_principled_shader_node(), {
            'Emission': self.hex_to_rgba(0x000000),
            'Emission Strength': 1.000,
        }, force=True)

        self.nodes.remove(node_emission_adjuster)


ADJUSTERS = {
    WetAdjuster.get_name(): WetAdjuster,
    SubsurfaceAdjuster.get_name(): SubsurfaceAdjuster,
    GlitterAdjuster.get_name(): GlitterAdjuster,
    EmissionAdjuster.get_name(): EmissionAdjuster,
}
