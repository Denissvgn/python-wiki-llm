"""Complete rendered-output accounting with independent token recounts."""

import io
import json
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import context_budget
from llm_wiki_cli.services.context_budget import build_budgeted_context
from llm_wiki_cli.services.context_packet import (
    validate_context_packet,
    _encode_packet_payload,
)
from llm_wiki_cli.services.token_counting import EstimatedCounter, LocalTokenizerCounter
from tests.test_context_packet_knowledge import _materialize_ready_project


def test_refusal_recovery_is_bound_and_identical_through_api_cli_and_mcp(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService

    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("class Example:\n    pass\n")
    request = {"protocol": "llm-wiki-context/v3", "budget_tokens": 1, "budget_mode": "estimated", "format": "packet",
               "knowledge_mode": "off", "changes": {"mode": "paths", "paths": []}}
    result = api.build_budgeted_context(request=request)
    assert not result.ok and result.rendered == "" and result.error == "cannot-fit"
    diagnostics = result.diagnostics
    assert diagnostics is not None
    assert diagnostics["request_id"] == context_budget.request_identity(request)
    assert diagnostics["emitted_context_bytes"] == 0
    assert diagnostics["accounting_meaning"] == "rejected-candidate-not-emitted-context-or-global-minimum"
    assert [item["id"] for item in diagnostics["recovery"]] == ["scoped-evidence", "explicit-larger-budget"]
    assert all(not item["automatic"] for item in diagnostics["recovery"])
    assert len(json.dumps(diagnostics).encode()) < 4096
    assert "class Example" not in json.dumps(diagnostics)

    request_file = tmp_path / "request.json"
    request_file.write_text(json.dumps(request))
    output = tmp_path / "should-not-exist.txt"
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "context", "--request", str(request_file), "--output", str(output)])
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 3 and not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["diagnostics"] == diagnostics

    service = McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")
    with pytest.raises(McpWikiError) as unavailable:
        service.build_budgeted_context(request)
    assert unavailable.value.code == "cannot-fit"
    assert unavailable.value.data is not None
    assert unavailable.value.data["diagnostics"] == diagnostics


def test_generated_broad_guidance_keeps_both_explicit_recovery_routes():
    from llm_wiki_cli.services import schema

    full = schema._wiki_instructions("docs/llm_wiki", ".agents/skills")
    compact = schema._compact_wiki_instructions("docs/llm_wiki", ".agents/skills")
    for text in (full, compact):
        assert "cannot-fit" in text and "global minimum" in text
        assert "scoped task/query" in text
        assert "explicitly authorize a larger complete-output budget" in " ".join(text.split())


class ByteCounter:
    identity = "utf8-bytes/v1"
    exact = True

    def count(self, text):
        return len(text.encode("utf-8"))


@pytest.mark.parametrize("fmt", ["json", "markdown", "packet"])
@pytest.mark.parametrize("output_file", [False, True])
def test_cli_emits_the_counted_utf8_bytes_with_windows_stdout(
    tmp_path, monkeypatch, fmt, output_file
):
    source = tmp_path / "project"
    source.mkdir()
    monkeypatch.chdir(source)
    (source / "app.py").write_bytes(
        '"""Café 雪."""\ndef greet_雪():\n    return "hello"\n'.encode("utf-8")
    )
    counter = ByteCounter()
    request = {
        "budget_tokens": 32000, "format": fmt, "focus": ["all"],
        "knowledge_mode": "off", "budget_mode": "exact",
    }
    expected = api.build_budgeted_context(request=request, counter=counter)
    assert expected.ok
    assert "greet_雪" in expected.rendered
    monkeypatch.setattr(context_budget, "LocalTokenizerCounter", lambda path: counter)
    command = [
        "context", "--format", fmt, "--focus", "all", "--budget", "32000",
        "--budget-mode", "exact", "--tokenizer", "configured-counter.json",
    ]
    output_path = tmp_path / "context-output.txt"
    if output_file:
        command += ["--output", str(output_path)]
    buffer = io.BytesIO()
    with io.TextIOWrapper(
        buffer, encoding="cp1252", errors="backslashreplace", newline="\r\n"
    ) as stream, monkeypatch.context() as patch:
        patch.setattr(sys, "stdout", stream)
        patch.setattr(sys, "argv", ["llm-wiki", *command])
        cli.main()
        stream.flush()
        stdout = buffer.getvalue()

    actual = output_path.read_bytes() if output_file else stdout
    assert actual == expected.rendered.encode("utf-8")
    assert len(actual) <= expected.accounting["used_tokens"] <= 32000
    if output_file:
        assert stdout == b""


def test_optional_tokenizer_absence_keeps_estimates_and_actionable_exact_error(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "tokenizers", None)
    assert EstimatedCounter().count("hello") == 2
    with pytest.raises(ValueError, match=r"agent-wiki-cli\[tokens\]"):
        LocalTokenizerCounter(tmp_path / "unused.json")


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


