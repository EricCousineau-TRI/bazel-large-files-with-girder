#!/bin/bash
set -e -u

# Download a set of files given a glob containing `*.sha512` files into the workspace.

# TODO(eric.cousineau): Add some other quick utilities to list things. Put this into Python.
sha_files="$@"
for sha_file in ${sha_files}; do
    if [[ ${sha_file} =~ ^(.*)\.sha512$ ]]; then
        out_file=${BASH_REMATCH[1]}
        bazel run //tools/external_data:download -- ${sha_file} ${out_file}
    else
        echo "File does not end in "'*.sha512'": '${sha_file}'" >&2
        exit 1
    fi
done
