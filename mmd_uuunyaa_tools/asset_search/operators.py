# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import bpy
from ..asset_search.assets import ASSETS, AssetUpdater
from ..asset_search.cache import CONTENT_CACHE
from ..m17n import _


class ReloadAssetJsons(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.reload_asset_jsons'
    bl_label = _('Reload Asset JSONs')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        ASSETS.reload()
        return {'FINISHED'}


class UpdateAssetJson(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.update_asset_json'
    bl_label = _('Update Assets JSON')
    bl_options = {'INTERNAL'}

    repo: bpy.props.StringProperty(default=AssetUpdater.default_repo)
    query: bpy.props.StringProperty(default=AssetUpdater.default_query)
    output_json: bpy.props.StringProperty(default=AssetUpdater.default_assets_json)

    def execute(self, context):
        AssetUpdater.write_assets_json(
            AssetUpdater.fetch_assets_json_by_query(self.repo, self.query),
            self.output_json
        )
        return {'FINISHED'}


class UpdateDebugAssetJson(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.update_debug_asset_json'
    bl_label = _('Update Debug Asset JSON')
    bl_options = {'INTERNAL'}

    repo: bpy.props.StringProperty(default=AssetUpdater.default_repo)
    issue_number: bpy.props.IntProperty()
    output_json: bpy.props.StringProperty(default='ZDEBUG.json')

    def execute(self, context):
        AssetUpdater.write_assets_json(
            AssetUpdater.fetch_assets_json_by_issue_number(self.repo, self.issue_number),
            self.output_json
        )
        return {'FINISHED'}


class DeleteDebugAssetJson(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.delete_debug_asset_json'
    bl_label = _('Delete Debug Asset JSON')
    bl_options = {'INTERNAL'}

    delete_json: bpy.props.StringProperty(default='ZDEBUG.json')

    def execute(self, context):
        if not AssetUpdater.delete_assets_json(self.delete_json):
            self.report(type={'INFO'}, message=f'{self.delete_json} does not exist.')
            return {'CANCELLED'}

        return {'FINISHED'}


class DeleteCachedFiles(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.delete_cached_files'
    bl_label = _('Delete Asset Cached Files')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        CONTENT_CACHE.delete_cache_folder()
        return {'FINISHED'}
