"""Base-owned collection witness for selected PR tests, with no deselection."""

import json
import os
from pathlib import Path


_collected = []
_deselected = []


def pytest_itemcollected(item):
    _collected.append(item.nodeid)


def pytest_deselected(items):
    _deselected.extend(item.nodeid for item in items)


def pytest_collection_finish(session):
    Path(os.environ["PR_CI_COLLECTION"]).write_text(
        json.dumps(
            {
                "collected": _collected,
                "selected": [item.nodeid for item in session.items],
                "deselected": _deselected,
            }
        ),
        encoding="utf-8",
    )
