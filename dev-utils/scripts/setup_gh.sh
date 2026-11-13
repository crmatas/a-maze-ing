#!/usr/bin/env bash

set -euo pipefail

install_dir="$HOME/.local/bin"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

case "$(uname -m)" in
    x86_64)
        gh_arch="amd64"
        ;;
    aarch64|arm64)
        gh_arch="arm64"
        ;;
    *)
        echo "Arquitectura no soportada: $(uname -m)" >&2
        exit 1
        ;;
esac

version="$(
    curl -fsSL https://api.github.com/repos/cli/cli/releases/latest |
        sed -n 's/.*"tag_name": "v\([^"]*\)".*/\1/p' |
        head -n 1
)"

if [[ -z "$version" ]]; then
    echo "No se pudo determinar la versión de GitHub CLI." >&2
    exit 1
fi

archive="gh_${version}_linux_${gh_arch}.tar.gz"
url="https://github.com/cli/cli/releases/download/v${version}/${archive}"

mkdir -p "$install_dir"
curl -fsSL -o "$tmp_dir/$archive" "$url"
tar -xzf "$tmp_dir/$archive" -C "$tmp_dir"
install -Dm755 \
    "$tmp_dir/gh_${version}_linux_${gh_arch}/bin/gh" \
    "$install_dir/gh"

echo "GitHub CLI $version instalado en $install_dir/gh"
