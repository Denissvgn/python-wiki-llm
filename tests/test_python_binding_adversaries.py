"""Executed target stores and captured namespace aliases retain caller uncertainty."""

from __future__ import annotations

import ast

import pytest

from llm_wiki_cli.extractors.python_bindings import (
    analyze_python_bindings,
    valid_python_constructor_facts,
)
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.extraction_service import (
    resolve_call_edges,
    resolve_call_observations,
)

# Expectations are source-grounded counterexamples plus disconfirming controls.
FROZEN_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    batch = Batch()\n    batch: int\n    return batch.cap()\n",
        True,
        "original",
        id="CR-01-local-annotation",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    write = namespace.__setitem__\n    write('cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="CR-03-captured-class-mapping-method",
    ),
    pytest.param(
        "class Batch:\n    global namespace\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    result = [namespace.__setitem__('cap', lambda self: 'replacement') for _ in (0,)]\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="CR-04-eager-class-comprehension",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    first = Batch()\n    second = Other()\n    namespace = vars(first)\n    namespace[(namespace := vars(second)) or 'cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        "replacement",
        id="CR-05-target-base-capture",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    first = Batch()\n    write = vars(first).__setitem__\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        "replacement",
        id="CR-06-captured-instance-mapping-method",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    return Batch().cap()\n",
        True,
        "original",
        id="CR-07-direct-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    batch = Batch()\n    alias = batch\n    return alias.cap()\n",
        True,
        "original",
        id="CR-08-assigned-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    batch = Batch()\n    alias = batch\n    batch = alias if condition else alias\n    return batch.cap()\n",
        True,
        "original",
        id="CR-09-identical-branch-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    first = Batch()\n    condition and setattr(first, 'cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CR-10-conditional-side-effect",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    first = Batch()\n    0 < int(condition) < (setattr(first, 'cap', lambda: 'replacement') or 2)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CR-11-chained-compare-effect",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    first = Batch()\n    return first.cap(setattr(first, 'cap', lambda: 'replacement'))\n",
        True,
        "original",
        id="CR-12-callee-before-arguments",
    ),
    pytest.param(
        "from __future__ import annotations\nclass Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\nvalue: setattr(Batch, 'cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="CR-13-future-module-annotation",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'other'\ndef run(condition=False):\n    class Inner:\n        global namespace\n        namespace = locals()\n        later = (namespace.__setitem__('cap', lambda self: 'replacement') for _ in (0,))\n    return Batch().cap()\n",
        True,
        "original",
        id="CR-14-deferred-class-generator-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    batch = Batch()\n    for batch.cap in (lambda: 'replacement',):\n        pass\n    return batch.cap()\n",
        False,
        "replacement",
        id="CR-15-for-attribute-target",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    batch = Batch()\n    namespace = vars(batch)\n    for namespace['cap'] in (lambda: 'replacement',):\n        pass\n    return batch.cap()\n",
        False,
        "replacement",
        id="CR-16-for-subscript-target",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    batch = Batch()\n    class Manager:\n        def __enter__(self): return lambda: 'replacement'\n        def __exit__(self, *args): return False\n    with Manager() as batch.cap:\n        pass\n    return batch.cap()\n",
        False,
        "replacement",
        id="CR-17-with-attribute-target",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    batch = Batch()\n    for value in (1,):\n        pass\n    return batch.cap()\n",
        True,
        "original",
        id="CR-18-plain-for-positive",
    ),
]


FROZEN_CONDITIONAL_NAMESPACE_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C2-02-conditional-namespace-bound-writer",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first) if condition else {}\n    namespace.__setitem__('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C2-03-conditional-namespace-direct-write",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    (vars(first) if condition else {}).update(cap=lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C2-04-expression-namespace-update",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    write = (vars(first) if condition else {}).__setitem__\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C2-05-expression-namespace-bound-writer",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    eager = [locals().__setitem__('extra', 1) for _ in (0,)]\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="C2-06-class-comprehension-unrelated",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    eager = [None for _ in (locals().__setitem__('cap', lambda self: 'replacement') or (0,))]\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="C2-07-class-comprehension-outer-iter-effect",
    ),
]


