#!/usr/bin/env python

# @note This does not use `girder_client`, to minimize dependencies.

from __future__ import absolute_import, print_function
import sys
import os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--no_cache', action='store_true')
parser.add_argument('sha_file', type=str)
parser.add_argument('output_file', type=str)

args = parser.parse_args()

# files = [args.sha_file, args.output_file]
# if not all(map(os.path.isabs, files)):
#     raise RuntimeError("Must specify absolute paths:\n  {}".format("\n".join(files)))

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data.util import run, subshell, get_all_conf, eprint

sha = subshell("cat {}".format(args.sha_file))

d = locals()
conf = get_all_conf(do_auth=True)
# TODO: Pipe progress bar and file name to stderr.
subshell((
    'curl -L --progress-bar -H "Girder-Token: {conf.token}" ' +
    '-o {args.output_file} -O {conf.api_url}/file/hashsum/sha512/{sha}/download'
).format(**d))

# Test the SHA.
run("sha512sum -c --status", input="{sha} {args.output_file}".format(**d))

# TODO: Place in cache directory.
