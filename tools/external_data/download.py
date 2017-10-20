#!/usr/bin/env python

# @note This does not use `girder_client`, to minimize dependencies.

from __future__ import absolute_import, print_function
import sys
import os
import argparse
import json
from subprocess import Popen, PIPE

parser = argparse.ArgumentParser()
parser.add_argument('--no_cache', action='store_true')
parser.add_argument('sha_file', type=str)
parser.add_argument('output_file', type=str)

args = parser.parse_args()

# files = [args.sha_file, args.output_file]
# if not all(map(os.path.isabs, files)):
#     raise RuntimeError("Must specify absolute paths:\n  {}".format("\n".join(files)))

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data.util import run, subshell, get_conf, eprint

sha = subshell("cat {}".format(args.sha_file))

remote = get_conf('.remote-master', 'master')
# cache_dir = get_conf('.cache-dir', os.path.expanduser("~/.cache/bazel-girder"))
server = get_conf('-remote.{}.url'.format(remote))
folder_id = get_conf('-remote.{}.folder-id'.format(remote))
api_key = get_conf('-auth.{}.api-key'.format(server))

api_url = "%s/api/v1" % server

token_raw = subshell("curl -L -s --data key={api_key} {api_url}/api_key/token".format(**locals()))
token = json.loads(token_raw)["authToken"]["token"]

subshell((
    'curl -L --progress-bar -H "Girder-Token: {token}" ' +
    '-o {args.output_file} -O {api_url}/file/hashsum/sha512/{sha}/download'
).format(**locals()))

# Test the SHA.
run("sha512sum -c --status", input="{sha} {args.output_file}".format(**locals()))

# TODO: Place in cache directory.
