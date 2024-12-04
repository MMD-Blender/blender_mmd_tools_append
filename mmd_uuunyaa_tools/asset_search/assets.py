# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import ast
import glob
import importlib
import json
import os
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, ItemsView, Tuple, ValuesView

import requests
from .. import PACKAGE_PATH, REGISTER_HOOKS
from ..m17n import _
from ..utilities import get_preferences


class AssetType(Enum):
    ALL = 'All'
    MODEL_MMD = 'Model (.pmx)'
    MODEL_BLENDER = 'Model (.blend)'
    MOTION_MMD = 'Motion (.vmd)'
    POSE_MMD = 'Pose (.vpd)'
    LIGHTING = 'Lighting'
    MATERIAL = 'Material'
    WORLD_BLENDER = 'World (.blend)'


translation_properties = [
    _('All'),
    _('Model (.pmx)'),
    _('Model (.blend)'),
    _('Motion (.vmd)'),
    _('Pose (.vpd)'),
    _('Lighting'),
    _('Material'),
    _('World (.blend)'),
]


class AssetDescription:
    def __init__(
        self,
        id: str,
        type: AssetType,
        url: str,
        name: str,
        tags: Dict[str, str],
        updated_at: datetime,
        thumbnail_url: str,
        source_url: str,
        download_action: str,
        import_action: str,
        aliases: Dict[str, str],
        note: str,
    ):
        self.id = id
        self.type = type
        self.url = url
        self.name = name
        self.tags = tags
        self.updated_at = updated_at
        self.thumbnail_url = thumbnail_url
        self.source_url = source_url
        self.download_action = download_action
        self.import_action = import_action
        self.aliases = aliases
        self.note = note
        self.tag_names = set(tags.values())
        self.keywords = '^'.join(['', name, note, *self.tag_names, *aliases.values()]).lower()

    def tags_text(self) -> str:
        return ', '.join(self.tag_names)


