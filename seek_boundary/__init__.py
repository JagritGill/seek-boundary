"""Finite-snapshot strict prefix-cursor audits."""

from .core import audit
from .model import InputError

__all__ = ["audit", "InputError"]
