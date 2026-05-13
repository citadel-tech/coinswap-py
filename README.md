# Coinswap Python

Python scaffolding for Coinswap.

## Run Qt Scaffolding App

```bash
# from the repository root
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ./coinswap-python/requirements.txt
python -m pip install -e ./coinswap-python

coinswap-qt
```

This opens a basic Qt window with:

`Coinswap Python Scaffolding here`

```bash
python -m coinswap.qt_app
```

## Build Release Artifacts

Use the arch-specific release scripts from `build-scripts/`.

```bash
# Linux targets
bash ./build-scripts/build-release-linux-x86_64.sh
bash ./build-scripts/build-release-linux-aarch64.sh

# macOS targets
bash ./build-scripts/build-release-macos-x86_64.sh
bash ./build-scripts/build-release-macos-aarch64.sh
```

## Docker Test Stack

The Docker setup script is for local testing only. It pulls the Coinswap repo for Docker images, builds the stack, and starts the regtest services.

```bash
bash ./ffi-docker-setup setup
bash ./ffi-docker-setup start

# optional helpers
bash ./ffi-docker-setup status
bash ./ffi-docker-setup logs
bash ./ffi-docker-setup stop
```
