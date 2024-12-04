# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

import hashlib
import json
import os
import shutil
import tempfile
import threading
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import Callable, Dict, List, Optional, OrderedDict

from .. import REGISTER_HOOKS
from ..asset_search.url_resolvers import (URLResolver,
                                                          URLResolverABC)
from ..utilities import get_preferences

URL = str
Callback = Callable[['Content'], None]


class Content:
    # pylint: disable=too-few-public-methods

    class State(Enum):
        FETCHING = 1
        CACHED = 2
        FAILED = 3

    id: str
    state: State
    filepath: str = None
    type: str = None
    length: int = 0

    def __init__(
        self,
        id: str,
        state: State,
        filepath: str = None,
        type: str = None,
        length: int = 0,
    ):
        # pylint: disable=too-many-arguments,redefined-builtin
        self.id = id  # pylint: disable=invalid-name
        self.state = state
        self.filepath = filepath
        self.type = type
        self.length = length

    @staticmethod
    def to_content_id(url: URL) -> str:
        return hashlib.sha1(url.encode('utf-8')).hexdigest()


class Task:
    # pylint: disable=too-few-public-methods

    class State(Enum):
        QUEUING = 1
        RUNNING = 2
        SUCCESS = 3
        FAILURE = 4
        CANCELED = 5

    url: URL
    state: State
    callbacks: List[Callback]
    future: Future
    content_id: str
    fetched_size: int
    content_length: int

    def __init__(
        self,
        url: URL,
        state: State,
        callbacks: List[Callback] = None,
    ):
        self.url = url
        self.state = state
        self.callbacks = [] if callbacks is None else callbacks
        self.future = None
        self.content_id = Content.to_content_id(url)
        self.fetched_size = 0
        self.content_length = 0


class CacheABC(ABC):
    @abstractmethod
    def cancel_fetch(self, url: URL):
        pass

    @abstractmethod
    def remove_content(self, url: URL) -> bool:
        pass

    @abstractmethod
    def try_get_content(self, url: URL) -> Optional[Content]:
        pass

    @abstractmethod
    def try_get_task(self, url: URL) -> Optional[Task]:
        pass

    @abstractmethod
    def async_get_content(self, url: URL, callback: Callback) -> Future:
        pass


