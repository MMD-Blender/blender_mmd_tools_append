# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import functools
import os
import time
from enum import Enum
from typing import List, Optional, Tuple

import bpy
import bpy.utils.previews
from .. import PACKAGE_PATH
from ..asset_search.actions import ImportActionExecutor, MessageException
from ..asset_search.assets import ASSETS, AssetDescription, AssetType
from ..asset_search.cache import CONTENT_CACHE, Content, Task
from ..asset_search.operators import DeleteDebugAssetJson, ReloadAssetJsons, UpdateAssetJson, UpdateDebugAssetJson
from ..m17n import _, iface_
from ..utilities import get_preferences, label_multiline, to_human_friendly_text, to_int32

PREVIEWS: Optional[bpy.utils.previews.ImagePreviewCollection]


class AssetState(Enum):
    INITIALIZED = 0
    DOWNLOADING = 1
    CACHED = 2
    EXTRACTED = 3
    FAILED = 4
    UNKNOWN = -1


class Utilities:
    @staticmethod
    def is_importable(asset: AssetDescription) -> bool:
        return (
            ASSETS.is_extracted(asset.id)
            or
            CONTENT_CACHE.try_get_content(asset.download_action) is not None
        )

    @staticmethod
    def get_asset_state(asset: AssetDescription) -> Tuple[AssetState, Optional[Content], Optional[Task]]:
        if ASSETS.is_extracted(asset.id):
            return (AssetState.EXTRACTED, None, None)

        content = CONTENT_CACHE.try_get_content(asset.download_action)
        if content is not None:
            if content.state is Content.State.CACHED:
                return (AssetState.CACHED, content, None)

            if content.state is Content.State.FAILED:
                return (AssetState.FAILED, content, None)

        else:
            task = CONTENT_CACHE.try_get_task(asset.download_action)
            if task is None:
                return (AssetState.INITIALIZED, None, None)

            elif task.state in {Task.State.QUEUING, Task.State.RUNNING}:
                return (AssetState.DOWNLOADING, None, task)

        return (AssetState.UNKNOWN, None, None)

    @staticmethod
    def resolve_path(asset: AssetDescription) -> str:
        return ASSETS.resolve_path(asset.id)


