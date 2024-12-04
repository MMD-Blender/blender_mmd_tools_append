# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import os
import pathlib
import tempfile

import bpy

from . import addon_updater_ops, utilities
from .asset_search.assets import AssetUpdater
from .asset_search.operators import DeleteCachedFiles
from .m17n import _


@addon_updater_ops.make_annotations
class MMDUuuNyaaToolsAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    asset_search_results_max_display_count: bpy.props.IntProperty(
        name=_('Asset Search Results Max. Display Count'),
        description=_('Larger value is slower'),
        min=10,
        soft_max=200,
        default=50,
    )

    asset_jsons_folder: bpy.props.StringProperty(
        name=_('Asset JSONs Folder'),
        description=_('Path to asset list JSON files'),
        subtype='DIR_PATH',
        default=os.path.join(os.path.dirname(__file__), 'asset_jsons')
    )

    asset_json_update_repo: bpy.props.StringProperty(
        name=_('Asset JSON Update Repository'),
        description=_('Specify the github repository which to retrieve the assets'),
        default=AssetUpdater.default_repo
    )

    asset_json_update_query: bpy.props.StringProperty(
        name=_('Asset JSON Update Query'),
        description=_('Specify the filter conditions for retrieving assets'),
        default=AssetUpdater.default_query
    )

    asset_json_update_on_startup_enabled: bpy.props.BoolProperty(
        name=_('Asset JSON Auto Update on Startup'),
        default=True
    )

    asset_cache_folder: bpy.props.StringProperty(
        name=_('Asset Cache Folder'),
        description=_('Path to asset cache folder'),
        subtype='DIR_PATH',
        default=os.path.join(tempfile.gettempdir(), 'mmd_uuunyaa_tools_cache'),
    )

    asset_max_cache_size: bpy.props.IntProperty(
        name=_('Asset Max. Cache Size (MB)'),
        description=_('Maximum size (Mega bytes) of the asset cache folder'),
        min=100,
        soft_max=1_000_000,
        default=10_000,
    )

    asset_extract_root_folder: bpy.props.StringProperty(
        name=_('Asset Extract Root Folder'),
        description=_('Path to extract the cached assets'),
        subtype='DIR_PATH',
        default=os.path.join(pathlib.Path.home(), 'BlenderAssets')
    )

    asset_extract_folder: bpy.props.StringProperty(
        name=_('Asset Extract Folder'),
        description=_('Path to assets. Create it under the Asset Extract Root Folder.\n'
                      'The following variables are available: {id}, {type}, {name}, {aliases[en]}, {aliases[ja]}'),
        default='{type}/{id}.{name}'
    )

    asset_extract_json: bpy.props.StringProperty(
        name=_('Asset Extract JSON'),
        description=_('Name to assets marker JSON. Create it under the Asset Extract Folder.\n'
                      'The presence of this file is used to determine the existence of the asset.\n'
                      'The following variables are available: {id}, {type}, {name}, {aliases[en]}, {aliases[ja]}'),
        default='{id}.json'
    )

    # Addon updater preferences.
    auto_check_update: bpy.props.BoolProperty(
        name='Auto-check for Update',
        description='If enabled, auto-check for updates using an interval',
        default=False
    )

    updater_interval_months: bpy.props.IntProperty(
        name='Months',
        description='Number of months between checking for updates',
        default=0,
        min=0
    )

    updater_interval_days: bpy.props.IntProperty(
        name='Days',
        description='Number of days between checking for updates',
        default=7,
        min=0,
        max=31
    )

    updater_interval_hours: bpy.props.IntProperty(
        name='Hours',
        description='Number of hours between checking for updates',
        default=0,
        min=0,
        max=23
    )

    updater_interval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description='Number of minutes between checking for updates',
        default=0,
        min=0,
        max=59
    )

    _translation_texts = [
        _('Check now for mmd_uuunyaa_tools update'),
        _('Auto-check for Update'),
        _('Last check: Never'),
        _('Addon is up to date'),
        _('Checking...'),
        _("Choose 'Update Now' & press OK to install, "),
        _('or click outside window to defer'),
        _('No updates available'),
        _('Press okay to dismiss dialog'),
        _('Check for update now?'),
        _('Process update'),
        _('Decide to install, ignore, or defer new addon update'),
        _('Update Now'),
        _('Install update now'),
        _('Ignore'),
        _('Ignore this update to prevent future popups'),
        _('Defer'),
        _('Defer choice till next blender session'),
    ]

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # pylint: disable=no-member

        col = layout.box().column()
        col.prop(self, 'asset_search_results_max_display_count')

        col = layout.box().column()
        col.prop(self, 'asset_jsons_folder')

        row = col.split(factor=0.95, align=True)
        row.prop(self, 'asset_json_update_repo')
        row.operator('wm.url_open', text=_('Browse Assets'), icon='URL').url = f'https://github.com/{self.asset_json_update_repo}/issues'

        row = col.split(factor=0.95, align=True)
        row.prop(self, 'asset_json_update_query')
        row.operator('wm.url_open', text=_('Query Examples'), icon='URL').url = 'https://github.com/UuuNyaa/blender_mmd_uuunyaa_tools/wiki/How-to-add-a-new-asset#query-examples'

        col.prop(self, 'asset_json_update_on_startup_enabled')

        col = layout.box().column()
        col.prop(self, 'asset_cache_folder')

        usage = col.split(align=True, factor=0.24)
        usage.label(text=_('Asset Cache Usage:'))
        usage_row = usage.column(align=True)
        usage_row.alignment = 'RIGHT'

        cache_folder_size = sum(f.stat().st_size for f in pathlib.Path(self.asset_cache_folder).glob('**/*') if f.is_file())
        usage_row.label(text=f'{utilities.to_human_friendly_text(cache_folder_size)}B')

        col.prop(self, 'asset_max_cache_size')

        col.operator(DeleteCachedFiles.bl_idname)

        col = layout.box().column()
        col.prop(self, 'asset_extract_root_folder')
        col.prop(self, 'asset_extract_folder')
        col.prop(self, 'asset_extract_json')

        col = layout.box().column()
        col.label(text=_('(Experimental) Add-on Update'), icon='ERROR')
        addon_updater_ops.update_settings_ui_condensed(self, context, col)

        layout.separator()
        col = layout.column()
        col.label(text=_('Credits:'))

        credit = col.column(align=True)
        row = credit.split(factor=0.95)
        row.label(text=_('Rigid body Physics to Cloth Physics feature is the work of 小威廉伯爵.'))
        row.operator('wm.url_open', text=_(''), icon='URL').url = 'https://github.com/958261649/Miku_Miku_Rig'
        credit.label(text=_('It was ported with his permission.'))
