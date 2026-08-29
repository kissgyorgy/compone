#!/usr/bin/env bash
set -euo pipefail

if (($# == 0)); then
	echo "Usage: $0 WHEEL [...]" >&2
	exit 2
fi

for wheel in "$@"; do
	entries=$(unzip -Z1 "$wheel")

	if python_files=$(rg '\.pyi?$' <<<"$entries"); then
		echo "$wheel contains Python files:" >&2
		echo "$python_files" >&2
		exit 1
	fi

	mapfile -t payload < <(rg -v '/$|^[^/]+\.dist-info/' <<<"$entries")
	if ((${#payload[@]} != 1)) || [[ ! "${payload[0]}" =~ ^compone(\.[^.]+)*\.(so|pyd)$ ]]; then
		echo "$wheel has unexpected non-metadata payload:" >&2
		printf '%s\n' "${payload[@]}" >&2
		exit 1
	fi

done
