#!/usr/bin/env bash

set -uo pipefail

readonly SUMMARY_MAX_LINES=40
readonly SUMMARY_MAX_BYTES=8192
readonly STATUS_RECORD_LIMIT=20

usage() {
  cat <<'EOF'
Usage:
  run-llm-wiki-ci-check.sh \
    --python PATH \
    --src-dir PATH \
    --wiki-dir PATH \
    --helper-cache-dir PATH \
    --report-dir PATH \
    --jobs 1 \
    --knowledge-drift-report

The selected Python is used both to invoke `llm_wiki_cli.cli` and to parse its
JSON output. Project-local plugins are disabled, and the bounded result summary
is written to GITHUB_STEP_SUMMARY.
EOF
}

die() {
  printf 'run-llm-wiki-ci-check: %s\n' "$*" >&2
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

python_executable=""
src_dir=""
wiki_dir=""
helper_cache_dir=""
report_dir=""
jobs=""
knowledge_drift_report=false

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
    --report-dir)
      require_value "$1" "$#"
      [[ -z "${report_dir}" ]] || die "--report-dir may be supplied only once"
      report_dir="$2"
      shift 2
      ;;
    --jobs)
      require_value "$1" "$#"
      [[ -z "${jobs}" ]] || die "--jobs may be supplied only once"
      jobs="$2"
      shift 2
      ;;
    --knowledge-drift-report)
      ${knowledge_drift_report} &&
        die "--knowledge-drift-report may be supplied only once"
      knowledge_drift_report=true
      shift
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
[[ -n "${report_dir}" ]] || die "--report-dir is required"
[[ "${jobs}" == "1" ]] || die "--jobs must be exactly 1"
${knowledge_drift_report} || die "--knowledge-drift-report is required"
[[ -n "${GITHUB_STEP_SUMMARY:-}" ]] || die "GITHUB_STEP_SUMMARY is required"

for path_and_label in \
  "${python_executable}" \
  "${src_dir}" \
  "${wiki_dir}" \
  "${helper_cache_dir}" \
  "${report_dir}" \
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
  'import sys; sys.stdout.write("llm-wiki-ci-python-v1")')"
probe_exit=$?
[[ ${probe_exit} -eq 0 && "${python_probe}" == "llm-wiki-ci-python-v1" ]] ||
  die "--python did not execute the required Python probe"

summary_parent="$(dirname -- "${GITHUB_STEP_SUMMARY}")"
[[ -d "${summary_parent}" ]] || die "summary parent directory does not exist"
if [[ -e "${report_dir}" || -L "${report_dir}" ]]; then
  [[ -d "${report_dir}" && ! -L "${report_dir}" ]] ||
    die "report directory must be a real directory"
else
  mkdir -p -- "${report_dir}" || die "could not create report directory"
fi
[[ -d "${report_dir}" && ! -L "${report_dir}" ]] ||
  die "report directory must be a real directory"

readonly MARKDOWN_REPORT="${report_dir}/llm-wiki-ci-report.md"
readonly JSON_REPORT="${report_dir}/llm-wiki-ci-report.json"
readonly INVALID_REPORT="${report_dir}/llm-wiki-ci-report.invalid.txt"
collision_quarantine=""

quarantine_evidence_path() {
  local evidence_path="$1"
  local leaf="${evidence_path##*/}"
  if [[ -z "${collision_quarantine}" ]]; then
    collision_quarantine="$(
      mktemp -d "${report_dir}/.llm-wiki-ci-collision.XXXXXX"
    )" || collision_quarantine=""
  fi
  if [[ -n "${collision_quarantine}" ]] &&
    mv -- "${evidence_path}" "${collision_quarantine}/${leaf}"; then
    return 0
  fi
  case "${evidence_path}" in
    "${report_dir}"/llm-wiki-ci-report.*|\
    "${report_dir}"/.llm-wiki-ci-report.raw.*)
      rm -rf -- "${evidence_path}" &&
        [[ ! -e "${evidence_path}" && ! -L "${evidence_path}" ]]
      ;;
    *) return 1 ;;
  esac
}

for stale_output in "${MARKDOWN_REPORT}" "${JSON_REPORT}" "${INVALID_REPORT}"; do
  if [[ -e "${stale_output}" || -L "${stale_output}" ]]; then
    quarantine_evidence_path "${stale_output}" ||
      die "could not quarantine stale evidence"
  fi
  [[ ! -e "${stale_output}" && ! -L "${stale_output}" ]] ||
    die "could not clear stale evidence"
done

raw_output="$(mktemp "${report_dir}/.llm-wiki-ci-report.raw.XXXXXX")" ||
  die "could not create temporary raw output"
status_output="$(mktemp "${report_dir}/.llm-wiki-ci-status.raw.XXXXXX")" || {
  rm -f -- "${raw_output}"
  die "could not create temporary status output"
}
sorted_status="$(mktemp "${report_dir}/.llm-wiki-ci-status.sorted.XXXXXX")" || {
  rm -f -- "${raw_output}" "${status_output}"
  die "could not create temporary sorted status output"
}