class _Utilities:

    @staticmethod
    def to_dict(asset: AssetDescription) -> Dict[str, Any]:
        return {
            'id': asset.id,
            'type': asset.type,
            'url': asset.url,
            'name': asset.name,
            'tags': asset.tags,
            'updated_at': asset.updated_at,
            'thumbnail_url': asset.thumbnail_url,
            'source_url': asset.source_url,
            'download_action': asset.download_action,
            'import_action': asset.import_action,
            'aliases': asset.aliases,
            'note': asset.note,
        }

    @staticmethod
    def from_dict(asset: Dict[str, Any]) -> AssetDescription:
        return AssetDescription(
            id=asset['id'],
            type=AssetType[asset['type']],
            url=asset['url'],
            name=asset['name'],
            tags=asset['tags'],
            updated_at=datetime.strptime(asset['updated_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=timezone.utc).astimezone(tz=None),
            thumbnail_url=asset['thumbnail_url'],
            source_url=asset['source_url'],
            download_action=asset['download_action'],
            import_action=asset['import_action'],
            aliases=asset['aliases'],
            note=asset['note'],
        )

    @staticmethod
    def to_json(asset: AssetDescription, **kwargs):
        def encoder(obj):
            if isinstance(obj, datetime):
                return obj.astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            if isinstance(obj, Enum):
                return obj.name

            if isinstance(obj, set):
                return list(obj)

            raise TypeError(repr(obj) + ' is not JSON serializable')

        return json.dumps({
            'format': 'blender_mmd_assets:3',
            'description': 'This file is a mmd_uuunyaa_tools marking',
            'license': 'CC-BY-4.0 License',
            'created_at': datetime.now(),
            'assets': [_Utilities.to_dict(asset)]
        }, default=encoder, **kwargs)

    @staticmethod
    def to_context(asset: AssetDescription) -> Dict[str, str]:
        return {
            'id': asset.id,
            'type': asset.type.name,
            'name': asset.name,
            'aliases': asset.aliases,
        }

    @staticmethod
    def resolve_path(asset: AssetDescription) -> Tuple[str, str]:
        preferences = get_preferences()
        asset_extract_root_folder = preferences.asset_extract_root_folder
        asset_extract_folder = preferences.asset_extract_folder
        asset_extract_json = preferences.asset_extract_json

        context = _Utilities.to_context(asset)
        asset_path = os.path.join(
            asset_extract_root_folder,
            asset_extract_folder.format(**context)
        )

        asset_json = os.path.join(
            asset_path,
            asset_extract_json.format(**context)
        )

        return (asset_path, asset_json)

    @staticmethod
    def is_extracted(asset: AssetDescription) -> bool:
        _, asset_json = _Utilities.resolve_path(asset)
        return os.path.exists(asset_json)

    @staticmethod
    def write_json(asset: AssetDescription):
        _, asset_json = _Utilities.resolve_path(asset)
        try:
            with open(asset_json, mode='wt', encoding='utf-8') as f:
                f.write(_Utilities.to_json(asset, indent=2, ensure_ascii=False))
        except:
            os.remove(asset_json)
            raise


class AssetRegistry:

    def __init__(self, *assets: AssetDescription):
        self.assets: Dict[str, AssetDescription] = {}
        for asset in assets:
            self.add(asset)

    def add(self, asset: AssetDescription):
        self.assets[asset.id] = asset

    def __contains__(self, identifier: str) -> bool:
        return identifier in self.assets

    def __getitem__(self, identifier: str) -> AssetDescription:
        return self.assets[identifier]

    def items(self) -> ItemsView[str, AssetDescription]:
        return self.assets.items()

    def values(self) -> ValuesView[AssetDescription]:
        return self.assets.values()

    def reload(self):
        preferences = get_preferences()

        self.assets.clear()

        json_paths = glob.glob(os.path.join(preferences.asset_jsons_folder, '*.json'))
        json_paths.sort()
        for json_path in json_paths:
            try:
                with open(json_path, encoding='utf-8') as file:
                    for asset in json.load(file)['assets']:
                        try:
                            self.add(_Utilities.from_dict(asset))
                        except:  # pylint: disable=bare-except
                            traceback.print_exc()
            except:  # pylint: disable=bare-except
                traceback.print_exc()

    def is_extracted(self, identifier: str) -> bool:
        return _Utilities.is_extracted(self[identifier])

    def resolve_path(self, identifier: str) -> str:
        asset_dir, _ = _Utilities.resolve_path(self[identifier])
        return asset_dir


class AssetUpdater:
    default_repo = 'UuuNyaa/blender_mmd_assets'
    default_query = '{"state": "open", "milestone": 1, "labels": "Official"}'
    default_assets_json = 'assets.json'

    @staticmethod
    def load_cat_asset_json():
        namespace = 'cat_asset_json'
        loader = importlib.machinery.SourceFileLoader(
            namespace,
            os.path.join(PACKAGE_PATH, 'externals', 'blender_mmd_assets', 'cat_asset_json.py')
        )
        return loader.load_module(namespace)  # pylint: disable=deprecated-method

    @staticmethod
    def write_assets_json(assets_json_object, output_json: str):
        preferences = get_preferences()
        with open(os.path.join(preferences.asset_jsons_folder, output_json), mode='wt', encoding='utf-8') as file:
            json.dump(assets_json_object, file, ensure_ascii=False, indent=2)

    @staticmethod
    def delete_assets_json(delete_json: str) -> bool:
        preferences = get_preferences()
        json_path = os.path.join(preferences.asset_jsons_folder, delete_json)

        if not os.path.exists(json_path):
            return False

        os.remove(json_path)
        return True

    @staticmethod
    def fetch_assets_json_by_query(repo: str, query_text: str):
        query = ast.literal_eval(query_text)
        cat_asset_json = AssetUpdater.load_cat_asset_json()

        session = requests.Session()
        return cat_asset_json.wrap_assets(cat_asset_json.fetch_assets(session, repo, query))

    @staticmethod
    def fetch_assets_json_by_issue_number(repo: str, issue_number: int):
        cat_asset_json = AssetUpdater.load_cat_asset_json()

        session = requests.Session()
        return cat_asset_json.wrap_assets([
            cat_asset_json.fetch_asset(session, repo, issue_number)
        ])


ASSETS = AssetRegistry()


def initialize_asset_registory():
    preferences = get_preferences()

    if preferences.asset_json_update_on_startup_enabled:
        try:
            print(f"Asset Auto Update: repo='{preferences.asset_json_update_repo}', query='{preferences.asset_json_update_query}'")
            AssetUpdater.write_assets_json(
                AssetUpdater.fetch_assets_json_by_query(preferences.asset_json_update_repo, preferences.asset_json_update_query),
                AssetUpdater.default_assets_json
            )
        except:  # pylint: disable=bare-except
            traceback.print_exc()

    ASSETS.reload()


REGISTER_HOOKS.append(initialize_asset_registory)
