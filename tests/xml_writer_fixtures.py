"""Exercise ElementTree's native text-file newline behavior on any test host."""

import builtins
from contextlib import contextmanager
import xml.etree.ElementTree as ET


@contextmanager
def elementtree_text_newlines(monkeypatch, newline):
    def native_open(file, mode="r", **kwargs):
        if "b" not in mode:
            kwargs.setdefault("newline", newline)
        return builtins.open(file, mode, **kwargs)

    # ElementTree uses its module's open() for filename output. Binary stream
    # output uses its own explicit LF wrapper, independent of the host default.
    with monkeypatch.context() as patch:
        patch.setattr(ET, "open", native_open, raising=False)
        yield
