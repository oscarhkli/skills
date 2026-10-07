#!/usr/bin/env bash
# Usage: scripts/install.sh [-y]    (-y: replace changed skills without asking)
set -euo pipefail

assume_yes=false
[ "${1:-}" = "-y" ] && assume_yes=true

src="$(cd "$(dirname "$0")/.." && pwd)/skills"
dst="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
backup="$(dirname "$dst")/.skills-backup/$(date +%Y%m%d-%H%M%S)"
diff_opts=(-r -x .DS_Store -x __pycache__)
mkdir -p "$dst"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

stage_skill() {
  rm -rf "${stage:?}/$1"
  cp -R "$src/$1" "$stage/$1"
  rm -rf "$stage/$1/evals"
  find "$stage/$1" \( -name .DS_Store -o -name __pycache__ \) -prune -exec rm -rf {} +
}

deploy() {
  rm -rf "${dst:?}/$1"
  cp -R "$stage/$1" "$dst/$1"
}

for skill in "$src"/*/; do
  name="$(basename "$skill")"
  target="$dst/$name"
  stage_skill "$name"

  if [ ! -e "$target" ]; then
    deploy "$name"
    echo "installed  $name"
    continue
  fi

  if diff -q "${diff_opts[@]}" "$stage/$name" "$target" >/dev/null 2>&1; then
    echo "up-to-date $name"
    continue
  fi

  echo "differs    $name"
  diff "${diff_opts[@]}" -u "$target" "$stage/$name" | sed 's/^/  /' || true

  reply=y
  if [ "$assume_yes" = false ]; then
    read -r -p "Replace deployed '$name' with the repo version? [y/N/a=all remaining] " reply </dev/tty
    case "$reply" in [aA]*) assume_yes=true ;; esac
  fi
  case "$reply" in
    [yYaA]*)
      mkdir -p "$backup"
      mv "$target" "$backup/$name"
      deploy "$name"
      echo "replaced   $name (old copy: $backup/$name)"
      ;;
    *) echo "skipped    $name" ;;
  esac
done
