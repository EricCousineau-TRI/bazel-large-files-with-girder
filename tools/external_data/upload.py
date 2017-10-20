#!/usr/bin/env python

"""This script allows to upload data file revisoned based on a canonical path.
"""

from __future__ import absolute_import, print_function
import girder_client
import json
import os
import sys
import textwrap

from datetime import datetime

from .util import subshell, get_conf, sha_exists

cur_dir = os.path.dirname(__file__)
project_root = os.path.join(cur_dir, "..")


def upload(server, api_key, folder_id, project_root, filepath):
    api_url = "%s/api/v1" % server
    filepath = os.path.abspath(filepath)
    versioned_filepath = os.path.relpath(filepath, project_root)
    item_name = "%s %s" % (os.path.basename(filepath), datetime.utcnow().isoformat())

    print("api_url ............: %s" % api_url)
    print("folder_id ..........: %s" % folder_id)
    print("filepath ...........: %s" % filepath)
    print("item_name ..........: %s" % item_name)
    print("project_root .......: %s" % project_root)
    print("versioned_filepath .: %s" % versioned_filepath)

    sha = subshell(['sha512sum', filepath]).split(' ')[0]
    print("sha512 .............: %s" % sha)

    if not _sha_exists(api_url, sha):
        gc = girder_client.GirderClient(apiUrl=api_url)

        gc.authenticate(apiKey=api_key)

        ref = json.dumps({'versionedFilePath': versioned_filepath})

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

    # TODO(eric.cousineau): Place this in the cache, if enabled.

    print("[ Done ]")


def display_usage():
    print(textwrap.dedent(
        """
        usage:

          %s /path/to/filename

        """ % os.path.basename(__file__)))


def display_error(text):
    print("\nerror: %s" % text)
    display_usage()


def main():
    remote = get_conf('.remote-master', "master")
    server = get_conf('-remote.{}.url'.format(remote))
    folder_id = get_conf('-remote.{}.folder-id'.format(remote))
    api_key = get_conf('-auth.{}.api-key'.format(server))

    if len(sys.argv) != 2:
        display_error("'/path/to/filename' is not specified")
        sys.exit(1)

    # TODO(eric.cousineau): Use `bazel info workspace`?
    filepath = sys.argv[1]

    upload(server, api_key, folder_id, project_root, filepath)


if __name__ == '__main__':
    main()