FROZEN_SCOPE_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    third = Batch()\n    namespace = vars(first) if condition else vars(second)\n    write = namespace.__setitem__\n    write('cap', replacement)\n    return third.cap()\n",
        True,
        "original",
        id="C3-01-unrelated-instance",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    write('cap', (namespace := vars(second)) or replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-02-writer-before-namespace-argument-rebind",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else {}\n    namespace.__setitem__('cap', (namespace := {}) or replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-03-direct-writer-before-argument-rebind",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    write = (vars(first) if condition else {}).__setitem__\n    write('cap', (write := replacement))\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-04-writer-before-callee-variable-rebind",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else (vars(second) if not condition else {})\n    write = namespace.__setitem__\n    write('cap', replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-05-nested-conditional-owner",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else vars(second)\n    write = namespace.update\n    write(extra=1)\n    return first.cap()\n",
        True,
        "original",
        id="C3-06-unrelated-key-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    eager = [(vars(first) if condition else {}).__setitem__('cap', replacement) for _ in (0,)]\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-07-eager-conditional-mapping-comprehension",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    later = ((vars(first) if condition else {}).__setitem__('cap', replacement) for _ in (0,))\n    return first.cap()\n",
        True,
        "original",
        id="C3-08-deferred-conditional-mapping-generator",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    later = (None for _ in ((vars(first) if condition else {}).__setitem__('cap', replacement) or (0,)))\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="C3-09-generator-outer-iterable-effect",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else {}\n    eager = [namespace.__setitem__('cap', replacement) for namespace in ({},)]\n    return first.cap()\n",
        True,
        "original",
        id="C3-10-shadowed-comprehension-namespace",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first) if condition else {}\n    later = lambda: namespace.__setitem__('cap', replacement)\n    return first.cap()\n",
        True,
        "original",
        id="C3-11-deferred-namespace-lambda",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    replacement = lambda *args: 'replacement'\n    namespace = vars(first)\n    write = namespace.__setitem__ if condition else namespace.__setitem__\n    write('cap', replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="C3-12-identical-namespace-join",
    ),
]


FROZEN_GETTER_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    write = getattr(vars(first), '__setitem__')\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        "replacement",
        id="GA-01-instance-getattr-mapping-writer",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    write = getattr(namespace, '__setitem__')\n    write('cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="GA-02-class-getattr-mapping-writer",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    write = getattr(vars(first), '__setitem__')\n    write('extra', 1)\n    return first.cap()\n",
        True,
        "original",
        id="GA-03-unrelated-key-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    getattr = lambda obj, attr: (lambda *args: None)\n    write = getattr(vars(first), '__setitem__')\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        True,
        "original",
        id="GA-04-shadowed-getattr-positive",
    ),
    pytest.param(
        "import builtins as b\nclass Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    write = b.getattr(vars(first), 'update')\n    write(cap=lambda: 'replacement')\n    return first.cap()\n",
        False,
        "replacement",
        id="GA-05-builtins-getattr-alias",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    write = getattr(vars(first) if condition else {}, '__setitem__')\n    write('cap', lambda: 'replacement')\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="GA-06-conditional-namespace-getattr",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    write = getattr(namespace, '__setitem__')\n    write('cap', (namespace := {}) or (lambda: 'replacement'))\n    return first.cap()\n",
        False,
        "replacement",
        id="GA-07-getattr-writer-before-argument-rebind",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    getattr = lambda obj, attr: (lambda *args: None)\n    write = getattr(namespace, '__setitem__')\n    write('cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="GA-08-class-shadowed-getattr-positive",
    ),
]


FROZEN_UNBOUND_DICT_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    dict.__setitem__(namespace, 'cap', replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="UD-01-direct-dict-descriptor",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    write = dict.update\n    write(namespace, cap=replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="UD-02-captured-dict-update",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    write = dict.__setitem__\n    write(namespace, 'extra', 1)\n    return first.cap()\n",
        True,
        "original",
        id="UD-03-unrelated-key-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    later = dict.__setitem__\n    return first.cap()\n",
        True,
        "original",
        id="UD-04-uninvoked-descriptor-positive",
    ),
    pytest.param(
        "class Fake:\n    @staticmethod\n    def update(*args, **kwargs): return None\nclass Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    dict = Fake\n    write = dict.update\n    write(namespace, cap=replacement)\n    return first.cap()\n",
        True,
        "original",
        id="UD-05-shadowed-dict-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    dict.__setitem__(namespace, 'cap', (namespace := {}) or replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="UD-06-receiver-before-later-walrus",
    ),
    pytest.param(
        "from builtins import dict as mapping\nclass Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    mapping.__setitem__(namespace, 'cap', replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="UD-07-imported-dict-alias",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    dict.__setitem__(namespace, 'cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="UD-08-class-direct-descriptor",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    write = dict.update\n    write(namespace, cap=lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="UD-09-class-captured-update",
    ),
    pytest.param(
        "class Fake:\n    @staticmethod\n    def update(*args, **kwargs): return None\nclass Batch:\n    def cap(self, *args): return 'original'\n    dict = Fake\n    namespace = locals()\n    write = dict.update\n    write(namespace, cap=lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="UD-10-class-shadowed-dict-positive",
    ),
]


