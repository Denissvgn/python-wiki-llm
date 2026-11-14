#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd -P)"
readonly QUALIFICATION_HELPER="${PROJECT_ROOT}/release/qualification.py"

die() {
  printf 'setup-llm-wiki-ci-toolchains: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  setup-llm-wiki-ci-toolchains.sh --mode MODE --install-root PATH [OPTIONS]

Required:
  --mode routine            Install the locked Node/npm routine toolchain.
  --mode qualification-go   Install locked Go for local qualification tools.
  --mode extractor-go       Install locked Go for the Go extractor helper.
  --mode extractor-rust     Install locked Rust for the Rust extractor helper.
  --mode extractor-haskell  Install locked GHC for the Haskell extractor helper.
  --install-root PATH       Install below this dedicated root.

Options:
  --environment-file PATH   Local shell handoff file. Defaults below checkout
                            Git metadata (including linked worktrees).
  --lock PATH               Toolchain lock (default: release/toolchain-lock.json).
  --python PATH             Qualification Python. Local use is restricted to
                            .venv/bin/python; Actions may pass setup-python's
                            selected interpreter.
  --help                    Show this message.

When GITHUB_ACTIONS=true, --install-root must be below RUNNER_TEMP and the
script persists executable paths through GITHUB_PATH/GITHUB_ENV. Otherwise,
the install root and environment file must be ignored paths in this checkout
or use its dedicated llm-wiki-ci-* Git metadata namespace.
Linux x86_64/ARM64 supports all modes with explicit locked host artifacts.
Darwin ARM64 supports locked Node/npm and Go; other hosts fail before download.
EOF
}

mode=""
install_root_input=""
environment_file_input=""
environment_file=""
lock_path="${PROJECT_ROOT}/release/toolchain-lock.json"
qualification_python=""

