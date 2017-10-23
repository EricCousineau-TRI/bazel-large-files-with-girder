#!/usr/bin/env python

"""This script allows to upload data file revisoned based on a canonical path.
"""

from __future__ import absolute_import, print_function
import girder_client
import json
import os
import sys
import textwrap
import argparse

from datetime import datetime

assert __name__ == '__main__'

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from external_data import util

SHA_SUFFIX = '.sha512'

def upload(conf, filepath, do_cache):
    if not os.path.isabs(filepath):
        raise RuntimeError("Must supply absolute path: {}".format(filepath))
    filepath = os.path.abspath(filepath)
    if filepath.endswith(SHA_SUFFIX):
        filepath_guess = filepath[:-len(SHA_SUFFIX)]
        raise RuntimeError("Input file is a SHA file. Did you mean to upload '{}' instead?".format(filepath_guess))
    item_name = "%s %s" % (os.path.basename(filepath), datetime.utcnow().isoformat())

    versioned_filepath = os.path.relpath(filepath, conf.project_root)
    if versioned_filepath.startswith('..'):
        raise RuntimeError("File to upload, '{}', must be under '{}'".format(filepath, conf.project_root))

    sha = util.subshell(['sha512sum', filepath]).split(' ')[0]
    print("api_url ............: %s" % conf.api_url)
    print("folder_id ..........: %s" % conf.folder_id)
    print("filepath ...........: %s" % filepath)
    print("sha512 .............: %s" % sha)

    if not util.is_sha_uploaded(conf, sha):
        print("item_name ..........: %s" % item_name)
        print("project_root .......: %s" % conf.project_root)
        print("versioned_filepath .: %s" % versioned_filepath)
        ref = json.dumps({'versionedFilePath': versioned_filepath})

        gc = girder_client.GirderClient(apiUrl=conf.api_url)
        gc.authenticate(apiKey=conf.api_key)

        size = os.stat(filepath).st_size
        with open(filepath, 'rb') as fd:
            print("Uploading: {}".format(filepath))
            gc.uploadFile(conf.folder_id, fd, name=item_name, size=size, parentType='folder', reference=ref)
    else:
        # TODO(eric.cousineau): Check and ensure 
        print("File already uploaded")

    # Write SHA512
    sha_file = filepath + SHA_SUFFIX
    with open(sha_file, 'w') as fd:
        print("Updating sha file: {}".format(sha_file))
        fd.write(sha)

    # Place copy in cache.
    # @note This is purposely simpler than `download`s caching logic, so that developers can easily
    # test the round-trip experience without prematurely caching.
    # This will overwrite the cached, even if it already exists.
    if do_cache:
        cache_path = util.get_sha_cache_path(conf, sha, create_dir=True)
        print("Cache path: {}".format(cache_path))
        with util.FileWriteLock(cache_path):
            util.subshell(['cp', filepath, cache_path])
            # Make cache file read-only.
            util.subshell(['chmod', '-w', cache_path])

    print("[ Done ]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--do_cache', action='store_true')
    parser.add_argument('--project_root', type=str, default='[find]',
                        help='Project root. Can be "[find]" to find .project-root, or a relative or absolute directory.')
    parser.add_argument('filepath', type=str)
    args = parser.parse_args()
    project_root = util.parse_project_root_arg(args.project_root)

    conf = util.get_all_conf(project_root, mode='upload')
    upload(conf, args.filepath, args.do_cache)


if __name__ == '__main__':
    main()
