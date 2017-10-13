#!/usr/bin/env bash

set -e -u

# Get script inputs
if [ "$#" -ne 2 ]; then
  echo "usage: $0 <sha_file> <output_file>"
  exit 1
fi
sha_file=$1
output_filepath=$2

sha=$(cat $sha_file | tr -d " \n\r")

# NOTE: `git config` does not normally pass through?... Why?
export GIT_CONFIG=~/.gitconfig

# TODO (jc) This should be obtain from the environment / settings
bg_remote=main
get_conf() {
    key=bazel-girder.${1}
    git config ${key} || { echo "Could not resolve 'git config ${key}'" >&2; exit 1; }
}
bg_remote=$(get_conf primary)
GIRDER_API_KEY=$(get_conf ${bg_remote}.api-key)
GIRDER_SERVER=$(get_conf ${bg_remote}.server)
GIRDER_API_ROOT=${GIRDER_SERVER}/api/v1

# Get token
girder_token=$(curl -L -s --data "key=${GIRDER_API_KEY}" \
  ${GIRDER_API_ROOT}/api_key/token | python -c 'import sys, json; print(json.load(sys.stdin)["authToken"]["token"])')

# Download file

# TODO(eric.cousineau): Check existing file system to see if this file already exists in the workspace root.
# TODO(eric.cousineau): Add option to check sha512 of the existing file. If it mathces, it's fine.
# Otherwise, it should print a message saying the file has changed, and how to revert this change (if they so desire).

curl -L --progress-bar -H "Girder-Token: ${girder_token}" -o ${output_filepath} -O ${GIRDER_API_ROOT}/file/hashsum/sha512/${sha}/download

# Test the SHA
set -x
sha512sum "$output_filepath"
sha_expected="${sha} ${output_filepath}"
set +x
echo ${sha_expected} | sha512sum -c --status || { echo "Bad checksum. Failing."; exit 1; }

# TODO(eric.cousineau): Implement simple caching: ~/.bazel-girder/sha512/{hash}
# TODO(eric.cousineau): Make this script be Python.
