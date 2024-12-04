# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import ast
import errno
import functools
import importlib
import json
import os
import re
import shutil
import stat
import urllib
import zipfile
from typing import List, Optional

import bpy
import requests
from .. import PACKAGE_PATH
from ..asset_search.assets import AssetDescription, _Utilities
from ..m17n import _
from ..utilities import MessageException


class RestrictionChecker(ast.NodeVisitor):
    def __init__(self, *functions: List[str]):
        self._functions = functions

    def visit(self, node: ast.AST):
        node_name = node.__class__.__name__

        if node_name not in {'Module', 'Expr', 'Call', 'Constant', 'Name', 'Str', 'JoinedStr', 'FormattedValue', 'Load', 'Num', 'keyword'}:
            raise NotImplementedError(ast.dump(node))

        if node_name == 'Call':
            if node.func.id not in self._functions:
                raise NotImplementedError(ast.dump(node))

        return self.generic_visit(node)


class DownloadActionExecutor:
    @staticmethod
    def get(url: str) -> requests.models.Response:
        return requests.get(url, allow_redirects=True, stream=True)

    @staticmethod
    def tstorage(url: str, password: str = None) -> requests.models.Response:
        return requests.post(
            url,
            data={
                'op': 'download2',
                'id': url[len('http://tstorage.info/'):],
                'rand': '',
                'referer': '',
                'method_free': '',
                'method_premium': '',
                'password': password,
            },
            allow_redirects=True,
            stream=True
        )

    @staticmethod
    def smutbase(url: str) -> requests.models.Response:
        session = requests.Session()
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()

        match = re.search(r'<a +href="([^"]+)">Click here if your download does not start within a few seconds.</a>', response.text)
        if match is None:
            raise ValueError(_('Failed to download assets from SmutBase. The response format may have changed.'))

        return session.get(match.group(1).replace('&amp;', '&'), stream=True)

    @staticmethod
    def bowlroll(url: str, password: str = None) -> requests.models.Response:
        session = requests.Session()
        response = session.get(url)
        response.raise_for_status()

        match = re.search(r' data-csrf_token="([^"]+)"', response.text)
        csrf_token = match.group(1)

        match = re.search(r'<input type="hidden" name="download_key" value="([^"]+)">', response.text)
        download_key = match.group(1) if password is None else password

        response = session.post(
            f"{url.replace('/file/','/api/file/')}/download-check",
            data={
                'download_key': download_key,
                'csrf_token': csrf_token,
            }
        )
        response.raise_for_status()

        download_json = json.loads(response.text)
        if 'url' not in download_json:
            raise ValueError(_('Failed to download assets from BowlRoll. Incorrect download key.'))

        return session.get(download_json['url'], stream=True)

    @staticmethod
    def gdrive(url: str) -> requests.models.Response:
        parsed = urllib.parse.urlparse(url)

        match = re.match(r'^/file/d/(.*?)/view$', parsed.path)
        if match:
            file_id = match.groups()[0]
        else:
            query = urllib.parse.parse_qs(parsed.query)
            if 'id' in query and parsed.hostname == 'drive.google.com':
                file_id = query['id'][0]
            else:
                raise ValueError(_('Failed to download assets from Google Drive. Incorrect download key.'))

        download_url = urllib.parse.urljoin(url, '/uc')

        session = requests.Session()
        response = session.get(download_url, params={'id': file_id}, stream=True)
        response.raise_for_status()

        warning = [value for key, value in response.cookies.items() if key.startswith('download_warning')]

        if len(warning) == 0:
            return response

        return session.get(
            download_url,
            params={'id': file_id, 'confirm': warning[0]},
            stream=True
        )

    @staticmethod
    def onedrive(url: str) -> requests.models.Response:
        # https://stackoverflow.com/questions/37857098/download-onedrive-file-from-curl-since-theyve-changed-their-urls-construction
        parsed = urllib.parse.urlparse(url)
        match = re.match(r'^/[^/]+/(s!.*)$', parsed.path)
        if not match:
            raise ValueError(_('Failed to download assets from OneDrive. Incorrect download key.'))

        file_id = match.groups()[0]
        download_url = f'https://api.onedrive.com/v1.0/shares/{file_id}/root/content'

        session = requests.Session()
        return session.get(
            download_url,
            stream=True,
            allow_redirects=True
        )

    @staticmethod
    def uploader(url: str, password=None) -> requests.models.Response:
        error_message = _('Failed to download assets from uploader.jp. The response format may have changed.')
        session = requests.Session()

        if password is None:
            response = session.get(url)
        else:
            response = session.post(url, data={'password': password, 'q': 'age_confirmation'})
        response.raise_for_status()

        match = re.search(r'<input +type="hidden" +name="token" value="([^"]+)" ', response.text)
        if match is None:
            raise ValueError(error_message)

        response = session.post(url, data={'token': match.group(1)})
        response.raise_for_status()

        match = re.search(r'<a +href="([^"]+)"[^>]*>Download Now</a>', response.text)
        if match is None:
            raise ValueError(error_message)

        return session.get(match.group(1).replace('&#45;', '-'), stream=True)

    @staticmethod
    def execute_action(download_action: str):
        tree = ast.parse(download_action)

        functions = {
            'get': functools.partial(DownloadActionExecutor.get),
            'tstorage': functools.partial(DownloadActionExecutor.tstorage),
            'smutbase': functools.partial(DownloadActionExecutor.smutbase),
            'bowlroll': functools.partial(DownloadActionExecutor.bowlroll),
            'gdrive': functools.partial(DownloadActionExecutor.gdrive),
            'onedrive': functools.partial(DownloadActionExecutor.onedrive),
            'uploader': functools.partial(DownloadActionExecutor.uploader),
        }

        RestrictionChecker(*(functions.keys())).visit(tree)

        ast.dump(tree)
        return eval(  # pylint: disable=eval-used
            download_action,
            {'__builtins__': {}},
            {
                **functions
            }
        )


