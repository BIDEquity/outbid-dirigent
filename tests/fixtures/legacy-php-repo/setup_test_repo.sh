#!/bin/bash
# Creates a temporary git repo from this fixture for smoke testing.
# Usage: REPO_DIR=$(./setup_test_repo.sh)

set -e

FIXTURE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR=$(mktemp -d)/legacy-php-kontakt
mkdir -p "$REPO_DIR"

# Copy all PHP files
cp "$FIXTURE_DIR"/index.php "$REPO_DIR/"
cp "$FIXTURE_DIR"/config.php "$REPO_DIR/"
cp "$FIXTURE_DIR"/admin.php "$REPO_DIR/"
cp "$FIXTURE_DIR"/schema.sql "$REPO_DIR/"
mkdir -p "$REPO_DIR/lib"
cp "$FIXTURE_DIR"/lib/*.php "$REPO_DIR/lib/"

# Init git with old commits to trigger legacy detection (suppress git output)
cd "$REPO_DIR"
git init -q
git config user.email "dev@example.com"
git config user.name "Legacy Dev"

git add . && git commit -q -m "Initial commit: PHP Kontaktformular" --date="2023-01-15T10:00:00"

echo "/* v1.1 */" >> index.php
git add . && git commit -q -m "feat: add priority field" --date="2023-03-20T10:00:00"

echo "/* v1.2 */" >> lib/validation.php
git add . && git commit -q -m "fix: validate email domains" --date="2023-06-01T10:00:00"

echo "/* v1.3 */" >> admin.php
git add . && git commit -q -m "feat: admin status management" --date="2023-09-15T10:00:00"

# Copy spec (not committed — it's the migration request)
cp "$FIXTURE_DIR"/SPEC.md "$REPO_DIR/"

echo "$REPO_DIR"
