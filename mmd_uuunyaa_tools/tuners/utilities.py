# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import os

import bpy
from ..utilities import raise_installation_error


class ObjectMarker:
    def __init__(self, mark_id: str):
        self.mark_id = mark_id

    def mark(self, obj, depth=0):
        obj[self.mark_id] = True

        if depth <= 0:
            return

        for child in obj.children:
            self.mark(child, depth=depth-1)

    def unmark(self, obj, depth=0):
        if self.is_marked(obj):
            del obj[self.mark_id]

        if depth <= 0:
            return

        for child in obj.children:
            self.unmark(child, depth=depth-1)

    def is_marked(self, obj) -> bool:
        return self.mark_id in obj


class ObjectAppender(ObjectMarker):
    def __init__(self, mark_id: str, blend_filename: str):
        super().__init__(mark_id)
        self.blend_filename = blend_filename

    def remove_objects(self, target_collection: bpy.types.Collection = None):
        target = target_collection if target_collection is not None else bpy.context.view_layer.active_layer_collection.collection

        if not self.is_marked(target):
            return

        for obj in target.objects.values():
            if not self.is_marked(obj):
                continue

            bpy.data.objects.remove(obj, do_unlink=True)

        self.unmark(target)

    def append_collection(self, collection_name: str):
        if collection_name not in bpy.data.collections:
            path = os.path.join(self.blend_filename)

            try:
                with bpy.data.libraries.load(path, link=False) as (_, data_to):
                    data_to.collections = [collection_name]
            except OSError as exception:
                raise_installation_error(exception)

        return bpy.data.collections[collection_name]

    def append_objects_from_collection(self, collection_name: str, target_collection: bpy.types.Collection = None):
        source = self.append_collection(collection_name)
        target = target_collection if target_collection is not None else bpy.context.view_layer.active_layer_collection.collection
        self.mark(target)
        for obj in source.objects.values():
            self.mark(obj)
            source.objects.unlink(obj)
            target.objects.link(obj)
        bpy.data.collections.remove(source)