FROZEN_FACTORY_HELPER_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    factory = vars if condition else (lambda obj: {})\n    namespace = factory(first)\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CF-01-conditional-vars-factory",
    ),
    pytest.param(
        "flag = True\nclass Batch:\n    def cap(self, *args): return 'original'\n    factory = locals if flag else (lambda: {})\n    namespace = factory()\n    namespace['cap'] = lambda self: 'replacement'\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="CF-02-class-conditional-locals-factory",
    ),
    pytest.param(
        "flag = True\nclass Batch:\n    def cap(self, *args): return 'original'\nclass Other:\n    def cap(self, *args): return 'replacement'\nfactory = globals if flag else (lambda: {})\nnamespace = factory()\nnamespace['Batch'] = Other\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="CF-03-module-conditional-globals-factory",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    factory = vars if condition else (lambda obj: {})\n    return first.cap()\n",
        True,
        "original",
        id="CF-04-uninvoked-factory-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    factory = vars if condition else vars\n    namespace = factory(first)\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        "replacement",
        id="CF-05-identical-vars-factory",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    vars = lambda obj: {}\n    factory = vars if condition else vars\n    namespace = factory(first)\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        True,
        "original",
        id="CF-06-shadowed-vars-factory-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    writer = setattr if condition else (lambda *args: None)\n    writer(first, 'cap', replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CH-01-conditional-setattr-helper",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    getter = getattr if condition else (lambda *args: (lambda *args: None))\n    writer = getter(namespace, '__setitem__')\n    writer('cap', replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CH-02-conditional-getattr-helper",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    writer = setattr if condition else (lambda *args: None)\n    return first.cap()\n",
        True,
        "original",
        id="CH-03-uninvoked-conditional-setter-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    writer = setattr if condition else (lambda *args: None)\n    writer(second, 'cap', replacement)\n    return first.cap()\n",
        True,
        "original",
        id="CH-04-unrelated-target-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    getter = getattr if condition else (lambda *args: (lambda *args: None))\n    writer = getter(namespace, '__setitem__')\n    return first.cap()\n",
        True,
        "original",
        id="CH-05-uninvoked-conditional-getter-writer-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    getter = getattr if condition else getattr\n    writer = getter(namespace, '__setitem__')\n    writer('cap', replacement)\n    return first.cap()\n",
        False,
        "replacement",
        id="CH-06-identical-helper-branches",
    ),
    pytest.param(
        "from builtins import getattr as fetch\nclass Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    second = Batch()\n    namespace = vars(first)\n    replacement = lambda *args: 'replacement'\n    getter = fetch if condition else (lambda *args: (lambda *args: None))\n    writer = getter(namespace, '__setitem__')\n    writer('cap', replacement)\n    return first.cap()\n",
        False,
        ["original", "replacement"],
        id="CH-07-imported-conditional-getter-helper",
    ),
    pytest.param(
        "flag = True\nclass Batch:\n    def cap(self, *args): return 'original'\n    namespace = locals()\n    getter = getattr if flag else (lambda *args: (lambda *args: None))\n    writer = getter(namespace, '__setitem__')\n    writer('cap', lambda self: 'replacement')\ndef run(condition=False): return Batch().cap()\n",
        False,
        "replacement",
        id="CH-08-class-conditional-getter-helper",
    ),
]


FROZEN_PUBLIC_PROJECTION_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nwrite = dict.__setitem__\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="PF-01-module-descriptor-private-fact",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nfactory = lambda obj: {}\ndef run(condition=False): return Batch().cap()\n",
        True,
        "original",
        id="PF-02-module-empty-dict-factory-private-fact",
    ),
]


FROZEN_NAMESPACE_GETTER_CONTROLS = [
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = getattr(first, '__dict__')\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        "replacement",
        id="DN-01-getattr-dict-namespace",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = object.__getattribute__(first, '__dict__')\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        "replacement",
        id="DN-02-object-getattribute-dict-namespace",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = first.__getattribute__('__dict__')\n    namespace['cap'] = lambda: 'replacement'\n    return first.cap()\n",
        False,
        "replacement",
        id="DN-03-bound-getattribute-dict-namespace",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = getattr(first, '__dict__')\n    return first.cap()\n",
        True,
        "original",
        id="DN-04-getter-namespace-uninvoked-write-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\ndef run(condition=False):\n    first = Batch()\n    namespace = getattr(first, '__dict__')\n    namespace['extra'] = 1\n    return first.cap()\n",
        True,
        "original",
        id="DN-05-getter-namespace-unrelated-key-positive",
    ),
    pytest.param(
        "class Batch:\n    def cap(self, *args): return 'original'\nfirst = Batch()\nclass Holder:\n    namespace = getattr(first, '__dict__')\n    namespace['cap'] = lambda: 'replacement'\ndef run(condition=False): return first.cap()\n",
        False,
        "replacement",
        id="DN-06-eager-class-namespace-getter",
    ),
]


@pytest.mark.parametrize(
    "source,unique,runtime",
    FROZEN_CONTROLS
    + FROZEN_CONDITIONAL_NAMESPACE_CONTROLS
    + FROZEN_SCOPE_CONTROLS
    + FROZEN_GETTER_CONTROLS
    + FROZEN_UNBOUND_DICT_CONTROLS
    + FROZEN_FACTORY_HELPER_CONTROLS
    + FROZEN_PUBLIC_PROJECTION_CONTROLS
    + FROZEN_NAMESPACE_GETTER_CONTROLS,
)
def test_namespace_target_counterexamples_and_required_dispatch(
    tmp_path, source, unique, runtime
):
    namespace = {}
    exec(compile(source, "app.py", "exec"), namespace)
    expected = runtime if isinstance(runtime, list) else [runtime, runtime]
    assert [namespace["run"](False), namespace["run"](True)] == expected
    assert_dispatch(tmp_path, source, unique)


