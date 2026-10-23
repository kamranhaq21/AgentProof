#!/usr/bin/env bash
# Print the version packages/python/pyproject.toml declares: the one `version = "..."`
# line at the top of the file, without its quotes, and nothing else. CI's `smoke` job and
# the release-draft workflow both compare it with something (the installed CLI's version
# line, the pushed tag), so the extraction lives here once. Carriage returns are stripped
# first because the Windows checkout normalises pyproject.toml to CRLF. Prints nothing
# when there is no such line; callers treat an empty result as a failure.
tr -d '\r' < "$(dirname "$0")/../../packages/python/pyproject.toml" | sed -nE 's/^version = "([^"]*)"$/\1/p'
