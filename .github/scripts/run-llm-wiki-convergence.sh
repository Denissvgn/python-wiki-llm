#!/usr/bin/env bash

set -uo pipefail

readonly RESULT_SCHEMA="llm-wiki-convergence/v1"
readonly SUMMARY_MAX_LINES=40
readonly SUMMARY_MAX_BYTES=8192
readonly STATUS_SUMMARY_LIMIT=20

usage() {
  cat <<'EOF'
Usage:
  run-llm-wiki-convergence.sh \
    --python PATH \
    --src-dir PATH \
    --wiki-dir PATH \
    --helper-cache-dir PATH \
    --evidence-dir PATH \
    --github-output PATH \
    --jobs 1

Runs one normal, plugin-disabled wiki sync in the current repository and
records complete pre/post wiki status plus full-worktree safety evidence.
EOF
}

die() {
  printf 'run-llm-wiki-convergence: %s\n' "$*" >&2
  exit 2
}

require_value() {
  local option="$1"
  local remaining="$2"
  ((remaining >= 2)) || die "${option} requires a value"
}

reject_multiline() {
  local value="$1"
  local label="$2"
  [[ "${value}" != *$'\n'* && "${value}" != *$'\r'* ]] ||
    die "${label} must not contain a newline"
}

status_count() {
  local path="$1"
  local count
  count="$(wc -l < "${path}")" || return 1
  count="${count//[[:space:]]/}"
  [[ "${count}" =~ ^[0-9]+$ ]] || return 1
  printf '%s' "${count}"
}

capture_scoped_status() {
  local destination="$1"
  LC_ALL=C git -c core.quotePath=true status \
    --porcelain=v1 \
    --untracked-files=all \
    --ignore-submodules=none \
    -- "${wiki_dir}" > "${destination}"
}

capture_worktree_status() {
  local destination="$1"
  LC_ALL=C git -c core.quotePath=true status \
    --porcelain=v1 \
    --untracked-files=all \
    --ignore-submodules=none > "${destination}"
}

capture_wiki_diff() {
  local destination="$1"
  LC_ALL=C git -c core.quotePath=true diff \
    --no-ext-diff \
    --no-textconv \
    --binary \
    --full-index \
    --no-color \
    HEAD -- "${wiki_dir}" > "${destination}"
}

python_executable=""
src_dir=""
wiki_dir=""
helper_cache_dir=""
evidence_dir=""
github_output=""
jobs=""

while (($#)); do
  case "$1" in
    --python)
      require_value "$1" "$#"
      [[ -z "${python_executable}" ]] || die "--python may be supplied only once"
      python_executable="$2"
      shift 2
      ;;
    --src-dir)
      require_value "$1" "$#"
      [[ -z "${src_dir}" ]] || die "--src-dir may be supplied only once"
      src_dir="$2"
      shift 2
      ;;
    --wiki-dir)
      require_value "$1" "$#"
      [[ -z "${wiki_dir}" ]] || die "--wiki-dir may be supplied only once"
      wiki_dir="$2"
      shift 2
      ;;
    --helper-cache-dir)
      require_value "$1" "$#"
      [[ -z "${helper_cache_dir}" ]] ||
        die "--helper-cache-dir may be supplied only once"
      helper_cache_dir="$2"
      shift 2
      ;;
    --evidence-dir)
      require_value "$1" "$#"
      [[ -z "${evidence_dir}" ]] || die "--evidence-dir may be supplied only once"
      evidence_dir="$2"
      shift 2
      ;;
    --github-output)
      require_value "$1" "$#"
      [[ -z "${github_output}" ]] ||
        die "--github-output may be supplied only once"
      github_output="$2"
      shift 2
      ;;
    --jobs)
      require_value "$1" "$#"
      [[ -z "${jobs}" ]] || die "--jobs may be supplied only once"
      jobs="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n "${python_executable}" ]] || die "--python is required"
