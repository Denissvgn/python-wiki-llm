"""Complete rendered-output accounting with independent token recounts."""

import json
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.context_budget import build_budgeted_context
from llm_wiki_cli.services.context_packet import (
    validate_context_packet,
    _encode_packet_payload,
)
from llm_wiki_cli.services.token_counting import EstimatedCounter, LocalTokenizerCounter
from tests.test_context_packet_knowledge import _materialize_ready_project


class ByteCounter:
    identity = "utf8-bytes/v1"
    exact = True

    def count(self, text):
        return len(text.encode("utf-8"))


@pytest.mark.parametrize("fmt", ["json", "markdown", "packet"])
@pytest.mark.parametrize("mode", ["off", "auto", "required"])
def test_complete_render_and_minimum_envelope(tmp_path, monkeypatch, fmt, mode):
    tree, _ = _materialize_ready_project(tmp_path, monkeypatch)
    request = {
        "budget_tokens": 300_000,
        "focus": ["all"],
        "format": fmt,
        "knowledge_mode": mode,
        "budget_mode": "exact",
    }
    counter = ByteCounter()
    full = api.build_budgeted_context(
        ".", str(tree["wiki_root"]), request, counter=counter
    )
    assert full.ok
    assert (
        len(full.rendered.encode("utf-8")) <= full.accounting["used_tokens"] <= 300_000
    )
    assert full.accounting["exact_compliance"]
    if fmt == "packet":
        validate_context_packet(
            _encode_packet_payload(json.loads(full.rendered)["packet"])
        )
    # Budget pressure can reduce entries, but the complete result is recounted.
    reduced = build_budgeted_context(
        ".",
        str(tree["wiki_root"]),
        {**request, "budget_tokens": full.accounting["used_tokens"] - 200},
        counter=counter,
    )
    if reduced.ok:
        assert counter.count(reduced.rendered) <= reduced.accounting["used_tokens"]
        assert reduced.accounting["used_tokens"] <= full.accounting["used_tokens"] - 200
    else:
        assert reduced.error == "cannot-fit"
    tiny = build_budgeted_context(
        ".", str(tree["wiki_root"]), {**request, "budget_tokens": 1}, counter=counter
    )
    assert not tiny.ok and tiny.error == "cannot-fit" and tiny.rendered == ""
    assert not tiny.accounting["exact_compliance"]


@pytest.mark.parametrize("fmt", ["json", "markdown", "packet"])
def test_local_tokenizer_independent_recount(tmp_path, monkeypatch, fmt):
    tokenizers = pytest.importorskip("tokenizers")
    tokenizer = tokenizers.Tokenizer(tokenizers.models.BPE(unk_token="[UNK]"))
    tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.ByteLevel(
        add_prefix_space=False
    )
    tokenizer.train_from_iterator(
        [
            'def плотный_код(long_identifier_name): return {"ключ": [1, 2, 3]}',
            "json nested envelope token budget accounting class function metadata "
            * 20,
        ],
        tokenizers.trainers.BpeTrainer(
            vocab_size=300,
            special_tokens=["[UNK]"],
            initial_alphabet=tokenizers.pre_tokenizers.ByteLevel.alphabet(),
        ),
    )
    path = tmp_path / "tokenizer.json"
    tokenizer.save(str(path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text(
        'def плотный_код(long_identifier_name):\n    return {"ключ": [1, 2, 3]}\n',
        encoding="utf-8",
    )
    counter = LocalTokenizerCounter(path)
    result = build_budgeted_context(
        request={"budget_tokens": 10_000, "format": fmt}, counter=counter
    )
    assert result.ok
    independent = tokenizers.Tokenizer.from_file(str(path))
    assert (
        len(independent.encode(result.rendered, add_special_tokens=False).ids)
        <= result.accounting["used_tokens"]
        <= 10_000
    )
    assert ":sha256:" in result.accounting["counter_id"]


def test_explicit_estimates_and_counter_pinning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="requires an explicit"):
        build_budgeted_context(request={"budget_tokens": 10000})
    with pytest.raises(ValueError, match="estimated counter"):
        build_budgeted_context(
            request={"budget_tokens": 10000}, counter=EstimatedCounter()
        )
    with pytest.raises(ValueError, match="counter_id"):
        build_budgeted_context(
            request={"budget_tokens": 10000, "counter_id": "wrong"},
            counter=ByteCounter(),
        )
    result = build_budgeted_context(
        request={"budget_tokens": 10000, "budget_mode": "estimated"}
    )
    assert result.ok and not result.accounting["exact_compliance"]
    exact_backend = build_budgeted_context(
        request={"budget_tokens": 10000, "budget_mode": "estimated"},
        counter=ByteCounter(),
    )
    assert exact_backend.ok and not exact_backend.accounting["exact_compliance"]
    assert exact_backend.accounting["mode"] == "estimated"


def test_cli_v3_and_cannot_fit(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "context", "--budget", "10000", "--budget-mode", "estimated"],
    )
    cli.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["protocol"] == "llm-wiki-context/v3"
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "protocol": "llm-wiki-context/v3",
                "budget_tokens": 1,
                "budget_mode": "estimated",
            }
        )
    )
    with pytest.raises(SystemExit) as exc:
        monkeypatch.setattr(
            sys, "argv", ["llm-wiki", "context", "--request", str(request)]
        )
        cli.main()
    assert exc.value.code == 3
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["error"] == "cannot-fit"
