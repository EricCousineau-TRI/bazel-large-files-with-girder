#!/usr/bin/env python

# @note This does not use `girder_client`, to minimize dependencies.

from __future__ import absolute_import, print_function
import sys
import os
import argparse

# This hurts Bazel workflows. Need to figure out how to make this work better...
NEED_ABS = False

parser = argparse.ArgumentParser()
parser.add_argument('--no_cache', action='store_true')
parser.add_argument('sha_file', type=str)
parser.add_argument('output_file', type=str)

args = parser.parse_args()

if NEED_ABS:
    files = [args.sha_file, args.output_file]
    if not all(map(os.path.isabs, files)):
        raise RuntimeError("Must specify absolute paths:\n  {}".format("\n".join(files)))

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data import util

sha = util.subshell("cat {}".format(args.sha_file))

conf = util.get_all_conf(do_auth=True)
cache_path = util.get_sha_cache_path(conf, sha, create_dir=True)

d = dict(args=args, conf=conf, sha=sha)

# Check if we need to download.
is_cached = False
if os.path.isfile(cache_path):
    # Can use cache. Copy to output path.
    is_cached = True
    print("Using cached file")
    util.subshell(['cp', cache_path, args.output_file])
else:
    # TODO: Pipe progress bar and file name to stderr.
    util.subshell((
        'curl -L --progress-bar -H "Girder-Token: {conf.token}" ' +
        '-o {args.output_file} -O {conf.api_url}/file/hashsum/sha512/{sha}/download'
    ).format(**d))

# Test the SHA.
util.run("sha512sum -c --status", input="{sha} {args.output_file}".format(**d))

# Place in cache directory.
if not is_cached:
    util.subshell(['cp', args.output_file, cache_path])
