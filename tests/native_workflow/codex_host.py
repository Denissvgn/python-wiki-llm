"""Bounded, tool-mediated calls to an explicitly selected local Codex host.

The coding model returns one structured action. A separately admitted controller
must own file/provider/oracle operations and observations; native Codex tools are
disabled and any unexpected native action invalidates the call. This bridge does
not implement that controller or establish general target-execution admission.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time

from tests.provider_conformance.model import canonical_json
from tests.native_workflow.run_trace import AttemptTrace, identity

MAX_OUTPUT_BYTES = 2_097_152
_NATIVE_WINDOWS = os.name == 'nt'
_CI_MARKERS = ('CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'TF_BUILD', 'BUILDKITE', 'JENKINS_URL')
DISABLED_FEATURES = ('shell_tool', 'unified_exec', 'shell_snapshot', 'apps', 'plugins', 'hooks',
                     'multi_agent', 'browser_use', 'browser_use_external', 'computer_use',
                     'image_generation', 'code_mode_host', 'workspace_dependencies', 'memories', 'goals', 'tool_suggest')
_STARTUP_NOTICE = ('Code Mode is unavailable because code-mode host is disabled. '
                   'Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.')


class HostError(ValueError):
    """The configured host did not deliver the required bounded observation."""

    def __init__(self, message, *, observation=None):
        self.observation = observation
        super().__init__(message)


class HostCancelled(HostError):
    """A requested cancellation prevented the host process from launching."""


@dataclass(frozen=True)
class ProcessObservation:
    returncode: int
    stdout: bytes
    stderr: bytes
    elapsed_ns: int
    disposition: str


def binary_hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1_048_576), b''):
            result.update(block)
    return 'sha256:' + result.hexdigest()


def run_bounded(argv: list[str], *, cwd: Path, input_bytes: bytes, timeout: float,
                cancelled=None, max_output: int = MAX_OUTPUT_BYTES) -> ProcessObservation:
    """Bound retained output and terminate the owned process group on failure."""
    if (type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 600
            or type(max_output) is not int or not 0 < max_output <= MAX_OUTPUT_BYTES
            or not isinstance(input_bytes, bytes) or len(input_bytes) > MAX_OUTPUT_BYTES):
        raise HostError('Invalid process byte/time budget')
    if cancelled is not None and cancelled():
        raise HostCancelled('Process cancelled before launch')
    started = time.monotonic_ns()
    overflow = threading.Event()
    buffers = [bytearray(), bytearray()]
    environment = {k: v for k, v in os.environ.items() if k not in {'PYTHONPATH', 'PYTHONHOME'}}
    environment.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryFile() as input_file:
        input_file.write(input_bytes)
        input_file.seek(0)
        process = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=input_file,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=os.name != 'nt')

        def collect(stream, buffer):
            try:
                for chunk in iter(lambda: stream.read(4096), b''):
                    room = max_output - len(buffer)
                    buffer.extend(chunk[:room])
                    if len(chunk) > room:
                        overflow.set()
                        break
            finally:
                stream.close()

        readers = [threading.Thread(target=collect, args=(stream, buffer), daemon=True)
                   for stream, buffer in zip((process.stdout, process.stderr), buffers)]
        for reader in readers:
            reader.start()
        disposition = 'completed'
        cleanup_error = None
        interrupted = False
        try:
            while process.poll() is None:
                if overflow.is_set():
                    disposition = 'output-limit'
                    break
                if cancelled is not None and cancelled():
                    disposition = 'cancelled'
                    break
                if (time.monotonic_ns() - started) / 1e9 >= timeout:
                    disposition = 'timed-out'
                    break
                time.sleep(0.01)
        except KeyboardInterrupt:
            interrupted = True
            disposition = 'cancelled'
        finally:
            if process.poll() is None:
                if os.name == 'nt':
                    process.kill()
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except PermissionError as error:
                        # Best-effort root cleanup is not evidence that group
                        # containment works. Refuse this host after reaping it.
                        cleanup_error = error
                        process.kill()
                process.wait(timeout=5)
            for reader in readers:
                reader.join(timeout=0.1)
            # Also catch descendants that have closed both output pipes. This
            # is process-group cleanup, not containment of an untrusted target:
            # a process that creates another session requires a stronger host.
            if os.name != 'nt':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError as error:
                    cleanup_error = error
                else:
                    if disposition == 'completed':
                        disposition = 'descendants-terminated'
            for reader in readers:
                reader.join(timeout=5)
            partial = ProcessObservation(process.returncode, bytes(buffers[0]), bytes(buffers[1]),
                                         time.monotonic_ns() - started, 'cleanup-failed')
            if any(reader.is_alive() for reader in readers):
                raise HostError('Process output did not close during cleanup', observation=partial)
            if cleanup_error is not None:
                raise HostError('Process-group cleanup is unavailable in this execution environment',
                                observation=partial) from cleanup_error
        if overflow.is_set():
            disposition = 'output-limit'
    observation = ProcessObservation(process.returncode, bytes(buffers[0]), bytes(buffers[1]),
                                     time.monotonic_ns() - started, disposition)
    if interrupted:
        raise HostCancelled('Host process interrupted', observation=observation)
    return observation


def parse_response(observation: ProcessObservation) -> dict:
    """Accept a single completed, tool-free host turn; preserve usage qualifications."""
    try:
        return _parse_response(observation)
    except (ValueError, TypeError, AttributeError, UnicodeError) as error:
        raise HostError(str(error), observation=observation) from error


def _parse_response(observation: ProcessObservation) -> dict:
    if len(observation.stdout) > MAX_OUTPUT_BYTES or len(observation.stderr) > MAX_OUTPUT_BYTES:
        raise HostError('Host output exceeds its byte bound')
    if observation.disposition != 'completed' or observation.returncode != 0:
        raise HostError('Codex host call failed: ' + observation.disposition)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise HostError('Duplicate host JSON field')
            result[key] = value
        return result

    events = []
    for line in observation.stdout.splitlines():
        if len(line) > MAX_OUTPUT_BYTES:
            raise HostError('Host event exceeds its byte bound')
        event = json.loads(line, object_pairs_hook=unique)
        if not isinstance(event, dict):
            raise HostError('Host event must be an object')
        canonical_json(event)
        events.append(event)
    started, completed, threads, messages, diagnostics = 0, [], [], [], []
    for event in events:
        kind = event.get('type')
        if completed:
            raise HostError('Host events follow the completed turn')
        if kind == 'thread.started':
            if threads or started:
                raise HostError('Host thread event is out of order')
            threads.append(event.get('thread_id'))
        elif kind == 'turn.started':
            if len(threads) != 1 or started:
                raise HostError('Host turn event is out of order')
            started += 1
        elif kind == 'turn.completed':
            if not started:
                raise HostError('Host completion lacks a started turn')
            completed.append(event)
        elif kind in {'error', 'turn.failed'}:
            raise HostError('Host reported a failed turn')
        elif kind in {'item.started', 'item.updated', 'item.completed'}:
            item = event.get('item', {})
            item_type = item.get('type')
            if item_type == 'error' and not started and item.get('message') == _STARTUP_NOTICE:
                diagnostics.append(item['message'])
            elif item_type not in {'agent_message', 'reasoning'}:
                raise HostError('Unexpected native tool or diagnostic in mediated host call')
            elif not started:
                raise HostError('Host content precedes the turn')
            elif item_type == 'agent_message' and kind == 'item.completed':
                messages.append(item.get('text'))
        else:
            raise HostError('Unknown host event')
    if (len(threads) != 1 or not isinstance(threads[0], str) or not threads[0]
            or started != 1 or len(completed) != 1 or len(messages) != 1 or not isinstance(messages[0], str)):
        raise HostError('Host turn is incomplete or ambiguous')
    usage = completed[0].get('usage')
    if (not isinstance(usage, dict) or not {'input_tokens', 'output_tokens'} <= usage.keys()
            or any(type(v) is not int or v < 0 for v in usage.values())):
        raise HostError('Host did not report usable token accounting')
    action = json.loads(messages[-1], object_pairs_hook=unique)
    if not isinstance(action, dict):
        raise HostError('Host final answer must be a structured action')
    canonical_json(action)
    return {'action': action, 'usage': usage, 'thread_id': threads[0], 'diagnostics': diagnostics,
            'scope': 'one observed Codex host invocation; internal provider retries/framing are not independently observed'}


@dataclass(frozen=True)
class CodexHost:
    executable: Path
    executable_sha256: str
    version: str
    model: str
    reasoning_effort: str
    service_tier: str = 'default'

    def configuration(self) -> dict:
        return {'adapter': 'native-workflow-codex-host/v1', 'executable': str(self.executable),
                'executable_sha256': self.executable_sha256, 'version': self.version,
                'model': self.model, 'reasoning_effort': self.reasoning_effort, 'service_tier': self.service_tier,
                'disabled_features': list(DISABLED_FEATURES), 'mode': 'ephemeral-tool-free',
                'filesystem': 'minimal-runtime-and-read-only-control-directory', 'network': 'disabled-for-tools',
                'scope': 'host-invocation; provider-internal-retries-and-framing-unobserved'}

    def command(self, workspace: Path, schema_path: Path) -> list[str]:
        policy = '{filesystem={":minimal"="read",":workspace_roots"={"."="read",".codex"="deny",".agents"="deny"}},network={enabled=false}}'
        command = [str(self.executable), 'exec', '--ignore-user-config', '--ephemeral', '--json', '--strict-config',
            '--model', self.model, '-c', 'model_reasoning_effort=' + json.dumps(self.reasoning_effort),
            '-c', 'service_tier=' + json.dumps(self.service_tier), '-c', 'approval_policy="never"',
            '-c', 'default_permissions="native-model"', '-c', 'permissions.native-model=' + policy,
            '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
            '-c', 'shell_environment_policy.inherit="none"', '--skip-git-repo-check',
            '-C', str(workspace), '--output-schema', str(schema_path)]
        for feature in DISABLED_FEATURES:
            command.extend(['--disable', feature])
        return [*command, '-']

    def call(self, prompt: str, schema: dict, *, workspace: Path, timeout: float, cancelled=None):
        if any(os.environ.get(name) for name in _CI_MARKERS):
            raise HostError('Live agent evaluation is local-only and cannot run in CI')
        if _NATIVE_WINDOWS:
            raise HostError('Live host execution is not qualified on native Windows')
        if cancelled is not None and cancelled():
            raise HostCancelled('Host call cancelled before preparation')
        prompt_raw = prompt.encode('utf-8')
        schema_raw = canonical_json(schema)
        if (len(prompt_raw) > MAX_OUTPUT_BYTES or len(schema_raw) > MAX_OUTPUT_BYTES
                or not isinstance(schema, dict) or type(timeout) not in (int, float)
                or not math.isfinite(timeout) or not 0 < timeout <= 600):
            raise HostError('Invalid host input or time budget')
        if binary_hash(self.executable) != self.executable_sha256:
            raise HostError('Selected host binary changed since admission')
        # This directory contains only the output schema. Source, oracle and
        # evidence roots are neither mounted here nor exposed to native tools.
        workspace.mkdir(mode=0o700, parents=True, exist_ok=False)
        schema_path = workspace / 'output-schema.json'
        schema_path.write_bytes(schema_raw)
        observation = run_bounded(self.command(workspace, schema_path), cwd=workspace,
                                  input_bytes=prompt_raw, timeout=timeout, cancelled=cancelled)
        try:
            if binary_hash(self.executable) != self.executable_sha256:
                raise HostError('Selected host binary changed during the call')
            if (workspace.is_symlink() or set(workspace.iterdir()) != {schema_path}
                    or schema_path.is_symlink() or schema_path.read_bytes() != schema_raw):
                raise HostError('Read-only model control directory changed during the call')
        except (OSError, HostError) as error:
            raise HostError(str(error), observation=observation) from error
        return observation


def trace_call(trace: AttemptTrace, host: CodexHost, prompt: str, schema: dict, *, call_id: str,
               workspace: Path, timeout: float, cancelled=None) -> dict:
    """Record an actual invocation boundary, including unsuccessful observations.

    The caller supplies admission; retaining its reference does not verify it.
    This does not count hidden model framing or infer target reads from output.
    """
    settings = canonical_json(host.configuration())
    if (trace.manifest['execution_kind'] != 'external-host' or trace.manifest['model'] != host.model
            or trace.manifest['settings'] != identity(settings)):
        raise HostError('Trace does not bind the selected host configuration')
    trace.blob(settings)
    prompt_raw = prompt.encode('utf-8')
    trace.record('context', {'context_id': call_id, 'blob': trace.blob(prompt_raw),
                            'counter_id': 'utf8-bytes-upper-bound/v1', 'counter_mode': 'estimated',
                            'canonical_tokens': len(prompt_raw), 'host_framing_tokens': None})
    request = canonical_json({'prompt': prompt, 'schema': schema,
                              'argv': host.command(workspace, workspace / 'output-schema.json'), 'timeout': timeout})
    trace.record('model-start', {'call_id': call_id, 'request': trace.blob(request), 'context_ids': [call_id]})
    observation = None
    error_record = None
    parsed = None
    outcome = 'integration-failed'
    try:
        observation = host.call(prompt, schema, workspace=workspace, timeout=timeout, cancelled=cancelled)
        parsed = parse_response(observation)
        outcome = 'passed'
        return parsed
    except BaseException as error:
        if isinstance(error, HostError):
            observation = error.observation or observation
        error_record = {'exception_type': type(error).__name__, 'message': str(error)}
        if isinstance(error, (KeyboardInterrupt, HostCancelled)) or observation is not None and observation.disposition == 'cancelled':
            outcome = 'cancelled'
        elif observation is not None and observation.disposition == 'timed-out':
            outcome = 'timed-out'
        raise
    finally:
        receipt = {'scope': host.configuration()['scope'], 'error': error_record,
                   'host_process': None if observation is None else {
                       'returncode': observation.returncode, 'elapsed_ns': observation.elapsed_ns,
                       'disposition': observation.disposition, 'stdout': trace.blob(observation.stdout),
                       'stderr': trace.blob(observation.stderr)}}
        trace.record('model-end', {'call_id': call_id,
            'response': trace.blob(canonical_json(parsed['action'])) if parsed is not None else None,
            'receipt': trace.blob(canonical_json(receipt)), 'outcome': outcome,
            'input_tokens': parsed['usage']['input_tokens'] if parsed is not None else None,
            'output_tokens': parsed['usage']['output_tokens'] if parsed is not None else None})