def assert_dispatch(tmp_path, source, unique):
    tree = ast.parse(source)
    captured = analyze_python_bindings(tree)
    call = sorted(
        [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "cap"
        ],
        key=lambda node: (node.lineno, node.col_offset),
    )[-1]
    binding = captured.calls[id(call)]
    if unique:
        assert binding["kind"] == "constructed-receiver"
        assert binding["constructor"]["root_binding"] == {
            "kind": "local",
            "symbol": "Batch",
        }
    else:
        # Class definition qualifications are applied at shared extraction, so
        # the lexical binding may remain a qualified constructor candidate.
        assert binding["kind"] in {"constructed-receiver", "unresolved"}
    (tmp_path / "app.py").write_text(source)
    inventory = PythonExtractor().extract(
        str(tmp_path), deep=True, source_files=["app.py"]
    )
    assert valid_python_constructor_facts(inventory["app.py"])
    observations = [
        row
        for row in resolve_call_observations(inventory)["observations"]
        if row["from"]["symbol"] == "run"
        and row["name"].rsplit(".", 1)[-1] == "cap"
        and row["line"] == call.lineno
    ]
    assert len(observations) == 1
    row = observations[0]
    edges = [
        row
        for row in resolve_call_edges(inventory)
        if row["from"]["symbol"] == "run"
        and row["name"].rsplit(".", 1)[-1] == "cap"
        and row["line"] == call.lineno
    ]
    if unique:
        assert row["kind"] == "internal"
        assert row["to"] == {"file": "app.py", "symbol": "Batch.cap"}
        assert len(edges) == 1 and edges[0]["to"] == row["to"]
    else:
        assert row["kind"] in {"unresolved", "ambiguous"}
        assert row.get("reason") and row.get("location")
        assert len(edges) == 1 and edges[0]["kind"] in {"unresolved", "ambiguous"}
        assert edges[0]["to"] != {"file": "app.py", "symbol": "Batch.cap"}


CLASS = "class Batch:\n    def cap(self, *args): return 'original'\n"


@pytest.mark.parametrize(
    "body,unique",
    [
        (
            "batch = Batch()\n    write = vars(batch).__setitem__\n    if condition:\n        write = lambda *args: None\n    write('cap', lambda: 'replacement')\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    namespace = vars(batch) if condition else {}\n    namespace[(namespace := {}) or 'cap'] = lambda: 'replacement'\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__ if condition else (lambda *args: None)\n    write('cap', (write := lambda *args: None))\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__\n    alias = write\n    alias('cap', lambda: 'replacement')\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__\n    alias = write if condition else write\n    alias('cap', lambda: 'replacement')\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__ if condition else (lambda *args: None)\n    write('cap', lambda: 'replacement')\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__\n    write('unrelated', 1)\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    write = vars(batch).update\n    write(unrelated=1)\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    write = vars(batch).__setitem__\n    write('cap', (write := lambda *args: None))\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    namespace = vars(batch)\n    namespace.__setitem__('cap', (namespace := {}))\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    namespace = vars(batch)\n    namespace['unrelated'] = 1\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    namespace = vars(batch)\n    for namespace['unrelated'] in (1,):\n        pass\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    for batch.unrelated in (1,):\n        pass\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    later = (vars(batch).__setitem__('cap', lambda: 'replacement') for _ in (0,))\n    return batch.cap()",
            True,
        ),
        (
            "batch = Batch()\n    eager = [vars(batch).__setitem__('cap', lambda: 'replacement') for _ in (0,)]\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    batch.cap += batch.cap()\n    return batch.cap()",
            False,
        ),
        (
            "batch = Batch()\n    namespace = vars(batch)\n    namespace['unrelated'] = 0\n    namespace['unrelated'] += (namespace := {}) and 1\n    return batch.cap()",
            True,
        ),
    ],
)
def test_captured_mutator_aliases_and_target_order_controls(tmp_path, body, unique):
    assert_dispatch(
        tmp_path, CLASS + "def run(condition=False):\n    " + body + "\n", unique
    )


