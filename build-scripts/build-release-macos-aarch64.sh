#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COINSWAP_PY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$COINSWAP_PY_DIR/src/coinswap"
FFI_REPO="https://github.com/citadel-tech/coinswap-ffi.git"
FFI_DIR="/tmp/coinswap-ffi"

COMPILATION_TARGET="aarch64-apple-darwin"
LIB_NAME="libcoinswap_ffi.dylib"

echo "Building for target: $COMPILATION_TARGET"

if [ ! -d "$FFI_DIR/.git" ]; then
	rm -rf "$FFI_DIR"
	git clone --depth 1 "$FFI_REPO" "$FFI_DIR"
fi

cd "$FFI_DIR/ffi-commons" || exit
rustup target add $COMPILATION_TARGET

# Build the library
cargo build --profile release-smaller --target $COMPILATION_TARGET

mkdir -p "$PACKAGE_DIR"
cp ./target/$COMPILATION_TARGET/release-smaller/$LIB_NAME "$PACKAGE_DIR/"
cp ./target/$COMPILATION_TARGET/release-smaller/uniffi-bindgen "$PACKAGE_DIR/"
cargo run --bin uniffi-bindgen generate --library ./target/$COMPILATION_TARGET/release-smaller/$LIB_NAME --language python --out-dir "$PACKAGE_DIR" --no-format

echo "  Bindings: coinswap-python/src/coinswap/coinswap.py"
echo "✓ Build completed for $COMPILATION_TARGET"
echo "  Binary: coinswap-python/src/coinswap/$LIB_NAME"
