#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
CLI_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${CLI_ROOT}/build/output"

TARGET="${1:-current}"

usage() {
  cat <<'EOF'
Usage:
  ./builds/build.sh [current|all|clean]

Targets:
  current   Build for current host platform (default)
  all       Build for linux/darwin/windows amd64+arm64
  clean     Remove build artifacts from build/output
EOF
}

build_target() {
  goos="$1"
  goarch="$2"
  ext=""
  if [ "$goos" = "windows" ]; then
    ext=".exe"
  fi

  out="${OUTPUT_DIR}/neurograph-${goos}-${goarch}${ext}"
  echo "Building ${goos}/${goarch} -> ${out}"
  (
    cd "${CLI_ROOT}"
    GOOS="${goos}" GOARCH="${goarch}" CGO_ENABLED=0 \
      go build -trimpath -ldflags "-s -w" -o "${out}" ./cmd/neurograph
  )
}

build_current() {
  goos="$(go env GOOS)"
  goarch="$(go env GOARCH)"
  build_target "${goos}" "${goarch}"
}

build_all() {
  build_target linux amd64
  build_target linux arm64
  build_target darwin amd64
  build_target darwin arm64
  build_target windows amd64
  build_target windows arm64
}

mkdir -p "${OUTPUT_DIR}"

case "${TARGET}" in
  current)
    build_current
    ;;
  all)
    build_all
    ;;
  clean)
    rm -rf -- "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"
    echo "Cleaned ${OUTPUT_DIR}"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown target: ${TARGET}" >&2
    usage >&2
    exit 1
    ;;
esac

echo "Build artifacts are in: ${OUTPUT_DIR}"

if [ -n "${WSL_DISTRO_NAME:-}" ]; then
  echo "Note: running under WSL requires Go to be installed in WSL for sh builds."
fi
