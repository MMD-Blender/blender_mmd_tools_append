# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import hashlib
import importlib.util
import logging
import math
import re
import sys

import bpy

from .m17n import _


def to_int32(value: int) -> int:
    return ((value & 0xFFFFFFFF) ^ 0x80000000) - 0x80000000


def strict_hash(text: str) -> int:
    return to_int32(int(hashlib.sha1(text.encode("utf-8")).hexdigest(), 16))


SI_PREFIXES = ["", " k", " M", " G", " T", "P", "E"]


def to_human_friendly_text(number: float) -> str:
    if number == 0:
        return "0"

    prefix_index = max(0, min(len(SI_PREFIXES) - 1, int(math.floor(math.log10(abs(number)) / 3))))
    return f"{number / 10 ** (3 * prefix_index):.2f}{SI_PREFIXES[prefix_index]}"


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def sanitize_path_fragment(path_fragment: str) -> str:
    illegal_re = r'[\/\?<>\\:\*\|"]'
    control_re = r"[\x00-\x1f\x80-\x9f]"
    reserved_re = r"^\.+$"
    windows_reserved_re = r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?$"
    windows_trailing_re = r"[\. ]+$"

    return re.sub(
        windows_trailing_re,
        "",
        re.sub(windows_reserved_re, "", re.sub(reserved_re, "", re.sub(control_re, "", re.sub(illegal_re, "", path_fragment)))),
    )


def import_from_file(module_name: str, module_path: str):
    module_name = f"bl_ext.blender_org.mmd_tools_append.{module_name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module '{module_name}' from '{module_path}'")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # ensures single instance if repeatedly called
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def is_mmd_tools_installed():
    candidates = (
        "bl_ext.blender_org.mmd_tools",
        "bl_ext.vscode_development.mmd_tools",
    )

    for name in candidates:
        try:
            if name in sys.modules or importlib.util.find_spec(name) is not None:
                return True
        except:
            pass

    return False


_MMD_TOOLS_CACHE = None

MMD_TOOLS_IMPORT_HOOKS = []


def import_mmd_tools():
    global _MMD_TOOLS_CACHE
    global MMD_TOOLS_IMPORT_HOOKS

    if _MMD_TOOLS_CACHE is not None:
        return _MMD_TOOLS_CACHE

    try:
        _MMD_TOOLS_CACHE = importlib.import_module("bl_ext.blender_org.mmd_tools")
    except Exception as exception:
        try:
            _MMD_TOOLS_CACHE = importlib.import_module("bl_ext.vscode_development.mmd_tools")
        except:
            raise RuntimeError(_("MMD Tools is not installed correctly. Please install MMD Tools using the correct steps, as MMD Tools Append depends on MMD Tools.")) from exception

    for hook in MMD_TOOLS_IMPORT_HOOKS:
        try:
            hook(_MMD_TOOLS_CACHE)
        except:
            logging.exception(f"Warning: An error occurred in import_mmd_tools hook {hook}")

    return _MMD_TOOLS_CACHE


def label_multiline(layout, text="", width=0):
    if text.strip() == "":
        return

    threshold = int(width / 5.5) if width > 0 else 35
    for line in text.split("\n"):
        while len(line) > threshold:
            space_index = line.rfind(" ", 0, threshold)
            layout.label(text=line[:space_index])
            line = line[space_index:].lstrip()
        layout.label(text=line)


def raise_installation_error(base_from):
    raise RuntimeError(_("MMD Tools Append is not installed correctly. Please reinstall MMD Tools Append using the correct steps.")) from base_from


class MessageException(Exception):
    """Class for error with message."""