while (($#)); do
  case "$1" in
    --mode)
      (($# >= 2)) || die "--mode requires a value"
      mode="$2"
      shift 2
      ;;
    --install-root)
      (($# >= 2)) || die "--install-root requires a value"
      install_root_input="$2"
      shift 2
      ;;
    --environment-file)
      (($# >= 2)) || die "--environment-file requires a value"
      environment_file_input="$2"
      shift 2
      ;;
    --lock)
      (($# >= 2)) || die "--lock requires a value"
      lock_path="$2"
      shift 2
      ;;
    --python)
      (($# >= 2)) || die "--python requires a value"
      qualification_python="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

case "${mode}" in
  routine|qualification-go|extractor-go|extractor-rust|extractor-haskell) ;;
  "") die "--mode is required" ;;
  *) die "unsupported mode: ${mode}" ;;
esac
[[ -n "${install_root_input}" ]] || die "--install-root is required"
[[ -f "${lock_path}" ]] || die "toolchain lock is not a file: ${lock_path}"
[[ -f "${QUALIFICATION_HELPER}" ]] || die "qualification helper is missing"

reject_multiline_path() {
  local value="$1"
  local label="$2"
  [[ "${value}" != *$'\n'* && "${value}" != *$'\r'* ]] ||
    die "${label} must not contain a newline"
}

absolute_path_with_existing_parent() {
  local input="$1"
  local parent
  local leaf
  reject_multiline_path "${input}" "path"
  if [[ "${input}" != /* ]]; then
    input="${PWD}/${input}"
  fi
  parent="$(dirname -- "${input}")"
  leaf="$(basename -- "${input}")"
  [[ "${leaf}" != "." && "${leaf}" != ".." ]] ||
    die "path must name a dedicated child: ${input}"
  [[ -d "${parent}" ]] || die "path parent does not exist: ${parent}"
  parent="$(cd -- "${parent}" && pwd -P)"
  printf '%s/%s\n' "${parent}" "${leaf}"
}

canonical_existing_file() {
  local input="$1"
  local parent
  local leaf
  reject_multiline_path "${input}" "path"
  if [[ "${input}" != /* ]]; then
    input="${PWD}/${input}"
  fi
  parent="$(cd -- "$(dirname -- "${input}")" && pwd -P)"
  leaf="$(basename -- "${input}")"
  printf '%s/%s\n' "${parent}" "${leaf}"
}

install_root="$(absolute_path_with_existing_parent "${install_root_input}")"
[[ "${install_root}" != *:* ]] ||
  die "install root must not contain ':' because it becomes a PATH entry"
lock_path="$(canonical_existing_file "${lock_path}")"
github_actions=false
checkout_git_dir=""
if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  github_actions=true
fi

checkout_git() {
  # The install destination belongs to this checkout, not an ambient alternate
  # repository/index. Linked worktree gitfiles must resolve their own metadata.
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_INDEX_FILE \
    -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
    git --no-replace-objects -C "${PROJECT_ROOT}" \
      --git-dir "${PROJECT_ROOT}/.git" --work-tree "${PROJECT_ROOT}" "$@"
}

is_checkout_ignored_path() {
  local path="$1"
  local relative
  if [[ -n "${checkout_git_dir}" ]]; then
    case "${path}" in
      "${checkout_git_dir}/llm-wiki-ci-"*) return 0 ;;
      "${checkout_git_dir}/"*) return 1 ;;
    esac
  fi
  case "${path}" in
    "${PROJECT_ROOT}/.git/"*) return 1 ;;
    "${PROJECT_ROOT}/"*)
      relative="${path#"${PROJECT_ROOT}/"}"
      checkout_git check-ignore -q -- "${relative}"
      return
      ;;
    *) return 1 ;;
  esac
}

checkout_path_is_tracked() {
  local path="$1"
  local relative
  local tracked
  case "${path}" in
    "${PROJECT_ROOT}/.git/"*) return 1 ;;
    "${PROJECT_ROOT}/"*) relative="${path#"${PROJECT_ROOT}/"}" ;;
    *) return 1 ;;
  esac
  while IFS= read -r -d '' tracked; do
    [[ "${tracked}" == "${relative}" ]] && return 0
  done < <(checkout_git ls-files -z)
  return 1
}

checkout_tree_contains_tracked_paths() {
  local path="$1"
  local relative
  local tracked
  case "${path}" in
    "${PROJECT_ROOT}/.git/"*) return 1 ;;
    "${PROJECT_ROOT}/"*) relative="${path#"${PROJECT_ROOT}/"}" ;;
    *) return 1 ;;
  esac
  while IFS= read -r -d '' tracked; do
    case "${tracked}" in
      "${relative}"|"${relative}/"*) return 0 ;;
    esac
  done < <(checkout_git ls-files -z)
  return 1
}

if ${github_actions}; then
  [[ -n "${RUNNER_TEMP:-}" ]] || die "RUNNER_TEMP is required in Actions"
  [[ -n "${GITHUB_PATH:-}" ]] || die "GITHUB_PATH is required in Actions"
  [[ -n "${GITHUB_ENV:-}" ]] || die "GITHUB_ENV is required in Actions"
  [[ -z "${environment_file_input}" ]] ||
    die "--environment-file is local-only; Actions uses GITHUB_PATH/GITHUB_ENV"
  runner_temp="$(cd -- "${RUNNER_TEMP}" && pwd -P)"
  case "${install_root}" in
    "${runner_temp}/"*) ;;
    *) die "Actions install root must be below RUNNER_TEMP" ;;
  esac
  if [[ -z "${qualification_python}" ]]; then
    [[ -n "${pythonLocation:-}" ]] ||
      die "--python or setup-python's pythonLocation is required in Actions"
    qualification_python="${pythonLocation}/bin/python"
  fi
else
  [[ ! -L "${PROJECT_ROOT}/.git" &&
     ( -d "${PROJECT_ROOT}/.git" || -f "${PROJECT_ROOT}/.git" ) ]] ||
    die "local setup requires non-redirected checkout Git metadata"
  checkout_git_dir="$(checkout_git rev-parse --absolute-git-dir)" ||
    die "local checkout Git metadata cannot be resolved"
  reject_multiline_path "${checkout_git_dir}" "checkout Git metadata"
  [[ -d "${checkout_git_dir}" && ! -L "${checkout_git_dir}" &&
     "$(cd -- "${checkout_git_dir}" && pwd -P)" == "${checkout_git_dir}" ]] ||
    die "local checkout Git metadata must be a real canonical directory"
  checkout_tree_contains_tracked_paths "${install_root}" &&
    die "local install root must not be tracked or contain tracked paths"
  is_checkout_ignored_path "${install_root}" ||
    die "local install root must be ignored in this checkout or use its reserved Git metadata namespace"
  if [[ -z "${environment_file_input}" ]]; then
    case "${mode}" in
      routine)
        environment_file_input="${checkout_git_dir}/llm-wiki-ci-toolchains.env"
        ;;
      qualification-go)
        environment_file_input="${checkout_git_dir}/llm-wiki-ci-qualification-go.env"
        ;;
      *)
        environment_file_input="${checkout_git_dir}/llm-wiki-ci-${mode}.env"
        ;;
    esac
  fi
  environment_file="$(absolute_path_with_existing_parent "${environment_file_input}")"
  if [[ -e "${environment_file}" || -L "${environment_file}" ]]; then
    [[ -f "${environment_file}" && ! -L "${environment_file}" ]] ||
      die "local environment file must be absent or a non-symlink regular file"
  fi
  checkout_path_is_tracked "${environment_file}" &&
    die "local environment file must not be tracked"
  is_checkout_ignored_path "${environment_file}" ||
    die "local environment file must be ignored in this checkout or use its reserved Git metadata namespace"
  expected_python="${PROJECT_ROOT}/.venv/bin/python"
  if [[ -z "${qualification_python}" ]]; then
    qualification_python="${expected_python}"
  fi
  qualification_python="$(canonical_existing_file "${qualification_python}")"
  [[ "${qualification_python}" == "${expected_python}" ]] ||
    die "local qualification helper must use ${expected_python}"
fi

[[ -x "${qualification_python}" ]] ||
  die "qualification Python is not executable: ${qualification_python}"
qualification_python="$(canonical_existing_file "${qualification_python}")"

lock_value() {
  "${qualification_python}" -I "${QUALIFICATION_HELPER}" lock-value \
    --lock "${lock_path}" --key "$1"
}

verify_download() {
  local key="$1"
  local output="$2"
  "${qualification_python}" -I "${QUALIFICATION_HELPER}" verify-download \
    --lock "${lock_path}" --key "${key}" --output "${output}"
}

kernel="$(uname -s)"
machine="$(uname -m)"
linux_native=false
case "${kernel}:${machine}" in
  Linux:x86_64|Linux:amd64)
    artifact_suffix="artifact"
    expected_go_platform="linux/amd64"
    expected_rust_platform="x86_64-unknown-linux-gnu"
    expected_ghc_platform="x86_64-unknown-linux"
    linux_native=true
    ;;
  Linux:aarch64|Linux:arm64)
    artifact_suffix="platform_artifacts.linux_arm64"
    expected_go_platform="linux/arm64"
    expected_rust_platform="aarch64-unknown-linux-gnu"
    expected_ghc_platform="aarch64-unknown-linux"
    linux_native=true
    ;;
  Darwin:arm64|Darwin:aarch64)
    artifact_suffix="platform_artifacts.darwin_arm64"
    expected_go_platform="darwin/arm64"
    ;;
  *) die "no locked ${mode} artifact for ${kernel}/${machine}" ;;
esac
if [[ "${mode}" == "extractor-rust" || "${mode}" == "extractor-haskell" ]]; then
  ${linux_native} ||
    die "no locked ${mode} artifact for ${kernel}/${machine}"
fi

require_locked_artifact() {
  local key="$1"
  lock_value "${key}.url" >/dev/null &&
    lock_value "${key}.sha256" >/dev/null ||
    die "no locked ${mode} artifact for ${kernel}/${machine}: ${key}"
}

# Select every required artifact before making install/cache paths or downloading.
case "${mode}" in
  routine)
    require_locked_artifact "toolchains.node.${artifact_suffix}"
    require_locked_artifact toolchains.npm.artifact
    ;;
  qualification-go|extractor-go)
    require_locked_artifact "toolchains.go.${artifact_suffix}"
    ;;
  extractor-rust)
    rust_artifact_key="toolchains.rust.${artifact_suffix}"
    rust_clippy_key="toolchains.rust.clippy_artifact"
    if [[ "${artifact_suffix}" != artifact ]]; then
      rust_clippy_key="toolchains.rust.platform_clippy_artifacts.linux_arm64"
    fi
    require_locked_artifact toolchains.rust.checksum_manifest
    require_locked_artifact "${rust_artifact_key}"
    require_locked_artifact "${rust_clippy_key}"
    ;;
  extractor-haskell)
    require_locked_artifact "toolchains.haskell.${artifact_suffix}"
    ;;
esac

mkdir -p -- "${install_root}"
[[ -d "${install_root}" && ! -L "${install_root}" ]] ||
  die "install root must be a real directory"

target=""
staging_dir=""
target_created=false
environment_temporary_file=""
cleanup() {
  if [[ -n "${environment_temporary_file}" &&
        ( -e "${environment_temporary_file}" ||
          -L "${environment_temporary_file}" ) ]]; then
    case "${environment_temporary_file}" in
      "${environment_file}.tmp."*) rm -f -- "${environment_temporary_file}" ;;
      *) printf 'refusing to clean unexpected environment temporary path: %s\n' \
          "${environment_temporary_file}" >&2 ;;
    esac
  fi
  if ${target_created}; then
    case "${target}" in
      "${install_root}/node"|"${install_root}/go"|\
      "${install_root}/rust"|"${install_root}/haskell")
        rm -rf -- "${target}"
        ;;
      *) printf 'refusing to clean unexpected target path: %s\n' \
          "${target}" >&2 ;;
    esac
  fi
  if [[ -n "${staging_dir}" && -d "${staging_dir}" ]]; then
    case "${staging_dir}" in
      "${install_root}/.setup-"*) rm -rf -- "${staging_dir}" ;;
      *) printf 'refusing to clean unexpected staging path: %s\n' \
          "${staging_dir}" >&2 ;;
    esac
  fi
}
trap cleanup EXIT
staging_dir="$(mktemp -d "${install_root}/.setup-${mode}.XXXXXX")"

write_local_environment() {
  local executable_path="$1"
  local go_binary="${2:-}"
  local ghc_binary="${3:-}"
  environment_temporary_file="$(mktemp "${environment_file}.tmp.XXXXXX")"
  {
    printf '# Generated by setup-llm-wiki-ci-toolchains.sh; source with Bash.\n'
    printf 'export PATH=%q:"${PATH}"\n' "${executable_path}"
    if [[ "${mode}" == routine ]]; then
      printf 'unset LLM_WIKI_GO\n'
    fi
    if [[ -n "${go_binary}" ]]; then
      printf 'export LLM_WIKI_GO=%q\n' "${go_binary}"
    fi
    if [[ -n "${ghc_binary}" ]]; then
      printf 'export LLM_WIKI_GHC=%q\n' "${ghc_binary}"
    fi
  } > "${environment_temporary_file}"
  chmod 0600 "${environment_temporary_file}"
  mv -- "${environment_temporary_file}" "${environment_file}"
  environment_temporary_file=""
}

persist_environment() {
  local executable_path="$1"
  local go_binary="${2:-}"
  local ghc_binary="${3:-}"
  if ${github_actions}; then
    printf '%s\n' "${executable_path}" >> "${GITHUB_PATH}"
    if [[ -n "${go_binary}" ]]; then
      printf 'LLM_WIKI_GO=%s\n' "${go_binary}" >> "${GITHUB_ENV}"
    fi
    if [[ -n "${ghc_binary}" ]]; then
      printf 'LLM_WIKI_GHC=%s\n' "${ghc_binary}" >> "${GITHUB_ENV}"
    fi
  else
    write_local_environment "${executable_path}" "${go_binary}" "${ghc_binary}"
  fi
}

case "${mode}" in
routine)
  target="${install_root}/node"
  [[ ! -e "${target}" && ! -L "${target}" ]] ||
    die "routine toolchain target already exists: ${target}"
  node_archive="${staging_dir}/node.tar.xz"
  npm_archive="${staging_dir}/npm.tar.gz"
  node_tree="${staging_dir}/node"
  npm_tree="${staging_dir}/npm"
  verify_download "toolchains.node.${artifact_suffix}" "${node_archive}"
  verify_download "toolchains.npm.artifact" "${npm_archive}"
  mkdir -p -- "${node_tree}" "${npm_tree}"
  tar -xJf "${node_archive}" -C "${node_tree}" --strip-components=1
  tar -xzf "${npm_archive}" -C "${npm_tree}" --strip-components=1
  [[ -x "${node_tree}/bin/node" ]] || die "locked Node extraction is incomplete"
  [[ -f "${npm_tree}/bin/npm-cli.js" ]] || die "locked npm extraction is incomplete"
  if [[ -e "${node_tree}/lib/node_modules/npm" ||
        -L "${node_tree}/lib/node_modules/npm" ]]; then
    mv -- "${node_tree}/lib/node_modules/npm" \
      "${staging_dir}/unselected-bundled-npm"
  fi
  mkdir -p -- "${node_tree}/lib/node_modules"
  mv -- "${npm_tree}" "${node_tree}/lib/node_modules/npm"
  for command_name in npm npx; do
    if [[ -e "${node_tree}/bin/${command_name}" ||
          -L "${node_tree}/bin/${command_name}" ]]; then
      unlink "${node_tree}/bin/${command_name}"
    fi
  done
  ln -s ../lib/node_modules/npm/bin/npm-cli.js "${node_tree}/bin/npm"
  ln -s ../lib/node_modules/npm/bin/npx-cli.js "${node_tree}/bin/npx"
  expected_node="$(lock_value toolchains.node.version_output)"
  expected_npm="$(lock_value toolchains.npm.version_output)"
  actual_node="$("${node_tree}/bin/node" --version)"
  actual_npm="$("${node_tree}/bin/node" \
    "${node_tree}/lib/node_modules/npm/bin/npm-cli.js" --version)"
  [[ "${actual_node}" == "${expected_node}" ]] ||
    die "locked Node version mismatch: expected ${expected_node}, got ${actual_node}"
  [[ "${actual_npm}" == "${expected_npm}" ]] ||
    die "locked npm version mismatch: expected ${expected_npm}, got ${actual_npm}"
  mv -- "${node_tree}" "${target}"
  target_created=true
  installed_npm="$(PATH="${target}/bin:/usr/bin:/bin" \
    "${target}/bin/npm" --version)"
  [[ "${installed_npm}" == "${expected_npm}" ]] ||
    die "installed npm version mismatch: expected ${expected_npm}, got ${installed_npm}"
  persist_environment "${target}/bin"
  target_created=false
  printf 'installed locked Node/npm under %s\n' "${target}"
  ;;
qualification-go|extractor-go)
  target="${install_root}/go"
  go_purpose="qualification Go"
  if [[ "${mode}" == "extractor-go" ]]; then
    go_purpose="extractor Go"
  fi
  [[ ! -e "${target}" && ! -L "${target}" ]] ||
    die "${go_purpose} target already exists: ${target}"
  go_archive="${staging_dir}/go.tar.gz"
  go_parent="${staging_dir}/go-parent"
  verify_download "toolchains.go.${artifact_suffix}" "${go_archive}"
  mkdir -p -- "${go_parent}"
  tar -xzf "${go_archive}" -C "${go_parent}"
  [[ -x "${go_parent}/go/bin/go" ]] || die "locked Go extraction is incomplete"
  expected_go="$(lock_value toolchains.go.version_output)"
  actual_go="$("${go_parent}/go/bin/go" version)"
  read -r go_word version_word version_value go_platform extra <<< "${actual_go}"
  [[ -z "${extra:-}" ]] || die "unexpected locked Go version output: ${actual_go}"
  [[ "${go_word} ${version_word} ${version_value}" == "${expected_go}" ]] ||
    die "locked Go version mismatch: expected ${expected_go}, got ${actual_go}"
  [[ "${go_platform}" == "${expected_go_platform}" ]] ||
    die "locked Go platform mismatch: expected ${expected_go_platform}, got ${go_platform}"
  mv -- "${go_parent}/go" "${target}"
  target_created=true
  persist_environment "${target}/bin" "${target}/bin/go"
  target_created=false
  printf 'installed locked %s under %s\n' "${go_purpose}" "${target}"
  ;;
extractor-rust)
  target="${install_root}/rust"
  [[ ! -e "${target}" && ! -L "${target}" ]] ||
    die "extractor Rust target already exists: ${target}"
  rust_channel_manifest="${staging_dir}/rust-channel.toml"
  rust_archive="${staging_dir}/rust.tar.xz"
  rust_source="${staging_dir}/rust-source"
  verify_download "toolchains.rust.checksum_manifest" "${rust_channel_manifest}"
  "${qualification_python}" -I "${QUALIFICATION_HELPER}" verify-rust-manifest \
    --lock "${lock_path}" --manifest "${rust_channel_manifest}" \
    --target "${expected_rust_platform}"
  verify_download "${rust_artifact_key}" "${rust_archive}"
  mkdir -p -- "${rust_source}"
  tar -xJf "${rust_archive}" -C "${rust_source}" --strip-components=1
  [[ -x "${rust_source}/install.sh" ]] ||
    die "locked Rust extraction is incomplete"
  target_created=true
  "${rust_source}/install.sh" --prefix="${target}" --disable-ldconfig
  [[ -x "${target}/bin/cargo" && -x "${target}/bin/rustc" ]] ||
    die "locked Rust installation is incomplete"
  expected_cargo="$(lock_value toolchains.rust.version_output)"
  actual_cargo="$("${target}/bin/cargo" --version)"
  [[ "${actual_cargo}" == "${expected_cargo}" ]] ||
    die "locked Cargo version mismatch: expected ${expected_cargo}, got ${actual_cargo}"
  expected_rust_release="$(lock_value toolchains.rust.version)"
  actual_rust_metadata="$("${target}/bin/rustc" -vV)"
  actual_rust_platform=""
  actual_rust_release=""
  while IFS= read -r metadata_line; do
    case "${metadata_line}" in
      'host: '*)
        [[ -z "${actual_rust_platform}" ]] || die "duplicate locked Rust host metadata"
        actual_rust_platform="${metadata_line#host: }"
        ;;
      'release: '*)
        [[ -z "${actual_rust_release}" ]] || die "duplicate locked Rust release metadata"
        actual_rust_release="${metadata_line#release: }"
        ;;
    esac
  done <<< "${actual_rust_metadata}"
  [[ "${actual_rust_release}" == "${expected_rust_release}" ]] ||
    die "locked Rust version mismatch: expected ${expected_rust_release}, got ${actual_rust_release}"
  [[ "${actual_rust_platform}" == "${expected_rust_platform}" ]] ||
    die "locked Rust platform mismatch: expected ${expected_rust_platform}, got ${actual_rust_platform}"
  persist_environment "${target}/bin"
  target_created=false
  printf 'installed locked extractor Rust under %s\n' "${target}"
  ;;
extractor-haskell)
  target="${install_root}/haskell"
  [[ ! -e "${target}" && ! -L "${target}" ]] ||
    die "extractor Haskell target already exists: ${target}"
  ghc_archive="${staging_dir}/ghc.tar.xz"
  ghc_source="${staging_dir}/ghc-source"
  verify_download "toolchains.haskell.${artifact_suffix}" "${ghc_archive}"
  mkdir -p -- "${ghc_source}"
  tar -xJf "${ghc_archive}" -C "${ghc_source}" --strip-components=1
  [[ -x "${ghc_source}/configure" ]] ||
    die "locked GHC extraction is incomplete"
  target_created=true
  (
    cd -- "${ghc_source}"
    ./configure --prefix="${target}"
    make install
  )
  [[ -x "${target}/bin/ghc" ]] ||
    die "locked GHC installation is incomplete"
  expected_ghc="$(lock_value toolchains.haskell.version_output)"
  actual_ghc="$("${target}/bin/ghc" --numeric-version)"
  [[ "${actual_ghc}" == "${expected_ghc}" ]] ||
    die "locked GHC version mismatch: expected ${expected_ghc}, got ${actual_ghc}"
  actual_ghc_host="$("${target}/bin/ghc" --print-host-platform)"
  actual_ghc_target="$("${target}/bin/ghc" --print-target-platform)"
  [[ "${actual_ghc_host}" == "${expected_ghc_platform}" &&
     "${actual_ghc_target}" == "${expected_ghc_platform}" ]] ||
    die "locked GHC platform mismatch: expected ${expected_ghc_platform}, got host ${actual_ghc_host} and target ${actual_ghc_target}"
  persist_environment "${target}/bin" "" "${target}/bin/ghc"
  target_created=false
  printf 'installed locked extractor Haskell under %s\n' "${target}"
  ;;
esac
