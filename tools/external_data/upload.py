#!/usr/bin/env python

"""This script allows to upload data file revisoned based on a canonical path.
"""

from __future__ import absolute_import, print_function
import girder_client
import os
import sys
import textwrap
import argparse

from datetime import datetime

cur_dir = os.path.dirname(__file__)
import .util


def upload(conf, filepath, do_cache):
    filepath = os.path.abspath(filepath)
    item_name = "%s %s" % (os.path.basename(filepath), datetime.utcnow().isoformat())

    print("api_url ............: %s" % conf.api_url)
    print("folder_id ..........: %s" % conf.folder_id)
    print("filepath ...........: %s" % filepath)
    print("item_name ..........: %s" % item_name)

    sha = util.subshell(['sha512sum', filepath]).split(' ')[0]
    print("sha512 .............: %s" % sha)

    if not util.is_sha_uploaded(conf, sha):
        gc = girder_client.GirderClient(apiUrl=conf.api_url)
        gc.authenticate(apiKey=conf.api_key)

        size = os.stat(filepath).st_size
        with open(filepath, 'rb') as fd:
            print("Uploading: {}".format(filepath))
            gc.uploadFile(folder_id, fd, name=item_name, size=size, parentType='folder', reference=ref)
    else:
        print("File already uploaded")

    # Write SHA512
    sha_file = filepath + '.sha512'
    with open(sha_file, 'w') as fd:
        print("Updating sha file: {}".format(sha_file))
        fd.write(sha)

    # Place copy in cache.
    if do_cache:
        cache_path = util.get_sha_cache_path(conf, sha, create_dir=True)
        print("Cache path: {}".format(cache_path))
        subshell(['cp', filepath, cache_path])

    print("[ Done ]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--do_cache', type='store_true')
    parser.add_argument('filepath', type=str)
    args = parser.parse_args()

    conf = get_all_conf(do_auth=True)
    upload(conf, args.filepath, args.do_cache)


if __name__ == '__main__':
    main()