@pytest.mark.parametrize(
    "header,unique",
    [
        (
            "    write = locals().__setitem__\n    alias = write\n    alias('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    write = locals().__setitem__\n    alias = write if flag else (lambda *args: None)\n    alias('cap', lambda self: 'replacement')\n",
            False,
        ),
        ("    eager = [locals().__setitem__('cap', None) for _ in (0,)]\n", True),
        ("    eager = [vars().__setitem__('cap', None) for _ in (0,)]\n", True),
        (
            "    global namespace\n    namespace = locals()\n    eager = [namespace.__setitem__('cap', None) for namespace in ({},)]\n",
            True,
        ),
        ("    write = locals().__setitem__\n    write('unrelated', 1)\n", True),
        (
            "    global namespace\n    namespace = locals()\n    eager = {namespace.__setitem__('cap', lambda self: 'replacement') for _ in (0,)}\n",
            False,
        ),
        (
            "    global namespace\n    namespace = locals()\n    eager = {str(_): namespace.__setitem__('cap', lambda self: 'replacement') for _ in (0,)}\n",
            False,
        ),
        (
            "    global namespace\n    namespace = locals()\n    later = (namespace.__setitem__('cap', lambda self: 'replacement') for _ in (0,))\n",
            True,
        ),
        (
            "    global namespace\n    namespace = locals()\n    eager = [namespace.__setitem__('unrelated', 1) for _ in (0,)]\n",
            True,
        ),
    ],
)
def test_class_mutator_alias_and_eager_deferred_comprehension_controls(
    tmp_path, header, unique
):
    assert_dispatch(
        tmp_path,
        "flag = False\n"
        + CLASS
        + header
        + "def run(condition=False): return Batch().cap()\n",
        unique,
    )


def test_augmented_attribute_store_captures_callee_before_store(tmp_path):
    source = (
        CLASS
        + "def run():\n    batch = Batch()\n    batch.cap += batch.cap()\n    return batch.cap()\n"
    )
    (tmp_path / "app.py").write_text(source)
    inventory = PythonExtractor().extract(
        str(tmp_path), deep=True, source_files=["app.py"]
    )
    observations = sorted(
        [
            row
            for row in resolve_call_observations(inventory)["observations"]
            if row["from"]["symbol"] == "run" and row["name"] == "batch.cap"
        ],
        key=lambda row: row["line"],
    )
    assert len(observations) == 2
    assert observations[0]["kind"] == "internal"
    assert observations[0]["to"] == {"file": "app.py", "symbol": "Batch.cap"}
    assert observations[1]["kind"] == "unresolved"


