"""Known-equivalent and deliberately different syntax for real parser checks."""

from .model import Incomplete


PAIRS = {
    "python": [
        ("type", "list[tuple[int, str]]", "list[tuple[ int , str ]]", True),
        ("expr", "'a b'", "'ab'", False),
        ("expr", "{'value': 1}", "{'value': 2}", False),
        ("type", "tuple[int, str]", "tuple[str, int]", False),
    ],
    "typescript": [
        ("type", "(string | undefined)", "string|undefined", True),
        ("type", "{value?: string}", "{value: string | undefined}", False),
        (
            "type",
            "(x: string, y: number) => boolean",
            "(y: number, x: string) => boolean",
            False,
        ),
        ("expr", "'a b'", "'ab'", False),
        ("type", "Box<string>", "Box<number>", False),
        ("type", "x is string", "x is number", False),
    ],
    "go": [
        ("type", "map[string] (int)", "map[string]int", True),
        ("type", "func(string, int) bool", "func(int, string) bool", False),
        (
            "type",
            'struct { Value string `json:"a b"` }',
            'struct { Value string `json:"ab"` }',
            False,
        ),
        ("type", "[]int", "[1]int", False),
    ],
    "rust": [
        ("type", "Vec < (u8) >", "Vec<u8>", True),
        ("type", "&mut String", "&String", False),
        ("type", "fn(i32, bool) -> u8", "fn(bool, i32) -> u8", False),
        ("expr", '"a b"', '"ab"', False),
    ],
    "haskell": [
        ("type", "(a -> b) -> c", "a -> (b -> c)", False),
        ("type", "a -> (b -> c)", "a -> b -> c", True),
        ("type", "(Eq a) => a -> a", "Eq a => a -> a", True),
        ("type", '("a b", a)', '("ab", a)', False),
        ("type", "Either a b", "Either b a", False),
    ],
}

SOURCES = {
    "python": "class Box:\n    item: str\n    def run(self, value: int=3, *, flag: bool=False) -> str:\n        return 'no execution'\n",
    "typescript": "export interface Box { item?: string; run(value: number): string; }",
    "go": 'package p\ntype Box struct { Item string }\nfunc (b *Box) Run(value int) string { panic("not executed") }',
    "rust": 'pub struct Box { item: String }\nimpl Box { pub fn run(&self, value: i32) -> String { panic!("not executed") } }',
    "haskell": "module Probe where\ndata Box a = Box a\nrun :: Box a -> a\nrun (Box a) = a\n",
}


def self_test(frontends, languages=None) -> dict:
    results = []
    for lang in languages or PAIRS:
        if lang not in PAIRS:
            raise Incomplete(f"Unknown required frontend {lang}")
        for index, (mode, left, right, equal) in enumerate(PAIRS[lang]):
            values = frontends.batch(
                lang, [{"mode": mode, "text": text} for text in (left, right)]
            )
            if (values[0] == values[1]) is not equal:
                raise Incomplete(
                    f"{lang} semantic control {index} failed: expected equal={equal}"
                )
            results.append(
                {
                    "language": lang,
                    "case": index,
                    "expected_equal": equal,
                    "status": "pass",
                }
            )
        observed = frontends.batch(
            lang,
            [
                {
                    "mode": "source",
                    "text": SOURCES[lang],
                    "filename": "Probe.hs" if lang == "haskell" else "probe.ts",
                }
            ],
        )[0]
        names = [item["name"] for item in observed["declarations"]]
        if "Box" not in names or not any(n.lower() == "run" for n in names):
            raise Incomplete(f"{lang} source observer returned incomplete declarations")
    return {"status": "pass", "controls": results, "frontends": frontends.identities}
