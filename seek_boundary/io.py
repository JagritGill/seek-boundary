"""Bounded regular-file JSON loading. No database, network or stdin reads."""

import json
import os
import stat

from .model import InputError

MAX_BYTES = 2_097_152


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON object key")
        result[key] = value
    return result


def _constant(_value):
    raise InputError("non-finite JSON number")


def load(path):
    # Refuse special files before opening and check again after opening. Nonblock
    # avoids waiting if a stable-file assumption is violated by a FIFO replacement.
    # This is not a sandbox against adversarial concurrent filesystem changes.
    fd = None
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            raise InputError("input must be a regular file, not a symlink")
        flags = os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            fd = None
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise InputError("input must be a regular file")
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise InputError("input exceeds 2097152 bytes")
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    except InputError:
        raise
    except (OSError, ValueError, RecursionError):
        raise InputError("cannot read a valid UTF-8 JSON document") from None
    finally:
        if fd is not None:
            os.close(fd)