@pytest.mark.parametrize(
    "body,unique",
    [
        (
            "namespace = (vars(first) if condition else {}) if condition else {}\n    alias = namespace\n    write = alias.__setitem__\n    write('cap', lambda: 'replacement')",
            False,
        ),
        (
            "namespace = vars(original) if condition else {}\n    write = namespace.__setitem__\n    write('cap', (first := second))",
            False,
        ),
        (
            "namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    alias = write\n    alias('cap', lambda: 'replacement')",
            False,
        ),
        (
            "namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    write('cap', (namespace := vars(second)))",
            False,
        ),
        (
            "namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    write('cap', (write := lambda *args: None))",
            False,
        ),
        (
            "namespace = vars(first) if condition else {}\n    namespace.__setitem__('cap', (namespace := vars(second)))",
            False,
        ),
        (
            "(vars(first) if condition else {}).__setitem__('cap', (first := second))",
            False,
        ),
        (
            "write = (vars(first) if condition else {}).update\n    write(cap=lambda: 'replacement')",
            False,
        ),
        (
            "namespace = vars(first) if condition else {}\n    write = namespace.__setitem__\n    write('unrelated', 1)",
            True,
        ),
        ("(vars(first) if condition else {}).update(unrelated=1)", True),
        (
            "write = (vars(first) if condition else {}).update\n    write(unrelated=1)",
            True,
        ),
        (
            "namespace = vars(second) if condition else {}\n    write = namespace.__setitem__\n    write('cap', lambda: 'replacement')",
            True,
        ),
        (
            "namespace = {} if condition else {}\n    write = namespace.__setitem__\n    write('cap', lambda: 'replacement')",
            True,
        ),
        (
            "namespace = vars(first) if condition else {}\n    later = (namespace.__setitem__('cap', lambda: 'replacement') for _ in (0,))",
            True,
        ),
        (
            "namespace = vars(first) if condition else {}\n    eager = [namespace.__setitem__('cap', lambda: 'replacement') for _ in (0,)]",
            False,
        ),
    ],
)
def test_conditional_namespace_owners_survive_captured_and_direct_calls(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    original = first\n    second = Batch()\n    "
        + body
        + "\n    return original.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "body,unique",
    [
        (
            "eager = [namespace.__setitem__('cap', replacement) for namespace in ({},)]",
            True,
        ),
        (
            "eager = {namespace.__setitem__('cap', replacement) for namespace in ({},)}",
            True,
        ),
        (
            "eager = {str(index): namespace.__setitem__('cap', replacement) for namespace in ({},) for index in (0,)}",
            True,
        ),
        (
            "eager = [[namespace.__setitem__('cap', replacement) for namespace in ({},)] for _ in (0,)]",
            True,
        ),
        ("eager = [namespace.__setitem__('cap', replacement) for _ in (0,)]", False),
        (
            "eager = [namespace.__setitem__('cap', replacement) for namespace in ({},)]\n    namespace.__setitem__('cap', replacement)",
            False,
        ),
        (
            "later = (namespace.__setitem__('cap', replacement) for namespace in ({},))",
            True,
        ),
        (
            "later = (None for namespace in (namespace.__setitem__('cap', replacement) or ({},)))",
            False,
        ),
        ("eager = [None for first in (object(),)]", True),
        (
            "write = namespace.__setitem__\n    eager = [write('cap', replacement) for write in (lambda *args: None,)]",
            True,
        ),
        (
            "write = namespace.__setitem__\n    eager = [None for write in (lambda *args: None,)]\n    write('cap', replacement)",
            False,
        ),
        ("later = lambda namespace: namespace.__setitem__('cap', replacement)", True),
    ],
)
def test_comprehension_owner_names_are_lexical_and_outer_aliases_survive(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    namespace = vars(first) if condition else {}\n    replacement = lambda: 'replacement'\n    "
        + body
        + "\n    return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "body,unique",
    [
        ("getattr(namespace, '__setitem__')('cap', replacement)", False),
        ("(write := getattr(namespace, '__setitem__'))('cap', replacement)", False),
        (
            "write = getattr(namespace, '__setitem__') if condition else (lambda *args: None)\n    write('cap', replacement)",
            False,
        ),
        ("getattr(namespace if condition else {}, 'update')(cap=replacement)", False),
        (
            "getter = getattr\n    getter(namespace, '__setitem__')('cap', replacement)",
            False,
        ),
        (
            "getter = getattr if condition else (lambda *args: (lambda *args: None))\n    getter(namespace, '__setitem__')('cap', replacement)",
            False,
        ),
        (
            "getattr(namespace, '__setitem__', (namespace := {}))('cap', replacement)",
            False,
        ),
        (
            "getattr(namespace, (namespace := {}) or '__setitem__')('cap', replacement)",
            False,
        ),
        ("write = getattr(namespace, member)\n    write('cap', replacement)", False),
        ("write = getattr(namespace, '__setitem__')", True),
        ("write = getattr(namespace, member)", True),
        ("getattr(namespace, '__setitem__')('extra', 1)", True),
        ("getattr(namespace, 'get')('cap')", True),
        ("getattr(namespace, 'keys')()", True),
        (
            "getattr = lambda *args: (lambda *args: None)\n    getattr(namespace, '__setitem__')('cap', replacement)",
            True,
        ),
    ],
)
def test_literal_and_unknown_namespace_getter_results_capture_only_on_invocation(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda: 'replacement'\n    member = '__setitem__'\n    "
        + body
        + "\n    return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "header,unique",
    [
        (
            "    getattr(namespace, '__setitem__')('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    (write := getattr(namespace, '__setitem__'))('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    getter = getattr\n    write = getter(namespace, '__setitem__')\n    write('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    getter = getattr if flag else (lambda *args: (lambda *args: None))\n    getter(namespace, '__setitem__')('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    write = getattr(namespace, '__setitem__', (namespace := {}))\n    write('cap', lambda self: 'replacement')\n",
            False,
        ),
        ("    write = getattr(namespace, '__setitem__')\n", True),
        ("    getattr(namespace, '__setitem__')('extra', 1)\n", True),
        ("    getattr(namespace, 'get')('cap')\n", True),
        (
            "    write = getattr(namespace, member)\n    write('cap', lambda self: 'replacement')\n",
            False,
        ),
        ("    write = getattr(namespace, member)\n", True),
    ],
)
def test_class_namespace_getter_captures_literal_methods_without_a_result_cache(
    tmp_path, header, unique
):
    source = (
        "flag = False\nmember = '__setitem__'\n"
        + CLASS
        + "    namespace = locals()\n"
        + header
        + "def run(): return Batch().cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "prefix,getter",
    [
        ("import builtins as b\n", "b.getattr"),
        ("from builtins import getattr as retrieve\n", "retrieve"),
    ],
)
@pytest.mark.parametrize("class_scope", [False, True])
def test_explicit_builtin_getter_aliases_retain_namespace_receiver(
    tmp_path, prefix, getter, class_scope
):
    if class_scope:
        source = (
            prefix
            + CLASS
            + "    namespace = locals()\n    getter = "
            + getter
            + "\n    write = getter(namespace, '__setitem__')\n    write('cap', lambda self: 'replacement')\ndef run(): return Batch().cap()\n"
        )
    else:
        source = (
            prefix
            + CLASS
            + "def run():\n    first = Batch()\n    getter = "
            + getter
            + "\n    getter(vars(first), '__setitem__')('cap', lambda: 'replacement')\n    return first.cap()\n"
        )
    assert_dispatch(tmp_path, source, False)


