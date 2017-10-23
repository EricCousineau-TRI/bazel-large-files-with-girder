#!/usr/bin/env python

# @note This does not use `girder_client`, to minimize dependencies.
# @see util.py for more notes.

from __future__ import absolute_import, print_function
import sys
import os
import argparse

assert __name__ == '__main__'

# TODO(eric.cousineau): Make a `--quick` option to ignore checking SHA-512s, if the files are really large.

# TODO(eric.cousineau): Allow this to handle multiple files to download. Add a `--batch` argument, that will infer
# the output paths.

# TODO(eric.cousineau): Ensure that we do not need immediate authentication in configuration, e.g. when in road warrior mode.

parser = argparse.ArgumentParser()
parser.add_argument('--no_cache', action='store_true',
                    help='Always download, and do not cache the result.')
parser.add_argument('--use_cache_symlink', action='store_true',
                    help='Use this if you are confident that your test will not modify the data.')
parser.add_argument('--project_root', type=str, default='[find]',
                    help='Project root. Can be "[find]" to find .project-root, or a relative or absolute directory.')
parser.add_argument('--is_bazel_build', action='store_true',
                    help='If this is invoked via `macros.bzl`s `external_data`.')
parser.add_argument('-f,--force', action='store_true',
                    help='Overwrite existing output file if it already exists.')
parser.add_argument('sha_file', type=str,
                    help='File containing the SHA-512 of the desired contents.')
parser.add_argument('output_file', type=str,
                    help='Output destination.')

args = parser.parse_args()

# Hack to permit running from command-line easily.
# TODO(eric.cousineau): Require that this is only run from Bazel.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data import util

project_root = util.parse_project_root_arg(args.project_root)
# Get configuration.
conf = util.Config(project_root, mode='download')
pair = util.Bunch(output_file=args.output_file, sha_file=args.sha_file)

def do_download(pair):
    if not args.is_bazel_build:
        # Ensure that we have absolute file paths.
        files = [pair.sha_file, pair.output_file]
        if not all(map(os.path.isabs, files)):
            raise RuntimeError("Must specify absolute paths:\n  {}".format("\n".join(files)))

    # Ensure that we do not overwrite existing files.
    if os.path.isfile(pair.output_file):
        if not args.force:
            raise RuntimeError("Output file already exists (using `--force` to overwrite): {}".format(pair.output_file))

    # Get the sha.
    if not os.path.isfile(pair.sha_file):
        util.eprint("ERROR: File not found: {}".format(pair.sha_file))
        exit(1)
    sha = util.subshell("cat {}".format(pair.sha_file))
    use_cache = not args.no_cache

    # Common arguments for `format`.
    d = dict(conf=conf, pair=pair, sha=sha)

    def check_sha(throw_on_error=True):
        # Test the SHA.
        out = util.runc("sha512sum -c --status", input="{sha} {pair.output_file}".format(**d))
        if out[0] != 0 and throw_on_error:
            raise RuntimeError("SHA-512 mismatch")
        return out[0]

    def get_cached():
        # Can use cache. Copy to output path.
        print("Using cached file")
        if args.use_cache_symlink:
            util.subshell(['ln', '-s', cache_path, pair.output_file])
        else:
            util.subshell(['cp', cache_path, pair.output_file])
            util.subshell(['chmod', '+w', pair.output_file])
        # TODO(eric.cousineau): On error, remove cached file, and re-download.
        if check_sha(throw_on_error=False) != 0:
            util.eprint("SHA-512 mismatch. Removing old cached file, re-downloading.")
            # `os.remove()` will remove read-only files, reguardless.
            os.remove(cache_path)
            if os.path.islink(pair.output_file):
                # In this situation, the cache was corrupted (somehow), and Bazel
                # triggered a recompilation, and we still have a symlink in Bazel-space.
                # Remove this symlink, so that we do not download into a symlink (which
                # complicates the logic in `get_download_and_cache`). This also allows
                # us to "reset" permissions.
                os.remove(pair.output_file)
            get_download_and_cache()

    def get_download():
        # Defer authentication so that we can cache if necessary.
        conf.authenticate_if_needed()
        # TODO: Pipe progress bar and file name to stderr.
        util.subshell((
            'curl -L --progress-bar -H "Girder-Token: {conf.token}" ' +
            '-o {pair.output_file} -O {conf.api_url}/file/hashsum/sha512/{sha}/download'
        ).format(**d))
        check_sha()

    def get_download_and_cache():
        with util.FileWriteLock(cache_path):
            get_download()
            # Place in cache directory.
            if args.use_cache_symlink:
                # Hot-swap the freshly downloaded file.
                util.subshell(['mv', pair.output_file, cache_path])
                util.subshell(['ln', '-s', cache_path, pair.output_file])
            else:
                util.subshell(['cp', pair.output_file, cache_path])
                util.subshell(['chmod', '+w', pair.output_file])
            # Make cache file read-only.
            util.subshell(['chmod', '-w', cache_path])

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

do_download(pair)
