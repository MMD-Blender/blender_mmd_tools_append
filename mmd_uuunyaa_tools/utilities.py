# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import hashlib
import importlib
import importlib.util
import math
import re

import bpy
from .m17n import _


def to_int32(value: int) -> int:
    return ((value & 0xffffffff) ^ 0x80000000) - 0x80000000


def strict_hash(text: str) -> int:
    return to_int32(int(hashlib.sha1(text.encode('utf-8')).hexdigest(), 16))


SI_PREFIXES = ['', ' k', ' M', ' G', ' T', 'P', 'E']


def to_human_friendly_text(number: float) -> str:
    if number == 0:
        return '0'

    prefix_index = max(
        0,
        min(
            len(SI_PREFIXES)-1,
            int(math.floor(math.log10(abs(number))/3))
        )
    )
    return f'{number / 10**(3 * prefix_index):.2f}{SI_PREFIXES[prefix_index]}'


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def sanitize_path_fragment(path_fragment: str) -> str:
    illegal_re = r'[\/\?<>\\:\*\|"]'
    control_re = r'[\x00-\x1f\x80-\x9f]'
    reserved_re = r'^\.+$'
    windows_reserved_re = r'^(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?$'
    windows_trailing_re = r'[\. ]+$'

    return re.sub(
        windows_trailing_re, '',
        re.sub(
            windows_reserved_re, '',
            re.sub(
                reserved_re, '',
                re.sub(
                    control_re, '',
                    re.sub(
                        illegal_re, '',
                        path_fragment
                    )
                )
            )
        )
    )


def is_mmd_tools_installed() -> bool:
    return importlib.util.find_spec('bl_ext.blender_org.mmd_tools')  # pylint: disable=deprecated-method


def import_mmd_tools():
    try:
        return importlib.import_module('bl_ext.blender_org.mmd_tools')
    except ImportError as exception:
        raise RuntimeError(_("MMD Tools is not installed correctly. Please install MMD Tools using the correct steps, as UuuNyaa Tools depends on MMD Tools.")) from exception


def label_multiline(layout, text='', width=0):
    if text.strip() == '':
        return

    threshold = int(width / 5.5) if width > 0 else 35
    for line in text.split('\n'):
        while len(line) > threshold:
            space_index = line.rfind(' ', 0, threshold)
            layout.label(text=line[:space_index])
            line = line[space_index:].lstrip()
        layout.label(text=line)


def raise_installation_error(base_from):
    raise RuntimeError(_("MMD UuuNyaa Tools is not installed correctly. Please reinstall MMD UuuNyaa Tools using the correct steps.")) from base_from


class MessageException(Exception):
    """Class for error with message."""