class ContentCache(CacheABC):
    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        cache_folder: str,
        temporary_dir: str,
        max_cache_size_bytes: int = 1024*1024*1024,
        max_workers: int = 10,
        contents_load: bool = True,
        contents_save_interval_secs: float = 5.0,
        url_resolver: URLResolverABC = URLResolver()
    ):
        print(f'ContentCache.__init__: cache_folder={cache_folder}, temporary_dir={temporary_dir}')
        self.cache_folder: str = cache_folder
        self.max_cache_size_bytes: int = max_cache_size_bytes
        self.temporary_dir = temporary_dir
        self.contents_save_interval_secs = contents_save_interval_secs
        self.url_resolver = url_resolver

        self._lock = threading.RLock()

        self._executor = ThreadPoolExecutor(max_workers)
        self._tasks: Dict[URL, Task] = {}

        self._contents: OrderedDict[str, Content] = OrderedDict()
        self._contents_size: int = 0

        self._contents_save_timer = None

        if contents_load:
            self._load_contents()

    def __del__(self):
        self._save_contents()
        self._executor.shutdown()

    def _load_contents(self):
        contents_json_path = os.path.join(self.cache_folder, 'contents.json')
        if not os.path.exists(contents_json_path):
            return

        with self._lock:
            with open(contents_json_path, 'r') as file:
                content_json = json.load(file, object_pairs_hook=OrderedDict)

            self._contents = OrderedDict({
                key: Content(
                    id=value['id'],
                    state=Content.State[value['state']],
                    filepath=os.path.join(self.cache_folder, value['filepath']),
                    type=value['type'],
                    length=value['length']
                ) for key, value in content_json.items()
            })
            self._contents_size = sum([c.length for c in self._contents.values()])

            print(f'_load_contents: {len(self._contents)} from {contents_json_path}')

    def _save_contents(self):
        contents_json_path = os.path.join(self.cache_folder, 'contents.json')
        with self._lock:
            print(f'_save_contents: {len(self._contents)} to {contents_json_path}')
            content_json = {
                key: {
                    'id': value.id,
                    'state': value.state.name,
                    'filepath': os.path.basename(value.filepath) if value.filepath else '',
                    'type': value.type,
                    'length': value.length
                } for key, value in self._contents.items()
            }
            with open(contents_json_path, 'w') as file:
                json.dump(content_json, file)

    def _schedule_save_contents(self):
        if self._contents_save_timer is not None:
            self._contents_save_timer.cancel()

        self._contents_save_timer = threading.Timer(self.contents_save_interval_secs, self._save_contents)
        self._contents_save_timer.start()

    def _to_content_filepath(self, content_id: str) -> str:
        return os.path.join(self.cache_folder, content_id)

    def _fetch(self, task: Task):
        # pylint: disable=too-many-statements
        with self._lock:
            if task.state is not Task.State.QUEUING:
                raise ValueError(f'task (={task.url}) is invalid state (={task.state})')

            task.state = Task.State.RUNNING
            content_id = task.content_id

        content_filepath = self._to_content_filepath(content_id)
        content = Content(content_id, Content.State.FETCHING)

        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=self.temporary_dir)
            with os.fdopen(temp_fd, 'bw') as temp_file:
                response = self.url_resolver.resolve(task.url)
                response.raise_for_status()

                content_type = response.headers.get('Content-Type')
                content_length_text = response.headers.get('Content-Length')
                content_length = int(content_length_text) if content_length_text else 0
                fetch_size = 0

                with self._lock:
                    task.content_length = content_length
                    task.fetched_size = fetch_size

                for chunk in response.iter_content(chunk_size=65536):
                    fetch_size += len(chunk)
                    with self._lock:
                        task.fetched_size = fetch_size
                        if task.state is not Task.State.RUNNING:
                            raise InterruptedError(f'task (={task.url}) fetch was interrupted')
                    temp_file.write(chunk)

            os.rename(temp_path, content_filepath)

            content_length = os.path.getsize(content_filepath)
            with self._lock:
                self._contents_size += content_length
                task.state = Task.State.SUCCESS

                content.state = Content.State.CACHED
                content.filepath = content_filepath
                content.length = content_length
                content.type = content_type

        except:  # pylint: disable=bare-except
            traceback.print_exc()
            with self._lock:
                content.state = Content.State.FAILED

                if task.state is Task.State.RUNNING:
                    task.state = Task.State.FAILURE
                else:
                    pass  # keep state

            if temp_path is not None:
                os.remove(temp_path)
        finally:
            with self._lock:
                self._contents[content_id] = content
                del self._tasks[task.url]

        self._invoke_callbacks(task)
        self._schedule_save_contents()
        return task

    @staticmethod
    def _invoke_callback(callback, content):
        try:
            callback(content)
        except:  # pylint: disable=bare-except
            traceback.print_exc()

    def _invoke_callbacks(self, task: Task):
        with self._lock:
            task_callbacks_copy = list(task.callbacks)
            task.callbacks.clear()
            content = self._contents[task.content_id]

        for callback in task_callbacks_copy:
            self._invoke_callback(callback, content)

        return task

    def cancel_fetch(self, url: URL):
        with self._lock:
            task = self.try_get_task(url)
            if task is None:
                return

            if task.state != Task.State.RUNNING:
                return

            task.state = Task.State.CANCELED

    def remove_content(self, url: URL) -> bool:
        with self._lock:
            content = self.try_get_content(url)
            if content is None:
                return False

            del self._contents[content.id]

            self._schedule_save_contents()

        return True

    def try_get_content(self, url: URL) -> Optional[Content]:
        content_id = Content.to_content_id(url)
        with self._lock:
            if content_id not in self._contents:
                return None

            content = self._contents[content_id]

            # LRU implementation
            self._contents.move_to_end(content_id)
            excess_cache_size = max(0, self._contents_size - self.max_cache_size_bytes)
            if excess_cache_size > 0:
                for content_id in self._contents.keys():
                    content = self._contents[content_id]

                    if content.length == 0:
                        continue

                    del self._contents[content_id]
                    self._contents_size -= content.length

                    if os.path.exists(content.file_path):
                        try:
                            os.remove(content.file_path)
                        except:  # pylint: disable=bare-except
                            traceback.print_exc()

                    excess_cache_size -= content.length
                    if excess_cache_size <= 0:
                        break

                self._schedule_save_contents()

            return content

    def try_get_task(self, url: URL) -> Optional[Task]:
        with self._lock:
            return self._tasks[url] if url in self._tasks else None

    def async_get_content(self, url: URL, callback: Callback) -> Future:
        def queue_callback():
            task = self._tasks[url]
            if task.state not in {Task.State.QUEUING, Task.State.RUNNING}:
                raise ValueError(f'task (={task.url}) is invalid state (={task.state})')
            task.callbacks.append(callback)
            return task.future

        with self._lock:
            if url in self._tasks:
                return queue_callback()

            content = self.try_get_content(url)
            if content is not None:
                match content.state:
                    case Content.State.CACHED:
                        return self._executor.submit(self._invoke_callback, callback, content)
                    case Content.State.FETCHING:
                        return queue_callback()
                    case _: # maybe failed
                        self.remove_content(url)

            task = Task(url, Task.State.QUEUING, [callback])
            task.future = self._executor.submit(self._fetch, task)
            self._tasks[url] = task
            return task.future


class ReloadableContentCache(CacheABC):
    _cache: CacheABC = None

    def __init__(self):
        pass

    def delete_cache_object(self):
        if self._cache is not None:
            with self._cache._lock:  # pylint: disable=protected-access
                try:
                    del self._cache
                except:  # pylint: disable=bare-except
                    traceback.print_exc()
            self._cache = None

    def reload(self):
        self.delete_cache_object()

        preferences = get_preferences()
        asset_cache_folder = preferences.asset_cache_folder
        if not os.path.exists(asset_cache_folder):
            os.makedirs(asset_cache_folder, exist_ok=True)

        self._cache = ContentCache(
            cache_folder=asset_cache_folder,
            max_cache_size_bytes=preferences.asset_max_cache_size*1024*1024,
            temporary_dir=tempfile.mkdtemp()
        )

    def cancel_fetch(self, url: URL):
        self._cache.cancel_fetch(url)

    def remove_content(self, url: URL) -> bool:
        return self._cache.remove_content(url)

    def try_get_content(self, url: URL) -> Optional[Content]:
        return self._cache.try_get_content(url)

    def try_get_task(self, url: URL) -> Optional[Task]:
        return self._cache.try_get_task(url)

    def async_get_content(self, url: URL, callback: Callback) -> Future:
        return self._cache.async_get_content(url, callback)

    def delete_cache_folder(self):
        cache_folder = self._cache.cache_folder
        self.delete_cache_object()

        shutil.rmtree(cache_folder, ignore_errors=True)
        self.reload()


CONTENT_CACHE = ReloadableContentCache()
REGISTER_HOOKS.append(CONTENT_CACHE.reload)