ci_completed=false
cli_exit=0

cleanup() {
  local command_exit=$?
  local returned_exit="${command_exit}"
  trap - EXIT
  rm -f -- "${raw_output}" "${status_output}" "${sorted_status}" || true
  if ${ci_completed} && [[ ${cli_exit} -ne 0 ]]; then
    returned_exit="${cli_exit}"
  fi
  exit "${returned_exit}"
}
trap cleanup EXIT

set +e
"${python_executable}" -I -m llm_wiki_cli.cli ci-check \
  --src-dir "${src_dir}" \
  --wiki-dir "${wiki_dir}" \
  --helper-cache-dir "${helper_cache_dir}" \
  --report "${MARKDOWN_REPORT}" \
  --jobs "${jobs}" \
  --knowledge-drift-report \
  --format json \
  --no-plugins > "${raw_output}"
cli_exit=$?
ci_completed=true
set -e

json_valid=false
json_state="unavailable (no output)"
evidence_collision=false
for unexpected_output in "${JSON_REPORT}" "${INVALID_REPORT}"; do
  if [[ -e "${unexpected_output}" || -L "${unexpected_output}" ]]; then
    evidence_collision=true
    printf 'CI created an unexpected final evidence path: %s\n' \
      "${unexpected_output}" >&2
    quarantine_evidence_path "${unexpected_output}" ||
      printf 'Could not quarantine unexpected evidence path: %s\n' \
        "${unexpected_output}" >&2
  fi
done

if ${evidence_collision}; then
  json_state="unavailable (unexpected evidence-path collision)"
elif [[ -f "${raw_output}" && ! -L "${raw_output}" && -s "${raw_output}" ]]; then
  set +e
  "${python_executable}" -I -c \
    'import json, pathlib, sys; json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' \
    "${raw_output}"
  json_parse_exit=$?
  set -e
  if [[ ${json_parse_exit} -eq 0 ]]; then
    if [[ ! -e "${JSON_REPORT}" && ! -L "${JSON_REPORT}" ]] &&
      mv -- "${raw_output}" "${JSON_REPORT}" &&
      [[ -f "${JSON_REPORT}" && ! -L "${JSON_REPORT}" ]]; then
      json_valid=true
      json_state="available (parseable JSON)"
    else
      json_state="unavailable (could not preserve parseable output)"
      if [[ -e "${JSON_REPORT}" || -L "${JSON_REPORT}" ]]; then
        quarantine_evidence_path "${JSON_REPORT}" ||
          printf 'Could not quarantine rejected JSON evidence path: %s\n' \
            "${JSON_REPORT}" >&2
      fi
      printf 'Could not preserve parseable JSON evidence.\n' >&2
    fi
  else
    json_state="unavailable (invalid output; diagnostic raw available)"
    if [[ ! -e "${INVALID_REPORT}" && ! -L "${INVALID_REPORT}" ]] &&
      mv -- "${raw_output}" "${INVALID_REPORT}" &&
      [[ -f "${INVALID_REPORT}" && ! -L "${INVALID_REPORT}" ]]; then
      printf 'CI output is not parseable JSON; preserved as %s.\n' \
        "${INVALID_REPORT}" >&2
    else
      json_state="unavailable (invalid output could not be preserved)"
      if [[ -e "${INVALID_REPORT}" || -L "${INVALID_REPORT}" ]]; then
        quarantine_evidence_path "${INVALID_REPORT}" ||
          printf 'Could not quarantine rejected diagnostic evidence path: %s\n' \
            "${INVALID_REPORT}" >&2
      fi
      printf 'CI output is not parseable JSON and could not be preserved.\n' >&2
    fi
  fi
elif [[ -e "${raw_output}" || -L "${raw_output}" ]]; then
  if [[ -f "${raw_output}" && ! -L "${raw_output}" ]]; then
    json_state="unavailable (empty output)"
    rm -f -- "${raw_output}"
    printf 'CI produced empty JSON evidence.\n' >&2
  else
    json_state="unavailable (raw output is not a regular file)"
    quarantine_evidence_path "${raw_output}" ||
      printf 'Could not quarantine invalid raw output path.\n' >&2
    printf 'CI raw JSON evidence is not a regular file.\n' >&2
  fi
else
  printf 'CI produced no JSON evidence.\n' >&2
fi

markdown_available=false
markdown_state="unavailable"
if [[ -f "${MARKDOWN_REPORT}" && ! -L "${MARKDOWN_REPORT}" &&
      -s "${MARKDOWN_REPORT}" ]]; then
  markdown_available=true
  markdown_state="available"
else
  if [[ -e "${MARKDOWN_REPORT}" || -L "${MARKDOWN_REPORT}" ]]; then
    quarantine_evidence_path "${MARKDOWN_REPORT}" ||
      printf 'Could not quarantine invalid Markdown evidence path: %s\n' \
        "${MARKDOWN_REPORT}" >&2
  fi
  printf 'CI Markdown report is missing, empty, or not a regular file: %s\n' \
    "${MARKDOWN_REPORT}" >&2
