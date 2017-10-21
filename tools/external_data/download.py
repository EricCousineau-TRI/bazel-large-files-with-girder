#!/usr/bin/env python

# @note This does not use `girder_client`, to minimize dependencies.

from __future__ import absolute_import, print_function
import sys
import os
import argparse

# TODO(eric.cousineau): This hurts `bazel build` workflows... Need to figure out how to make this work better.
NEED_ABSPATH = False

parser = argparse.ArgumentParser()
parser.add_argument('--no_cache', action='store_true',
                    help='Always download, and do not cache the result.')
parser.add_argument('--use_cache_symlink', action='store_true',
                    help='Use this if you are confident that your test will not modify the data.')
parser.add_argument('sha_file', type=str,
                    help='File containing the SHA-512 of the desired contents.')
parser.add_argument('output_file', type=str,
                    help='Output destination.')

args = parser.parse_args()

if NEED_ABSPATH:
    files = [args.sha_file, args.output_file]
    if not all(map(os.path.isabs, files)):
        raise RuntimeError("Must specify absolute paths:\n  {}".format("\n".join(files)))

# Hack to permit running from command-line easily.
# TODO
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data import util

# Get configuration.
conf = util.get_all_conf(do_auth=True)

# Get the sha.
sha = util.subshell("cat {}".format(args.sha_file))
use_cache = not args.no_cache

# Common arguments for `format`.
d = dict(args=args, conf=conf, sha=sha)

def check_sha():
    # Test the SHA.
    util.run("sha512sum -c --status", input="{sha} {args.output_file}".format(**d))

def get_cached():
    # Can use cache. Copy to output path.
    print("Using cached file")
    if args.use_symlink:
        util.subshell(['ln', '-s', cache_path, args.output_file])
    else:
        util.subshell(['cp', cache_path, args.output_file])
    # TODO(eric.cousineau): On error, remove cached file, and re-download.
    check_sha()

def get_download():
    # TODO: Pipe progress bar and file name to stderr.
    util.subshell((
        'curl -L --progress-bar -H "Girder-Token: {conf.token}" ' +
        '-o {args.output_file} -O {conf.api_url}/file/hashsum/sha512/{sha}/download'
    ).format(**d))
    check_sha()

def get_download_and_cache():
    with util.FileWriteLock(cache_path):
        get_download()
        # Place in cache directory.
        if args.use_symlink:
            # Hot-swap.
            util.subshell(['mv', args.output_file, cache_path])
            util.subshell(['ln', '-s', cache_path, args.output_file])
        else:
            util.subshell(['cp', args.output_file, cache_path])
        # Make read-only.
        subshell(['chmod', '-w', cache_path])

# Check if we need to download.
if use_cache:
    cache_path = util.get_sha_cache_path(conf, sha, create_dir=True)

    util.wait_file_read_lock(cache_path)
    if os.path.isfile(cache_path):
        get_cached()
    else:
        get_download_and_cache()
else:
    get_download()