class ImportActionExecutor:
    @staticmethod
    def unzip(zip_file_path=None, encoding='cp437', password=None, asset=None):
        asset_path, asset_json = _Utilities.resolve_path(asset)

        print(f'unzip({zip_file_path},{asset_path},{asset_json})')

        if _Utilities.is_extracted(asset):
            return

        pwd = password.encode() if password else None

        with zipfile.ZipFile(zip_file_path) as zip_file:
            for info in zip_file.infolist():
                if info.flag_bits ^ 0x800:
                    info.filename = info.orig_filename.encode('cp437').decode(encoding)

                if os.sep != '/' and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, '/')

                zip_file.extract(info, path=asset_path, pwd=pwd)

        _Utilities.write_json(asset)
        ImportActionExecutor.chmod_recursively(asset_path, stat.S_IWRITE)

    @staticmethod
    def unrar(rar_file_path=None, password=None, asset=None):
        asset_path, asset_json = _Utilities.resolve_path(asset)

        print(f'unrar({rar_file_path},{asset_path},{asset_json})')

        if _Utilities.is_extracted(asset):
            return

        namespace = 'xrarfile'
        loader = importlib.machinery.SourceFileLoader(namespace, os.path.join(PACKAGE_PATH, 'externals', 'xrarfile', 'xrarfile.py'))
        xrarfile = loader.load_module(namespace)  # pylint: disable=deprecated-method

        try:
            with xrarfile.XRarFile(rar_file_path) as rar:
                rar.extractall(path=asset_path, pwd=password)
        except xrarfile.XRarCannotExec as ex:
            raise MessageException(_('Failed to execute unrar or WinRAR\nPlease install unrar or WinRAR and setup the PATH properly.')) from ex

        _Utilities.write_json(asset)
        ImportActionExecutor.chmod_recursively(asset_path, stat.S_IWRITE)

    @staticmethod
    def un7zip(zip_file_path=None, password=None, asset=None):
        asset_path, asset_json = _Utilities.resolve_path(asset)

        print(f'un7zip({zip_file_path},{asset_path},{asset_json})')

        if _Utilities.is_extracted(asset):
            return

        namespace = 'x7zipfile'
        loader = importlib.machinery.SourceFileLoader(namespace, os.path.join(PACKAGE_PATH, 'externals', 'x7zipfile', 'x7zipfile.py'))
        x7zipfile = loader.load_module(namespace)  # pylint: disable=deprecated-method

        try:
            with x7zipfile.x7ZipFile(zip_file_path, pwd=password) as zip_file:
                zip_file.extractall(path=asset_path)
        except x7zipfile.x7ZipCannotExec as ex:
            raise MessageException(_('Failed to execute 7z\nPlease install p7zip-full or 7-zip and setup the PATH properly.')) from ex

        _Utilities.write_json(asset)
        ImportActionExecutor.chmod_recursively(asset_path, stat.S_IWRITE)

    @staticmethod
    def link(to_name, from_path=None, asset=None):
        asset_path, asset_json = _Utilities.resolve_path(asset)

        print(f'link({to_name},{from_path},{asset_path},{asset_json})')

        if _Utilities.is_extracted(asset):
            return

        to_path = os.path.join(asset_path, to_name)

        os.makedirs(asset_path, exist_ok=True)
        try:
            os.link(from_path, to_path)
        except OSError as ex:
            # Invalid cross-device link
            if ex.errno != errno.EXDEV:
                raise ex
            shutil.copyfile(from_path, to_path)

        _Utilities.write_json(asset)
        ImportActionExecutor.chmod_recursively(asset_path, stat.S_IWRITE)

    @staticmethod
    def chmod_recursively(path, mode):
        for root, dirs, files in os.walk(path):
            for dir_name in dirs:
                target = os.path.join(root, dir_name)
                os.chmod(target, os.stat(target).st_mode | mode)

            for file in files:
                target = os.path.join(root, file)
                os.chmod(target, os.stat(target).st_mode | mode)

    @staticmethod
    def import_collections(blend_file_path, *collection_names, asset=None):
        asset_path, _asset_json = _Utilities.resolve_path(asset)

        print(f'import_collections({blend_file_path},{collection_names},{asset_path})')
        bpy.ops.wm.append(
            # 'INVOKE_DEFAULT',
            # filepath=os.path.join(asset_path, blend_file_path, 'Collection', collection_name),
            directory=os.path.join(asset_path, blend_file_path, 'Collection'),
            files=[{'name': name} for name in collection_names],
        )

    @staticmethod
    def import_world(blend_file_path, world_name, asset=None):
        asset_path, _asset_json = _Utilities.resolve_path(asset)

        print(f'import_world({blend_file_path},{world_name},{asset_path})')

        bpy.ops.wm.append(
            directory=os.path.join(asset_path, blend_file_path, 'World'),
            files=[{'name': world_name}],
        )

        bpy.context.scene.world = bpy.data.worlds[world_name]

    @staticmethod
    def import_pmx(pmx_file_path, scale=0.08, asset=None):
        asset_path, _asset_json = _Utilities.resolve_path(asset)

        print(f'import_pmx({pmx_file_path},{scale},{asset_path})')
        try:
            bpy.ops.mmd_tools.import_model('INVOKE_DEFAULT', filepath=os.path.join(asset_path, pmx_file_path), scale=scale)
        except AttributeError as ex:
            if str(ex) != 'Calling operator "bpy.ops.mmd_tools.import_model" error, could not be found':
                raise
            raise MessageException(_('Failed to invoke mmd_tools\nPlease install mmd_tools.')) from ex

    @staticmethod
    def import_vmd(vmd_file_path, scale=0.08, asset=None):
        asset_path, _asset_json = _Utilities.resolve_path(asset)

        print(f'import_vmd({vmd_file_path},{scale},{asset_path})')
        try:
            bpy.ops.mmd_tools.import_vmd('INVOKE_DEFAULT', filepath=os.path.join(asset_path, vmd_file_path), scale=scale)
        except AttributeError as ex:
            if str(ex) != 'Calling operator "bpy.ops.mmd_tools.import_vmd" error, could not be found':
                raise
            raise MessageException(_('Failed to invoke mmd_tools\nPlease install mmd_tools.')) from ex
        except RuntimeError as ex:
            if str(ex) != 'Operator bpy.ops.mmd_tools.import_vmd.poll() failed, context is incorrect':
                raise
            raise MessageException(_('Select an object.\nThe target object for motion import is not selected.')) from ex

    @staticmethod
    def import_vpd(vpd_file_path, scale=0.08, asset=None):
        asset_path, _asset_json = _Utilities.resolve_path(asset)

        print(f'import_vpd({vpd_file_path},{scale},{asset_path})')
        try:
            bpy.ops.mmd_tools.import_vpd('INVOKE_DEFAULT', filepath=os.path.join(asset_path, vpd_file_path), scale=scale)
        except AttributeError as ex:
            if str(ex) != 'Calling operator "bpy.ops.mmd_tools.import_vpd" error, could not be found':
                raise
            raise MessageException(_('Failed to invoke mmd_tools\nPlease install mmd_tools.')) from ex
        except RuntimeError as ex:
            if str(ex) != 'Operator bpy.ops.mmd_tools.import_vpd.poll() failed, context is incorrect':
                raise
            raise MessageException(_('Select an object.\nThe target object for pose import is not selected.')) from ex

    @staticmethod
    def delete_objects(prefix=None, suffix=None, recursive=False):
        print(f'delete_objects({prefix},{suffix})')

        if prefix is None and suffix is None:
            return

        if recursive:
            # TODO
            raise NotImplementedError('TODO')

        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.view_layer.active_layer_collection.collection.objects:
            if (prefix is None or obj.name.startswith(prefix)) and (suffix is None or obj.name.endswith(suffix)):
                obj.select_set(True)

        bpy.ops.object.delete()

    @staticmethod
    def execute_import_action(asset: AssetDescription, target_file: Optional[str]):
        tree = ast.parse(asset.import_action)

        functions = {
            'unzip': functools.partial(ImportActionExecutor.unzip, zip_file_path=target_file, asset=asset),
            'un7zip': functools.partial(ImportActionExecutor.un7zip, zip_file_path=target_file, asset=asset),
            'unrar': functools.partial(ImportActionExecutor.unrar, rar_file_path=target_file, asset=asset),
            'link': functools.partial(ImportActionExecutor.link, from_path=target_file, asset=asset),
            'import_collections': functools.partial(ImportActionExecutor.import_collections, asset=asset),
            'import_world': functools.partial(ImportActionExecutor.import_world, asset=asset),
            'import_pmx': functools.partial(ImportActionExecutor.import_pmx, asset=asset),
            'import_vmd': functools.partial(ImportActionExecutor.import_vmd, asset=asset),
            'import_vpd': functools.partial(ImportActionExecutor.import_vpd, asset=asset),
            'delete_objects': functools.partial(ImportActionExecutor.delete_objects),
        }

        RestrictionChecker(*(functions.keys())).visit(tree)

        try:
            exec(  # pylint: disable=exec-used
                compile(tree, '<source>', 'exec'),
                {'__builtins__': {}},
                {
                    **functions
                }
            )
        except FileNotFoundError as ex:
            if os.sys.platform == 'win32':
                message = str(ex)
                if message.startswith('[Errno 2] No such file or directory: ') and len(message) > 260+38:
                    raise MessageException(_('The file path is too long. This can be alleviated to some extent by shortening the Asset Extract Root Folder in the Add-on Preferences.')) from ex

            raise