class AssetSearch(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_search'
    bl_label = 'Search Asset'
    bl_options = {'INTERNAL'}

    @staticmethod
    def _on_thumbnail_fetched(search_result, region, update_time, asset, content):
        if search_result.update_time != update_time:
            return

        asset_item = search_result.asset_items.add()
        asset_item.id = asset.id

        global PREVIEWS  # pylint: disable=global-statement
        if asset.thumbnail_url not in PREVIEWS:
            if content.filepath is None:
                content.filepath = os.path.join(PACKAGE_PATH, 'thumbnails', 'ASSET_THUMBNAIL_EMPTY.png')
            PREVIEWS.load(asset.thumbnail_url, content.filepath, 'IMAGE')

        region.tag_redraw()

    def execute(self, context):
        # pylint: disable=too-many-locals

        preferences = get_preferences()

        max_search_result_count = preferences.asset_search_results_max_display_count

        query = context.scene.mmd_uuunyaa_tools_asset_search.query
        query_type = query.type
        query_text = query.text.lower()
        query_tags = query.tags
        query_is_cached = query.is_cached

        enabled_tag_names = {tag.name for tag in query_tags if tag.enabled}
        enabled_tag_count = len(enabled_tag_names)

        search_results: List[AssetDescription] = []
        search_results = [
            asset for asset in ASSETS.values() if (
                query_type in {AssetType.ALL.name, asset.type.name}
                and enabled_tag_count == len(asset.tag_names & enabled_tag_names)
                and query_text in asset.keywords
                and (Utilities.is_importable(asset) if query_is_cached else True)
            )
        ]

        hit_count = len(search_results)
        update_time = to_int32(time.time_ns() >> 10)
        result = context.scene.mmd_uuunyaa_tools_asset_search.result
        result.count = min(max_search_result_count, hit_count)
        result.hit_count = hit_count
        result.asset_items.clear()
        result.update_time = update_time

        for asset in search_results[:max_search_result_count]:
            CONTENT_CACHE.async_get_content(
                asset.thumbnail_url,
                functools.partial(self._on_thumbnail_fetched, result, context.region, update_time, asset)
            )

        tag_names = set()
        for asset in search_results:
            tag_names.update(asset.tag_names)

        query.is_updating = True
        try:
            query_tags.clear()
            query.tags_index = 0
            for tag_name in sorted(tag_names):
                tag = query_tags.add()
                tag.name = tag_name
                tag.enabled = tag_name in enabled_tag_names
        finally:
            query.is_updating = False

        return {'FINISHED'}


class AssetDownload(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_download'
    bl_label = 'Download Asset'
    bl_options = {'INTERNAL'}

    asset_id: bpy.props.StringProperty()

    @staticmethod
    def __on_fetched(_, asset, content):
        print(f'done: {asset.name}, {asset.id}, {content.state}, {content.id}')

    def execute(self, context):
        print(f'do: {self.bl_idname}, {self.asset_id}')
        asset = ASSETS[self.asset_id]
        CONTENT_CACHE.async_get_content(asset.download_action, functools.partial(self.__on_fetched, context, asset))
        return {'FINISHED'}


class AssetDownloadCancel(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_download_cancel'
    bl_label = 'Cancel Asset Download'
    bl_options = {'INTERNAL'}

    asset_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(f'do: {self.bl_idname}')

        asset = ASSETS[self.asset_id]
        CONTENT_CACHE.cancel_fetch(asset.download_action)

        return {'FINISHED'}


class AssetCacheRemove(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_cache_remove'
    bl_label = 'Remove Cached Asset'
    bl_options = {'INTERNAL'}

    asset_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(f'do: {self.bl_idname}')

        asset = ASSETS[self.asset_id]
        CONTENT_CACHE.remove_content(asset.download_action)

        return {'FINISHED'}


class AssetImport(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_import'
    bl_label = 'Import Asset'
    bl_options = {'INTERNAL'}

    asset_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'OBJECT'

    def execute(self, context):
        print(f'do: {self.bl_idname}')

        asset = ASSETS[self.asset_id]
        content = CONTENT_CACHE.try_get_content(asset.download_action)

        try:
            ImportActionExecutor.execute_import_action(asset, content.filepath if content is not None else None)
        except MessageException as ex:
            self.report(type={'ERROR'}, message=str(ex))

        return {'FINISHED'}


class AssetDetailPopup(bpy.types.Operator):
    bl_idname = 'mmd_uuunyaa_tools.asset_detail_popup'
    bl_label = 'Popup Asset Detail'
    bl_options = {'INTERNAL'}

    asset_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(f'do: {self.bl_idname}')
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        asset = ASSETS[self.asset_id]

        layout = self.layout

        def draw_title(layout, title, factor=0.11):
            split = layout.split(factor=factor)
            split.alignment = 'RIGHT'
            split.label(text=title)
            return split.row()

        def draw_titled_label(layout, title, text, split_factor=0.11):
            split = layout.split(factor=split_factor)
            split.alignment = 'RIGHT'
            split.label(text=title)
            label_multiline(split.column(align=True), text=text, width=int(600*(1-split_factor)))

        col = layout.column(align=True)

        grid = col.split(factor=0.5)
        draw_title(grid, _('Type:'), factor=0.11*2).label(text=asset.type.value)
        draw_title(grid, _('ID:'), factor=0.11*2).operator('wm.url_open', text=asset.id, icon='URL').url = asset.url

        draw_titled_label(col, title=_('Name:'), text=asset.name)
        draw_titled_label(col, title=_('Aliases:'), text=', '.join(list(asset.aliases.values())))
        draw_titled_label(col, title=_('Tags:'), text=asset.tags_text())
        draw_titled_label(col, title=_('Updated at:'), text=asset.updated_at.strftime('%Y-%m-%d %H:%M:%S %Z'))
        draw_titled_label(col, title=_('Note:'), text=asset.note)

        draw_title(col, _('Source:')).operator('wm.url_open', text=asset.source_url, icon='URL').url = asset.source_url

        (asset_state, content, task) = Utilities.get_asset_state(asset)

        if asset_state is AssetState.INITIALIZED:
            layout.operator(AssetDownload.bl_idname, text=_('Download'), icon='TRIA_DOWN_BAR').asset_id = asset.id

        elif asset_state is AssetState.DOWNLOADING:
            draw_titled_label(layout, title=_('Cache:'), text=f'{iface_("Downloading")} {to_human_friendly_text(task.fetched_size)}B / {to_human_friendly_text(task.content_length)}B')
            layout.operator(AssetDownloadCancel.bl_idname, text=_('Cancel'), icon='CANCEL').asset_id = asset.id

        elif asset_state is AssetState.CACHED:
            draw_title(layout, _('Cache:')).label(text=f'{to_human_friendly_text(content.length)}B   ({content.type})')
            draw_title(layout, _('Path:')).operator(
                'wm.path_open',
                text=content.filepath,
                icon='FILEBROWSER'
            ).filepath = content.filepath

            row = layout.split(factor=0.9, align=True)
            row.operator(AssetImport.bl_idname, text=_('Import'), icon='IMPORT').asset_id = asset.id
            row.operator(AssetCacheRemove.bl_idname, text='', icon='TRASH').asset_id = asset.id

        elif asset_state is AssetState.EXTRACTED:
            asset_path = Utilities.resolve_path(asset)
            draw_title(layout, _('Path:')).operator('wm.path_open', text=asset_path, icon='FILEBROWSER').filepath = asset_path
            layout.operator(AssetImport.bl_idname, text=_('Import'), icon='IMPORT').asset_id = asset.id

        elif asset_state is AssetState.FAILED:
            layout.operator(AssetDownload.bl_idname, text=_('Retry'), icon='FILE_REFRESH').asset_id = asset.id

        else:
            layout.operator(AssetDownload.bl_idname, text=_('Retry'), icon='FILE_REFRESH').asset_id = asset.id


class AssetSearchQueryTags(bpy.types.UIList):
    bl_idname = 'UUUNYAA_UL_mmd_uuunyaa_tools_asset_search_query_tags'

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_property,
        index: int = 0,
        flt_flag: int = 0
    ):
        # pylint: disable=too-many-arguments
        layout.prop(item, 'enabled', text=item.name, index=index)


class AssetSearchPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_mmd_uuunyaa_tools_asset_search'
    bl_label = _('UuuNyaa Asset Search')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assets'

    def draw(self, context):
        # pylint: disable=too-many-locals

        search = context.scene.mmd_uuunyaa_tools_asset_search
        query = search.query
        layout = self.layout

        layout.prop(query, 'type', text=_('Asset type'))
        layout.prop(query, 'text', text=_('Query'), icon='VIEWZOOM')
        if query.tags is not None:
            col = layout.column()
            row = col.row()
            row.label(text=_('Tags:'))
            row = row.row()
            row.alignment = 'RIGHT'
            row.prop(query, 'is_cached', text=_('Cached'))
            col.template_list(
                AssetSearchQueryTags.bl_idname, '',
                query, 'tags',
                query, 'tags_index',
                type='GRID',
                columns=max(1, int(context.region.width / 250)),
                rows=2
            )
            row = col.row()

        row = layout.row()
        row.alignment = 'RIGHT'
        row.label(text=iface_('{search_result_count} of {search_result_hit_count} results').format(
            search_result_count=search.result.count,
            search_result_hit_count=search.result.hit_count,
        ))

        asset_items = context.scene.mmd_uuunyaa_tools_asset_search.result.asset_items

        display_count = 0

        global PREVIEWS  # pylint: disable=global-statement

        grid = layout.grid_flow(row_major=True)
        for asset_item in asset_items:
            if asset_item.id not in ASSETS:
                continue

            asset = ASSETS[asset_item.id]

            if asset.thumbnail_url not in PREVIEWS:
                continue

            (asset_state, _content, _task) = Utilities.get_asset_state(asset)

            if asset_state is AssetState.INITIALIZED:
                icon = 'NONE'
            elif asset_state is AssetState.DOWNLOADING:
                icon = 'SORTTIME'
            elif asset_state is AssetState.CACHED:
                icon = 'SOLO_OFF'
            elif asset_state is AssetState.EXTRACTED:
                icon = 'SOLO_ON'
            elif asset_state is AssetState.FAILED:
                icon = 'ERROR'
            else:
                icon = 'ERROR'

            box = grid.box().column(align=True)
            box.template_icon(PREVIEWS[asset.thumbnail_url].icon_id, scale=6.0)
            box.operator(AssetDetailPopup.bl_idname, text=asset.name, icon=icon).asset_id = asset.id
            display_count += 1

        asset_item_count = len(asset_items)

        if display_count != asset_item_count:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text=_('Invalid search result, Please search again.'))
            return

        loading_count = search.result.count - asset_item_count
        if loading_count > 0:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text=iface_('Loading {loading_count} item{plural_form_suffix}...').format(
                loading_count=loading_count,
                plural_form_suffix='s' if loading_count > 1 else ''
            ))
            return

    @staticmethod
    def register():
        global PREVIEWS  # pylint: disable=global-statement
        PREVIEWS = bpy.utils.previews.new()  # pylint: disable=assignment-from-no-return

    @staticmethod
    def unregister():
        global PREVIEWS  # pylint: disable=global-statement
        if PREVIEWS is not None:
            bpy.utils.previews.remove(PREVIEWS)


class AssetsOperatorPanel(bpy.types.Panel):
    bl_idname = 'UUUNYAA_PT_assets_operator_panel'
    bl_label = _('UuuNyaa Assets Operator')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assets'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        box = col.box().column(align=True)
        box.label(text=_('Reload local asset JSON files'))
        box.operator(ReloadAssetJsons.bl_idname, icon='FILE_REFRESH')

        preferences = get_preferences()

        box = col.box().column(align=True)
        box.label(text=_('Download and Update to the latest assets'))
        operator = box.operator(UpdateAssetJson.bl_idname, icon='TRIA_DOWN_BAR')
        operator.repo = preferences.asset_json_update_repo
        operator.query = preferences.asset_json_update_query

        props = context.scene.mmd_uuunyaa_tools_asset_operator

        row = col.row(align=True)
        row.prop(
            props, 'debug_expanded',
            icon='TRIA_DOWN' if props.debug_expanded else 'TRIA_RIGHT',
            icon_only=True,
            emboss=False,
        )
        row.label(text=_('Debug'))

        if not props.debug_expanded:
            return

        box = col.box().column()
        box.label(text=_('Fetch an asset for debug'), icon='MODIFIER')
        box.column(align=True).prop(props, 'debug_issue_number', text=_('issue #'))

        row = box.row(align=True)
        row.operator(DeleteDebugAssetJson.bl_idname, icon='CANCEL')
        row.operator(UpdateDebugAssetJson.bl_idname, icon='TRIA_DOWN_BAR').issue_number = props.debug_issue_number

        box = col.box().column()
        box.label(text=_('Download and Update to the latest filtered assets for debug'), icon='FILTER')

        box.prop(props, 'repo', text=_('Repository'))
        box.prop(props, 'query', text=_('Query'))
        box.prop(props, 'output_json', text=_('Write to'))

        operator = box.operator(UpdateAssetJson.bl_idname, text=_('Update Assets JSON by query'), icon='TRIA_DOWN_BAR')
        operator.repo = props.repo
        operator.query = props.query
        operator.output_json = props.output_json
