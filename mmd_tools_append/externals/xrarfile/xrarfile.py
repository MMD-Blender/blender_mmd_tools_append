# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of xrarfile.
#
# BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import errno
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

_WIN32 = sys.platform == "win32"


@dataclass
class XRarInfo:
    pass


class XRarError(Exception):
    """Base class for xrarfile errors."""


class XRarNoEntry(XRarError):
    """File not found in archive"""


class XRarExecError(XRarError):
    """Problem reported by RAR."""


class XRarCannotExec(XRarExecError):
    """Executable not found."""


class _Executor(ABC):
    def __init__(self, executable: str):
        if sys.platform == "darwin" and os.path.sep not in executable:
            self.executable = self._macos_path_resolve(executable)
        else:
            self.executable = executable

    @staticmethod
    def _macos_path_resolve(executable: str) -> str:
        mac_common_paths = [
            "/opt/homebrew/bin/",
            "/usr/local/bin/",
            "/opt/local/bin",
            os.path.expanduser("~/.local/bin"),
        ]
        for path in mac_common_paths:
            full_path = os.path.join(path, executable)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path

        return executable

    def is_available(self, expect_returncode=0) -> bool:
        try:
            process = self._popen(self.executable)
            _, _ = process.communicate(timeout=1)
            process.wait()
            return process.returncode == expect_returncode
        except:  # pylint: disable=bare-except
            return False

    @staticmethod
    def _popen(command: str | list[str]) -> subprocess.Popen:
        """Disconnect command from parent fds, read only from stdout."""
        try:
            return subprocess.Popen(
                command,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                creationflags=0x08000000 if _WIN32 else 0,  # CREATE_NO_WINDOW
            )
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                raise XRarCannotExec("RAR not installed?") from None
            if ex.errno == errno.EACCES or ex.errno == errno.EPERM:
                raise XRarCannotExec("Cannot execute RAR") from None
            raise

    def execute(self, command: str | list[str]) -> Iterator[str]:
        linesep = os.linesep
        process = self._popen(command)
        while True:
            line = process.stdout.readline()
            if line is not None:
                yield line.decode("utf-8", "ignore").rstrip(linesep)

            if not line and process.poll() is not None:
                break

        exit_code = process.poll()
        error_message = process.stderr.read().decode("utf-8", "ignore").strip()

        for stream in [process.stdin, process.stdout, process.stderr]:
            try:
                stream.close()
            except:  # pylint: disable=bare-except
                pass

        if exit_code == 0:
            return

        raise XRarExecError(error_message)

    @abstractmethod
    def execute_extractall(
        self,
        archive_name: str,
        output_directory: str | None = None,
        password: str | None = None,
        other_options: list[str] | None = None,
    ):
        pass


class UnrarExecutor(_Executor):
    def execute_extractall(
        self,
        archive_name: str,
        output_directory: str | None = None,
        password: str | None = None,
        other_options: list[str] | None = None,
    ):
        command = [self.executable, "x", "-y", "-o+"]

        if password is not None:
            command.append(f"-p{password}")

        if other_options is not None:
            command.extend(other_options)

        if _WIN32 and archive_name[-4:].lower() != ".rar":
            archive_name += ".*"

        command.append(archive_name)

        if output_directory is not None:
            command.append(output_directory + ("" if output_directory.endswith(os.path.sep) else os.path.sep))

        for _ in self.execute(command):
            pass


class UnarExecutor(_Executor):
    def is_available(self, expect_returncode=1) -> bool:
        return super().is_available(expect_returncode)

    def execute_extractall(
        self,
        archive_name: str,
        output_directory: str | None = None,
        password: str | None = None,
        other_options: list[str] | None = None,
    ):
        command = [self.executable, "-force-overwrite"]

        if output_directory is not None:
            command.extend(["-output-directory", output_directory])

        if password is not None:
            command.extend(["-password", password])

        if other_options is not None:
            command.extend(other_options)

        command.append(archive_name)

        for _ in self.execute(command):
            pass


_EXECUTORS = [
    UnrarExecutor("unrar"),
    UnarExecutor("unar"),
] + (
    [
        UnrarExecutor("UnRAR.exe"),
    ]
    if _WIN32
    else []
)

_EXECUTOR: _Executor = None


def get_executor() -> _Executor:
    global _EXECUTOR  # pylint: disable=global-statement

    if _EXECUTOR is not None:
        return _EXECUTOR

    for executor in _EXECUTORS:
        if executor.is_available():
            _EXECUTOR = executor
            return _EXECUTOR

    raise XRarCannotExec("Cannot find working RAR command. Please install RAR and setup the PATH properly.")


class XRarFile:
    """Class with methods to open, close, list RAR files."""

    def __init__(
        self,
        file: str | bytes | os.PathLike,
        mode: str = "r",
        pwd: str | None = None,
    ):
        """Open the RAR file with mode read 'r'."""
        self._file = file if not isinstance(file, os.PathLike) else str(file)

        if mode != "r":
            raise NotImplementedError("XRarFile supports only mode=r")

        self._pwd = pwd

        self._executor = get_executor()

    def __enter__(self) -> "XRarFile":
        """Open context."""
        return self

    def __exit__(self, typ, value, traceback):
        """Exit context."""
        self.close()

    def open(self):
        raise NotImplementedError("XRarFile does not yet support open")

    def close(self):
        """Release open resources."""

    def infolist(self) -> list[XRarInfo]:
        raise NotImplementedError("XRarFile does not yet support infolist")

    def getinfo(self, member: str) -> XRarInfo:
        raise NotImplementedError("XRarFile does not yet support getinfo")

    def namelist(self) -> list[str]:
        raise NotImplementedError("XRarFile does not yet support namelist")

    def extract(self, member: str | XRarInfo, path: str | None = None, pwd: str | None = None):
        raise NotImplementedError("XRarFile does not yet support extract")

    def extractall(self, path: str | None = None, members: list[str | XRarInfo] | None = None, pwd: str | None = None):
        """Extract all files into current directory.
        Parameters:

            path
                optional destination path
            members
                optional filename or :class:`XRarInfo` instance list to extract
            pwd
                optional password to use
        """

        if members is not None:
            raise NotImplementedError("XRarFile does not yet support extractall with members")

        self._executor.execute_extractall(
            archive_name=self._file,
            output_directory=path,
            password=pwd or self._pwd,
        )