@pytest.mark.parametrize(
    "body,unique",
    [
        ("dict.__setitem__(namespace, 'cap', replacement)", False),
        ("dict.__setitem__(namespace, 'extra', 1)", True),
        (
            "write = dict.update\n    alias = write\n    alias(namespace, cap=replacement)",
            False,
        ),
        ("(write := dict.update)(namespace, cap=replacement)", False),
        (
            "write = dict.update if condition else (lambda *args, **kwargs: None)\n    write(namespace, cap=replacement)",
            False,
        ),
        (
            "write = dict.update\n    write(namespace if condition else {}, cap=replacement)",
            False,
        ),
        (
            "write = dict.__setitem__\n    write(namespace, 'cap', (namespace := {}) or replacement)",
            False,
        ),
        (
            "write = dict.__setitem__\n    write(namespace, 'cap', (write := replacement))",
            False,
        ),
        ("getattr(dict, '__setitem__')(namespace, 'cap', replacement)", False),
        ("getattr(dict, 'update')(namespace, extra=1)", True),
        (
            "getter = getattr\n    write = getter(dict, 'update')\n    write(namespace, cap=replacement)",
            False,
        ),
        ("getattr(dict, member)(namespace, 'cap', replacement)", False),
        ("write = getattr(dict, member)", True),
        ("getattr(dict, 'get')(namespace, 'cap')", True),
        ("write = dict.update", True),
        ("dict.update({}, cap=replacement)", True),
    ],
)
def test_builtin_unbound_dict_mutators_capture_namespace_and_key_offset(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda: 'replacement'\n    member = '__setitem__'\n    "
        + body
        + "\n    return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "header,unique",
    [
        ("    dict.__setitem__(namespace, 'cap', lambda self: 'replacement')\n", False),
        ("    write = dict.update\n    write(namespace, extra=1)\n", True),
        (
            "    write = dict.__setitem__\n    write(namespace, 'cap', (namespace := {}) or (lambda self: 'replacement'))\n",
            False,
        ),
        (
            "    getattr(dict, 'update')(namespace, cap=lambda self: 'replacement')\n",
            False,
        ),
        (
            "    (write := getattr(dict, '__setitem__'))(namespace, 'cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    write = dict.update if flag else (lambda *args, **kwargs: None)\n    write(namespace, cap=lambda self: 'replacement')\n",
            False,
        ),
        ("    write = getattr(dict, member)\n", True),
    ],
)
def test_class_builtin_unbound_dict_mutator_invocation_preserves_owner(
    tmp_path, header, unique
):
    source = (
        "flag = False\nmember = '__setitem__'\n"
        + CLASS
        + "    namespace = locals()\n"
        + header
        + "def run(): return Batch().cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "body,unique",
    [
        (
            "write = getattr(namespace, '__setitem__')\n    write.__call__('cap', replacement)",
            False,
        ),
        (
            "write = getattr(namespace, '__setitem__')\n    alias = write.__call__\n    alias('cap', replacement)",
            False,
        ),
        ("getattr(namespace, '__setitem__').__call__('cap', replacement)", False),
        (
            "write = namespace.__setitem__ if condition else (lambda *args: None)\n    write.__call__('cap', replacement)",
            False,
        ),
        ("getattr(namespace, '__setitem__').__call__('extra', 1)", True),
        ("getattr.__call__(namespace, '__setitem__')('cap', replacement)", False),
        ("setattr.__call__(first, 'cap', replacement)", False),
        (
            "writer = setattr if condition else (lambda *args: None)\n    writer.__call__(first, 'cap', replacement)",
            False,
        ),
        (
            "factory = vars if condition else (lambda obj: {})\n    factory.__call__(first)['cap'] = replacement",
            False,
        ),
        (
            "factory = vars if condition else (lambda obj: {})\n    namespace = factory(first)\n    namespace['extra'] = 1",
            True,
        ),
        (
            "factory = lambda obj: {}\n    namespace = factory(first)\n    namespace['cap'] = replacement",
            True,
        ),
        (
            "def opaque(obj): return vars(obj)\n    namespace = opaque(first)\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "def opaque(obj): return vars(obj)\n    namespace = opaque(first)\n    write = namespace.__setitem__\n    write('cap', replacement)",
            False,
        ),
    ],
)
def test_registered_callable_wrappers_and_factory_scope_controls(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    namespace = vars(first)\n    replacement = lambda: 'replacement'\n    "
        + body
        + "\n    return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "header,unique",
    [
        (
            "    getter = getattr\n    getter.__call__(namespace, '__setitem__')('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    write = getattr(namespace, '__setitem__')\n    write.__call__('cap', lambda self: 'replacement')\n",
            False,
        ),
        (
            "    getattr(namespace, '__setitem__').__call__('cap', lambda self: 'replacement')\n",
            False,
        ),
        ("    getattr(namespace, '__setitem__').__call__('extra', 1)\n", True),
        (
            "    factory = locals if flag else (lambda: {})\n    factory.__call__()['cap'] = lambda self: 'replacement'\n",
            False,
        ),
    ],
)
def test_class_namespace_known_callable_wrapper_preserves_captured_owner(
    tmp_path, header, unique
):
    source = (
        "flag = True\n"
        + CLASS
        + "    namespace = locals()\n"
        + header
        + "def run(): return Batch().cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "prefix,body,unique",
    [
        (
            "write = dict.__setitem__\n",
            "write(vars(first), 'cap', lambda: 'replacement')",
            False,
        ),
        ("write = dict.__setitem__\n", "write(vars(first), 'extra', 1)", True),
        (
            "factory = lambda obj: {}\n",
            "namespace = factory(first)\n    namespace['cap'] = lambda: 'replacement'",
            True,
        ),
        (
            "getter = getattr\n",
            "getter(vars(first), '__setitem__')('cap', lambda: 'replacement')",
            False,
        ),
        (
            "write = dict.__setitem__ if flag else (lambda *args: None)\n",
            "write(vars(first), 'cap', lambda: 'replacement')",
            False,
        ),
        (
            "factory = vars if flag else (lambda obj: {})\n",
            "factory(first)['cap'] = lambda: 'replacement'",
            False,
        ),
    ],
)
def test_public_projection_sanitizes_module_helpers_without_erasing_inference(
    tmp_path, prefix, body, unique
):
    source = (
        "flag = True\n"
        + CLASS
        + prefix
        + "def run():\n    first = Batch()\n    "
        + body
        + "\n    return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)
    captured = analyze_python_bindings(ast.parse(source))
    private_keys = {
        "namespace",
        "method",
        "target",
        "target_members",
        "possible_helpers",
        "possible_namespace_mutators",
        "_possible_targets",
        "_allocation",
    }

    def inspect(value):
        if isinstance(value, dict):
            assert not private_keys.intersection(value)
            for nested in value.values():
                inspect(nested)
        elif isinstance(value, list):
            for nested in value:
                inspect(nested)

    inspect(captured.module)
    inspect(list(captured.calls.values()))


@pytest.mark.parametrize(
    "body,unique",
    [
        (
            "read = first.__getattribute__ if condition else (lambda member: {})\n    namespace = read('__dict__')\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "namespace = getattr(first, '__dict__')\n    write = namespace.__setitem__\n    write('cap', replacement)",
            False,
        ),
        ("getattr(first, '__dict__')['cap'] = replacement", False),
        ("getattr(first, '__dict__').update(cap=replacement)", False),
        (
            "namespace = getattr(first, '__dict__', (first := second))\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "read = object.__getattribute__\n    namespace = read(first, '__dict__')\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "read = first.__getattribute__\n    namespace = read('__dict__')\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "read = first.__getattribute__\n    namespace = read.__call__('__dict__')\n    namespace['cap'] = replacement",
            False,
        ),
        ("getattr.__call__(first, '__dict__')['cap'] = replacement", False),
        ("getattr(first, '__getattribute__')('__dict__')['cap'] = replacement", False),
        (
            "namespace = object.__getattribute__(first, (first := second) and '__dict__')\n    namespace['cap'] = replacement",
            False,
        ),
        (
            "namespace = getattr(second, '__dict__')\n    namespace['cap'] = replacement",
            True,
        ),
        (
            "namespace = first.__getattribute__('__dict__')\n    namespace['extra'] = 1",
            True,
        ),
        ("read = first.__getattribute__", True),
        (
            "getattr = lambda *args: {}\n    namespace = getattr(first, '__dict__')\n    namespace['cap'] = replacement",
            True,
        ),
    ],
)
def test_namespace_getters_capture_owner_before_arguments_and_keep_positive_controls(
    tmp_path, body, unique
):
    source = (
        CLASS
        + "def run(condition=False):\n    first = Batch()\n    original = first\n    second = Batch()\n    replacement = lambda: 'replacement'\n    "
        + body
        + "\n    return original.cap()\n"
    )
    assert_dispatch(tmp_path, source, unique)


@pytest.mark.parametrize(
    "prefix,getter",
    [
        ("import builtins as b\n", "b.getattr(first, '__dict__')"),
        ("from builtins import getattr as read\n", "read(first, '__dict__')"),
        (
            "from builtins import object as base\n",
            "base.__getattribute__(first, '__dict__')",
        ),
    ],
)
@pytest.mark.parametrize("class_scope", [False, True])
def test_builtin_namespace_getter_aliases_and_eager_class_effects(
    tmp_path, prefix, getter, class_scope
):
    if class_scope:
        source = (
            prefix
            + CLASS
            + "first = Batch()\nclass Holder:\n    namespace = "
            + getter
            + "\n    namespace.update(cap=lambda: 'replacement')\ndef run(): return first.cap()\n"
        )
    else:
        source = (
            prefix
            + CLASS
            + "def run():\n    first = Batch()\n    namespace = "
            + getter
            + "\n    namespace.update(cap=lambda: 'replacement')\n    return first.cap()\n"
        )
    assert_dispatch(tmp_path, source, False)


def test_eager_class_conditional_namespace_getter_retains_external_owners(tmp_path):
    source = (
        "flag = True\n"
        + CLASS
        + "first = Batch()\nsecond = Batch()\nclass Holder:\n    read = first.__getattribute__ if flag else second.__getattribute__\n    namespace = read('__dict__')\n    namespace['cap'] = lambda: 'replacement'\ndef run(): return first.cap()\n"
    )
    assert_dispatch(tmp_path, source, False)
