#!/usr/bin/env bash

set -e -u -x

cur_dir=$(cd $(dirname $0) && pwd)

# Get script inputs
if [ "$#" -ne 2 ]; then
  echo "usage: $0 <sha_file> <output_file>"
  exit 1
fi
sha_file=$1
output_filepath=$2

sha=$(cat $sha_file | tr -d " \n\r")

# TODO (jc) This should be obtain from the environment / settings
bg_remote=main
get_conf() {
    ${cur_dir}/girder_conf.sh "$@" || exit 1
}
bg_remote=$(get_conf .remote-master "master")
bg_cache=$(get_conf .cache-dir "~/.cache/bazel-girder")

echo "${bg_cache}" >&2
GIRDER_SERVER=$(get_conf -remote."${bg_remote}".url)
# TODO(eric.cousineau): Is there a way to do this without required authentication?
GIRDER_API_KEY=$(get_conf -auth."${GIRDER_SERVER}".api-key)
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

# TODO(eric.cousineau): Implement simple caching: ~/.bazel-girder/sha512/{hash} - or use GIT_CONIG, bazel-girder.cache-dir
# TODO(eric.cousineau): Make this script be Python.