@pytest.mark.parametrize("counter", [EstimatedCounter(), ByteCounter()])
def test_packet_budget_fits_before_applying_wire_item_limit(tmp_path, monkeypatch, counter):
    """Large internal candidates are not deliverable packets until fitted."""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "dense.py"
    source.write_text("def dense():\n" + "    record(1, 2, 3, 4)\n" * 1000)
    original = source.read_bytes()
    monkeypatch.setattr(context_budget.packets, "_MAX_JSON_ITEMS", 5000)
    with pytest.raises(context_budget.packets.ContextPacketMalformedError,
                       match="5000-item limit"):
        context_budget.packets.build_qualified_context(request={
            "budget_tokens": 1_000_000, "focus": ["all"],
            "knowledge_mode": "off",
        })
    request = {
        "budget_tokens": 8000, "budget_mode": "estimated",
        "format": "packet", "focus": ["all"], "knowledge_mode": "off",
    }
    result = build_budgeted_context(request=request, counter=counter)
    assert result.ok
    validated = context_budget.validate_budgeted_context(
        result.rendered, request, counter=counter
    )
    assert validated["packet"]["response"]["truncated"]
    assert result.accounting["used_tokens"] <= 8000
    assert source.read_bytes() == original


def test_fitted_packet_still_requires_valid_packet_identity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("def app():\n    return 1\n")
    monkeypatch.setattr(context_budget.packets, "_packet_id", lambda body: "0" * 64)
    with pytest.raises(context_budget.packets.ContextPacketError):
        build_budgeted_context(request={
            "budget_tokens": 8000, "budget_mode": "estimated", "format": "packet",
        })


@pytest.mark.parametrize("fmt", ["json", "packet"])
def test_estimator_shortcut_preserves_full_render_selection(tmp_path, monkeypatch, fmt):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "雪.py").write_text(
        "def dense():\n" + "    record('雪', 2, 3, 4)\n" * 1000, encoding="utf-8"
    )
    request = {
        "budget_tokens": 8000, "budget_mode": "estimated", "format": fmt,
        "focus": ["all"], "knowledge_mode": "off",
    }
    calls = []
    render = context_budget.context._protocol_success_payload

    def counted(*args, **kwargs):
        calls.append(1)
        return render(*args, **kwargs)

    monkeypatch.setattr(context_budget.context, "_protocol_success_payload", counted)
    optimized = build_budgeted_context(request=request, counter=EstimatedCounter())
    optimized_calls = len(calls)
    calls.clear()

    class EquivalentCustomCounter(EstimatedCounter):
        pass

    reference = build_budgeted_context(request=request, counter=EquivalentCustomCounter())
    assert optimized.ok and reference.ok
    assert optimized.rendered == reference.rendered
    assert optimized.accounting == reference.accounting
    assert optimized_calls < len(calls)


def test_custom_counter_does_not_assume_monotonic_utf8_size(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dense.py").write_text(
        "def dense():\n" + "    record(1, 2, 3, 4)\n" * 1000
    )

    class NonMonotonicCounter:
        identity = "adversarial-trusted-counter/v1"
        exact = True

        def count(self, text):
            return 1 if '"calls"' in text else 100_000

    request = {
        "budget_tokens": 8000, "budget_mode": "exact", "format": "packet",
        "focus": ["all"], "knowledge_mode": "off",
    }
    result = build_budgeted_context(request=request, counter=NonMonotonicCounter())
    assert result.ok and result.accounting["exact_compliance"]
    payload = context_budget.validate_budgeted_context(
        result.rendered, request, counter=NonMonotonicCounter()
    )
    assert payload["packet"]["response"]["files"]["dense.py"]["detail"] == "deep"


def test_fitted_packet_retains_captured_native_file_identity_guard(tmp_path, monkeypatch):
    tree, _ = _materialize_ready_project(tmp_path, monkeypatch)
    target = tree["wiki_root"] / ".llm-wiki-knowledge.json"
    original = target.read_bytes()
    capture = context_budget.packets.capture_context_read

    def capture_with_integrity(*args, **kwargs):
        return capture(*args, **kwargs, respect_ignores=True)

    monkeypatch.setattr(context_budget.packets, "capture_context_read", capture_with_integrity)

    class ReplacingCounter(ByteCounter):
        replaced = False

        def count(self, text):
            if not self.replaced:
                target.write_bytes(original)
                self.replaced = True
            return super().count(text)

    with pytest.raises(context_budget.packets.ContextPacketSourceMutationError) as caught:
        build_budgeted_context(".", str(tree["wiki_root"]), {
            "budget_tokens": 300_000, "budget_mode": "exact", "format": "packet",
            "knowledge_mode": "auto",
        }, counter=ReplacingCounter())
    assert caught.value.facet == "wiki"
    assert target.read_bytes() == original