[[ -n "${src_dir}" ]] || die "--src-dir is required"
[[ -n "${wiki_dir}" ]] || die "--wiki-dir is required"
[[ -n "${helper_cache_dir}" ]] || die "--helper-cache-dir is required"
[[ -n "${evidence_dir}" ]] || die "--evidence-dir is required"
[[ -n "${github_output}" ]] || die "--github-output is required"
[[ "${jobs}" == "1" ]] || die "--jobs must be exactly 1"
[[ -n "${RUNNER_TEMP:-}" ]] || die "RUNNER_TEMP is required"
[[ -n "${GITHUB_STEP_SUMMARY:-}" ]] || die "GITHUB_STEP_SUMMARY is required"
[[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]] ||
  die "GITHUB_SHA must be a full lowercase Git SHA"

for path_and_label in \
  "${python_executable}" \
  "${src_dir}" \
  "${wiki_dir}" \
  "${helper_cache_dir}" \
  "${evidence_dir}" \
  "${github_output}" \
  "${RUNNER_TEMP}" \
  "${GITHUB_STEP_SUMMARY}"; do
  reject_multiline "${path_and_label}" "path"
done

case "${python_executable}" in
  */*) ;;
  *) die "--python must be an explicit path" ;;
esac
[[ -f "${python_executable}" && -x "${python_executable}" ]] ||
  die "--python must name an executable file: ${python_executable}"

python_probe="$("${python_executable}" -I -c \
  'import sys; sys.stdout.write("llm-wiki-convergence-python-v1")')"
probe_exit=$?
[[ ${probe_exit} -eq 0 && \
  "${python_probe}" == "llm-wiki-convergence-python-v1" ]] ||
  die "--python did not execute the required Python probe"

case "${wiki_dir}" in
  ""|.|/*|../*|*/../*|*/..|./*|*//*|:*|-*|*\\*)
    die "--wiki-dir must be a normalized repository-relative POSIX path"
    ;;
esac

[[ -d "${RUNNER_TEMP}" && ! -L "${RUNNER_TEMP}" ]] ||
  die "RUNNER_TEMP must be a real directory"
readonly EXPECTED_EVIDENCE_DIR="${RUNNER_TEMP}/llm-wiki-convergence-evidence"
[[ "${evidence_dir}" == "${EXPECTED_EVIDENCE_DIR}" ]] ||
  die "--evidence-dir must be ${EXPECTED_EVIDENCE_DIR}"
[[ ! -e "${evidence_dir}" && ! -L "${evidence_dir}" ]] ||
  die "evidence directory is already occupied: ${evidence_dir}"

[[ -d "${helper_cache_dir}" && ! -L "${helper_cache_dir}" ]] ||
  die "--helper-cache-dir must be a real directory"

repository_root="$(git rev-parse --show-toplevel 2>/dev/null)" ||
  die "current directory is not a Git worktree"
physical_cwd="$(pwd -P)" || die "could not resolve current directory"
[[ "${repository_root}" == "${physical_cwd}" ]] ||
  die "wrapper must run from the Git worktree root"
head_sha="$(git rev-parse HEAD 2>/dev/null)" ||
  die "could not resolve the checked-out commit"
[[ "${head_sha}" == "${GITHUB_SHA}" ]] ||
  die "GITHUB_SHA does not match the checked-out commit"

summary_parent="$(dirname -- "${GITHUB_STEP_SUMMARY}")"
[[ -d "${summary_parent}" ]] || die "summary parent directory does not exist"
[[ -f "${github_output}" && ! -L "${github_output}" ]] ||
  die "--github-output must name the runner's regular output file"

readonly WIKI_STATUS_BEFORE="${evidence_dir}/wiki-status-before.txt"
readonly WIKI_STATUS_AFTER="${evidence_dir}/wiki-status-after.txt"
readonly WORKTREE_STATUS_AFTER="${evidence_dir}/worktree-status-after.txt"
readonly WIKI_DIFF="${evidence_dir}/wiki-diff.patch"
readonly SYNC_LOG="${evidence_dir}/sync.log"
readonly RESULT_JSON="${evidence_dir}/convergence-result.json"

worktree_before="$(mktemp "${RUNNER_TEMP}/llm-wiki-worktree-before.XXXXXX")" ||
  die "could not reserve pre-sync worktree status"
inventory_cache_dir="$(mktemp -d \
  "${RUNNER_TEMP}/llm-wiki-convergence-cache.XXXXXX")" ||
  die "could not reserve convergence cache"

cleanup() {
  rm -f -- "${worktree_before}" || true
}
trap cleanup EXIT

mkdir -- "${evidence_dir}" || die "could not create evidence directory"
[[ -d "${evidence_dir}" && ! -L "${evidence_dir}" ]] ||
  die "evidence directory must be a real directory"

for evidence_path in \
  "${WIKI_STATUS_BEFORE}" \
  "${WIKI_STATUS_AFTER}" \
  "${WORKTREE_STATUS_AFTER}" \
  "${WIKI_DIFF}" \
  "${SYNC_LOG}" \
  "${RESULT_JSON}"; do
  [[ ! -e "${evidence_path}" && ! -L "${evidence_path}" ]] ||
    die "fixed evidence path is already occupied: ${evidence_path}"
done
: > "${WIKI_STATUS_BEFORE}"
: > "${WIKI_STATUS_AFTER}"
: > "${WORKTREE_STATUS_AFTER}"
: > "${WIKI_DIFF}"
: > "${SYNC_LOG}"
: > "${RESULT_JSON}"
for evidence_path in \
  "${WIKI_STATUS_BEFORE}" \
  "${WIKI_STATUS_AFTER}" \
  "${WORKTREE_STATUS_AFTER}" \
  "${WIKI_DIFF}" \
  "${SYNC_LOG}" \
  "${RESULT_JSON}"; do
  [[ -f "${evidence_path}" && ! -L "${evidence_path}" ]] ||
    die "could not reserve regular evidence file: ${evidence_path}"
done
printf 'evidence-ready=true\n' >> "${github_output}" ||
  die "could not publish the evidence readiness output"

before_status_exit=0
capture_scoped_status "${WIKI_STATUS_BEFORE}" || before_status_exit=$?
before_worktree_exit=0
capture_worktree_status "${worktree_before}" || before_worktree_exit=$?

before_count="$(status_count "${WIKI_STATUS_BEFORE}")" ||
  die "could not count pre-sync wiki status"
before_worktree_count="$(status_count "${worktree_before}")" ||
  die "could not count pre-sync worktree status"

sync_started=false
sync_exit=0
if [[ ${before_status_exit} -eq 0 && ${before_worktree_exit} -eq 0 &&
      ${before_count} -eq 0 && ${before_worktree_count} -eq 0 ]]; then
  sync_started=true
  set +e
  "${python_executable}" -I -m llm_wiki_cli.cli sync \
    --src-dir "${src_dir}" \
    --wiki-dir "${wiki_dir}" \
    --cache-dir "${inventory_cache_dir}" \
    --helper-cache-dir "${helper_cache_dir}" \
    --jobs "${jobs}" \
    --no-plugins > "${SYNC_LOG}" 2>&1
  sync_exit=$?
else
  printf '%s\n' \
    "Sync was not started because the pre-sync worktree was not clean and available." \
    > "${SYNC_LOG}"
fi

after_status_exit=0
capture_scoped_status "${WIKI_STATUS_AFTER}" || after_status_exit=$?
after_worktree_exit=0
capture_worktree_status "${WORKTREE_STATUS_AFTER}" || after_worktree_exit=$?
after_diff_exit=0
capture_wiki_diff "${WIKI_DIFF}" || after_diff_exit=$?

after_count="$(status_count "${WIKI_STATUS_AFTER}")" ||
  die "could not count post-sync wiki status"
after_worktree_count="$(status_count "${WORKTREE_STATUS_AFTER}")" ||
  die "could not count post-sync worktree status"

worktree_matches_scoped=false
if [[ ${after_status_exit} -eq 0 && ${after_worktree_exit} -eq 0 ]] &&
  cmp -s -- "${WIKI_STATUS_AFTER}" "${WORKTREE_STATUS_AFTER}"; then
  worktree_matches_scoped=true
fi

final_exit=0
if ${sync_started} && [[ ${sync_exit} -ne 0 ]]; then
  final_exit=${sync_exit}
elif [[ ${before_status_exit} -ne 0 || ${before_worktree_exit} -ne 0 ||
        ${before_count} -ne 0 || ${before_worktree_count} -ne 0 ||
        ${after_status_exit} -ne 0 || ${after_worktree_exit} -ne 0 ||
        ${after_diff_exit} -ne 0 ||
        ${after_count} -ne 0 ]] || ! ${worktree_matches_scoped}; then
  final_exit=1
fi

decision="FAIL"
[[ ${final_exit} -eq 0 ]] && decision="PASS"

result_program=$(cat <<'PY'
import hashlib
import json
import pathlib
import sys

schema, candidate_sha, wiki_dir, decision = sys.argv[1:5]
sync_started = sys.argv[5] == "true"
sync_exit = int(sys.argv[6]) if sync_started else None
before_status_exit = int(sys.argv[7])
before_worktree_exit = int(sys.argv[8])
after_status_exit = int(sys.argv[9])
after_worktree_exit = int(sys.argv[10])
after_diff_exit = int(sys.argv[11])
before_worktree_count = int(sys.argv[12])
worktree_matches_scoped = sys.argv[13] == "true"
output = pathlib.Path(sys.argv[14])
evidence_paths = [pathlib.Path(value) for value in sys.argv[15:]]


def record(path: pathlib.Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"evidence is not a regular file: {path}")
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "filename": path.name,
        "records": len(raw.splitlines()),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


records = {path.name: record(path) for path in evidence_paths}
payload = {
    "candidate_sha": candidate_sha,
    "captures": {
        "wiki_diff": {"exit_code": after_diff_exit},
    },
    "checks": {
        "post_sync_diff_available": after_diff_exit == 0,
        "post_sync_status_available": (
            after_status_exit == 0 and after_worktree_exit == 0
        ),
        "post_sync_wiki_clean": records["wiki-status-after.txt"]["records"] == 0,
        "pre_sync_status_available": (
            before_status_exit == 0 and before_worktree_exit == 0
        ),
        "pre_sync_wiki_clean": records["wiki-status-before.txt"]["records"] == 0,
        "pre_sync_worktree_clean": before_worktree_count == 0,
        "worktree_changes_scoped_to_wiki": worktree_matches_scoped,
    },
    "decision": decision,
    "evidence": records,
    "schema_version": schema,
    "sync": {
        "exit_code": sync_exit,
        "plugins_enabled": False,
        "started": sync_started,
    },
    "wiki_dir": wiki_dir,
}
if output.is_symlink() or not output.is_file() or output.stat().st_size != 0:
    raise SystemExit("reserved result JSON is not one empty regular file")
output.write_text(
    json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
    encoding="utf-8",
)
if output.is_symlink() or not output.is_file():
    raise SystemExit("result JSON is not a regular file")
PY
)

"${python_executable}" -I -c "${result_program}" \
  "${RESULT_SCHEMA}" \
  "${GITHUB_SHA}" \
  "${wiki_dir}" \
  "${decision}" \
  "${sync_started}" \
  "${sync_exit}" \
  "${before_status_exit}" \
  "${before_worktree_exit}" \
  "${after_status_exit}" \
  "${after_worktree_exit}" \
  "${after_diff_exit}" \
  "${before_worktree_count}" \
  "${worktree_matches_scoped}" \
  "${RESULT_JSON}" \
  "${WIKI_STATUS_BEFORE}" \
  "${WIKI_STATUS_AFTER}" \
  "${WORKTREE_STATUS_AFTER}" \
  "${WIKI_DIFF}" \
  "${SYNC_LOG}"
result_exit=$?
if [[ ${result_exit} -ne 0 ]]; then
  printf 'Could not write convergence result JSON.\n' >&2
  [[ ${sync_exit} -ne 0 && "${sync_started}" == "true" ]] || final_exit=1
fi

summary_program=$(cat <<'PY'
import pathlib
import sys

MAX_LINES = int(sys.argv[8])
MAX_BYTES = int(sys.argv[9])
STATUS_LIMIT = int(sys.argv[10])


def clip_utf8(value: str, limit: int = 240) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= limit:
        return value
    prefix = encoded[: limit - 3]
    while True:
        try:
            return prefix.decode("utf-8") + "..."
        except UnicodeDecodeError as exc:
            prefix = prefix[: exc.start]


summary_path = pathlib.Path(sys.argv[1])
decision = sys.argv[2]
sync_started = sys.argv[3] == "true"
sync_exit = int(sys.argv[4])
before_count = int(sys.argv[5])
after_count = int(sys.argv[6])
full_count = int(sys.argv[7])
status_path = pathlib.Path(sys.argv[11])
worktree_matches_scoped = sys.argv[12] == "true"

lines = [
    "## LLM Wiki scheduled convergence",
    f"- Result: **{decision}**",
    f"- Real sync started: `{'yes' if sync_started else 'no'}`",
    f"- Sync exit: `{sync_exit if sync_started else 'not-run'}`",
    f"- Pre-sync wiki status records: `{before_count}`",
    f"- Post-sync wiki status records: `{after_count}`",
    f"- Full post-sync worktree records: `{full_count}`",
    (
        "- Full-worktree changes are wiki-scoped: "
        f"`{'yes' if worktree_matches_scoped else 'no'}`"
    ),
]
if sync_started:
    lines.append(
        "- `llm-wiki sync` ran without `--dry-run`, `--force`, or project plugins."
    )
else:
    lines.append("- Sync was not started; inspect the complete pre-sync evidence.")
if after_count:
    lines.append("- Post-sync wiki status (bounded preview; artifact is complete):")
    records = status_path.read_bytes().splitlines()
    for raw_record in records[:STATUS_LIMIT]:
        record = raw_record.decode("utf-8", "backslashreplace")
        record = record.replace(chr(96), "\\x60")
        lines.append(f"  - `{clip_utf8(record)}`")
    if after_count > STATUS_LIMIT:
        lines.append(f"  - ... {after_count - STATUS_LIMIT} additional records omitted")

payload = ("\n".join(lines) + "\n").encode("utf-8")
if len(lines) > MAX_LINES or len(payload) > MAX_BYTES:
    raise SystemExit("bounded summary invariant failed")
with summary_path.open("ab") as stream:
    stream.write(payload)
PY
)

"${python_executable}" -I -c "${summary_program}" \
  "${GITHUB_STEP_SUMMARY}" \
  "${decision}" \
  "${sync_started}" \
  "${sync_exit}" \
  "${before_count}" \
  "${after_count}" \
  "${after_worktree_count}" \
  "${SUMMARY_MAX_LINES}" \
  "${SUMMARY_MAX_BYTES}" \
  "${STATUS_SUMMARY_LIMIT}" \
  "${WIKI_STATUS_AFTER}" \
  "${worktree_matches_scoped}"
summary_exit=$?
if [[ ${summary_exit} -ne 0 ]]; then
  printf 'Could not write the bounded convergence summary.\n' >&2
  [[ ${sync_exit} -ne 0 && "${sync_started}" == "true" ]] || final_exit=1
fi

exit "${final_exit}"
