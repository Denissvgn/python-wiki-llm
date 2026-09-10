"""TypedDict key presence is distinct from defaults and nullability."""

import textwrap

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.bootstrap_runtime import _generate_entity_md


def _extract(tmp_path, sources):
    for name, source in sources.items():
        (tmp_path / name).write_text(textwrap.dedent(source), encoding="utf-8")
    return PythonExtractor().extract(
        str(tmp_path), deep=True, source_files=list(sources)
    )


def _classes(inventory, path):
    return {item["name"]: item for item in inventory[path]["classes"]}


def test_total_false_subclass_preserves_base_required_keys(tmp_path):
    inventory = _extract(
        tmp_path,
        {
            "types.py": """
        from typing import TypedDict
        class Base(TypedDict):
            required: int
        class Result(Base, total=False):
            selection: str
        class Child(Result):
            new_required: int
    """
        },
    )
    classes = _classes(inventory, "types.py")
    assert classes["Result"]["model_kind"] == "typeddict"
    assert classes["Base"]["attributes"][0]["required"] is True
    assert classes["Result"]["attributes"][0]["required"] is False
    assert classes["Child"]["attributes"][0]["required"] is True
    markdown = _generate_entity_md(classes["Result"], "types.py", {})
    assert "| `selection` | `str` | *optional* |" in markdown
    assert "`*optional*`" not in markdown


def test_imported_aliased_typeddict_and_explicit_presence_overrides(tmp_path):
    inventory = _extract(
        tmp_path,
        {
            "base.py": "from typing_extensions import TypedDict as TD\nclass Base(TD):\n    key: int\n",
            "child.py": """
            from base import Base as Parent
            from typing_extensions import Required as R, NotRequired as N, Annotated
            from typing import Optional
            class Result(Parent, total=False):
                required: R[Optional[str]]
                optional: N[str]
                quoted: "R[int]"
                annotated: Annotated[R[int], "metadata"]
        """,
        },
    )
    cls = _classes(inventory, "child.py")["Result"]
    attrs = {attr["name"]: attr for attr in cls["attributes"]}
    assert cls["model_kind"] == "typeddict"
    assert attrs["required"]["required"] is True
    assert attrs["required"]["nullable"] is True
    assert attrs["optional"]["required"] is False
    assert attrs["optional"]["nullable"] is False
    assert attrs["quoted"]["required"] is True
    assert attrs["annotated"]["required"] is True


def test_unresolved_base_does_not_borrow_same_named_typeddict(tmp_path):
    inventory = _extract(
        tmp_path,
        {
            "base.py": "from typing import TypedDict\nclass Base(TypedDict):\n    key: int\n",
            "child.py": "from missing import Base\nclass Result(Base, total=False):\n    selection: str\n",
        },
    )
    assert _classes(inventory, "child.py")["Result"].get("model_kind") != "typeddict"


def test_unknown_total_is_not_reported_as_required(tmp_path):
    inventory = _extract(
        tmp_path,
        {
            "types.py": """
        from typing import TypedDict, Required
        class Result(TypedDict, total=unknown_policy()):
            selection: str
            required: Required[int]
    """
        },
    )
    cls = _classes(inventory, "types.py")["Result"]
    assert "required" not in cls["attributes"][0]
    assert cls["attributes"][1]["required"] is True
    assert "| `selection` | `str` | *unknown* |" in _generate_entity_md(
        cls, "types.py", {}
    )


def test_regular_class_and_dataclass_defaults_are_unchanged(tmp_path):
    inventory = _extract(
        tmp_path,
        {
            "types.py": """
        from dataclasses import dataclass
        @dataclass
        class Record:
            required: int
            defaulted: int = 3
    """
        },
    )
    cls = _classes(inventory, "types.py")["Record"]
    markdown = _generate_entity_md(cls, "types.py", {})
    assert "| `required` | `int` | *required* |" in markdown
    assert "| `defaulted` | `int` | `3` |" in markdown