fi

set +e
git status --porcelain=v1 --untracked-files=all > "${status_output}"
status_exit=$?
set -e

tree_clean=false
tree_state="unavailable"
status_count=0
if [[ ${status_exit} -eq 0 ]]; then
  if LC_ALL=C sort -- "${status_output}" > "${sorted_status}"; then
    while IFS= read -r _status_record; do
      ((status_count += 1))
    done < "${sorted_status}"
    if [[ ${status_count} -eq 0 ]]; then
      tree_clean=true
      tree_state="clean"
    else
      tree_state="dirty (${status_count} status records)"
      printf 'Validation left the worktree dirty (first %s sorted records):\n' \
        "${STATUS_RECORD_LIMIT}" >&2
      sed -n "1,${STATUS_RECORD_LIMIT}p" "${sorted_status}" |
        while IFS= read -r record; do
          printf '  %s\n' "${record}" >&2
        done
      if ((status_count > STATUS_RECORD_LIMIT)); then
        printf '  ... %s additional status records omitted\n' \
          "$((status_count - STATUS_RECORD_LIMIT))" >&2
      fi
    fi
  else
    printf 'Could not sort complete worktree status diagnostics.\n' >&2
  fi
else
  printf 'Could not inspect the complete worktree status (git exit %s).\n' \
    "${status_exit}" >&2
fi

final_exit=${cli_exit}
if [[ ${cli_exit} -eq 0 ]]; then
  if ! ${json_valid} || ! ${markdown_available} || ! ${tree_clean}; then
    final_exit=1
  fi
fi

result_label="FAIL"
[[ ${final_exit} -eq 0 ]] && result_label="PASS"

summary_program=$(cat <<'PY'
import pathlib
import sys

MAX_LINES = int(sys.argv[9])
MAX_BYTES = int(sys.argv[10])
STATUS_LIMIT = int(sys.argv[11])


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
result = sys.argv[2]
cli_exit = int(sys.argv[3])
json_state = sys.argv[4]
markdown_state = sys.argv[5]
tree_state = sys.argv[6]
status_path = pathlib.Path(sys.argv[7])
status_count = int(sys.argv[8])

lines = [
    "## LLM Wiki integrity",
    f"- Result: **{result}**",
]
if cli_exit != 0:
    lines.append(f"- Original `ci-check` exit: `{cli_exit}`")
lines.extend(
    [
        f"- JSON evidence: {json_state}",
        f"- Markdown report: {markdown_state}",
        f"- Worktree: {tree_state}",
        "- Native drift diagnostics are advisory; integrity validation remains blocking.",
    ]
)
if status_count:
    lines.append("- Dirty-path diagnostics (sorted and bounded):")
    records = status_path.read_bytes().splitlines()
    for raw_record in records[:STATUS_LIMIT]:
        record = raw_record.decode("utf-8", "backslashreplace")
        record = record.replace(chr(96), "\\x60")
        lines.append(f"  - `{clip_utf8(record)}`")
    if status_count > STATUS_LIMIT:
        lines.append(
            f"  - ... {status_count - STATUS_LIMIT} additional status records omitted"
        )

payload = ("\n".join(lines) + "\n").encode("utf-8")
if len(lines) > MAX_LINES or len(payload) > MAX_BYTES:
    raise SystemExit("bounded summary invariant failed")
summary_path.write_bytes(payload)
PY
)

set +e
"${python_executable}" -I -c "${summary_program}" \
  "${GITHUB_STEP_SUMMARY}" \
  "${result_label}" \
  "${cli_exit}" \
  "${json_state}" \
  "${markdown_state}" \
  "${tree_state}" \
  "${sorted_status}" \
  "${status_count}" \
  "${SUMMARY_MAX_LINES}" \
  "${SUMMARY_MAX_BYTES}" \
  "${STATUS_RECORD_LIMIT}"
summary_exit=$?
set -e

if [[ ${summary_exit} -ne 0 ]]; then
  printf 'Could not write the bounded CI summary.\n' >&2
  [[ ${cli_exit} -ne 0 ]] || final_exit=1
  {
    printf '%s\n' '## LLM Wiki integrity'
    printf '%s\n' '- Result: **FAIL**'
    if [[ ${cli_exit} -ne 0 ]]; then
      printf '%s\n' "- Original \`ci-check\` exit: \`${cli_exit}\`"
    fi
    printf '%s\n' "- JSON evidence: ${json_state}"
    printf '%s\n' "- Markdown report: ${markdown_state}"
    printf '%s\n' '- Summary rendering failed.'
    printf '%s\n' '- Native drift diagnostics are advisory; integrity validation remains blocking.'
  } > "${GITHUB_STEP_SUMMARY}" || true
fi

exit "${final_exit}"
