#!/bin/bash
# Round-7 isolation wrapper (release copy, paths generalized): new user+net+mount namespace; no network;
# $HOME hidden behind an empty tmpfs (only the read-only Python install PYROOT is re-exposed); runs in the
# given throwaway work dir. Must live OUTSIDE $HOME (r7_validity.py uses $R7_SANDBOX, default /tmp/r7sandbox).
# usage: sandbox.sh <workdir> <cmd...>     env: PYROOT (default $HOME/miniconda3)
SB="$(cd "$(dirname "$0")" && pwd)"
PYROOT="${PYROOT:-$HOME/miniconda3}"
mkdir -p "$SB/mc"
exec unshare -rnm bash -c '
set -e
SB="$1"; WD="$2"; PYROOT="$3"; H="$4"; shift 4
mount --bind "$PYROOT" "$SB/mc"
mount -t tmpfs -o size=16m tmpfs "$H"
mkdir -p "$PYROOT"
mount --bind "$SB/mc" "$PYROOT"
mount -o remount,bind,ro "$PYROOT"
cd "$WD"
export HOME="$WD"
exec "$@"' bash "$SB" "$1" "$PYROOT" "$HOME" "${@:2}"
