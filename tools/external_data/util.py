from __future__ import absolute_import, print_function
import os
import subprocess
import sys
import json

cur_dir = os.path.dirname(__file__)

conf_exe = os.path.join(cur_dir, 'girder', 'conf.sh')

class _Config(object):
    def __init__(self, remote="master", do_auth=False):
        d = self.__dict__
        # For now, disable project root stuff.
        self.project_root = None
        self.remote = remote
        self.server = _get_conf('-remote.{remote}.url'.format(**d))
        self.folder_id = _get_conf('-remote.{remote}.folder-id'.format(**d))
        self.api_url = "{server}/api/v1".format(**d)
        self.cache_dir = _get_conf('.cache-dir', os.path.expanduser("~/.cache/bazel-girder"))

        if do_auth:
            self.api_key = _get_conf('-auth.{server}.api-key'.format(**d))
            token_raw = subshell("curl -L -s --data key={api_key} {api_url}/api_key/token".format(**d))
            self.token = json.loads(token_raw)["authToken"]["token"]


def get_all_conf(**kwargs):
    return _Config(**kwargs)

def _get_conf(key, default=None):
    cmd = [conf_exe, key]
    if default:
        cmd.append(default)
    return subshell(cmd)


def is_sha_uploaded(conf, sha):
    """ Returns true if the given SHA exists on the given server. """
    # TODO(eric.cousineau): Check `folder_id` and ensure it lives in the same place?
    # This is necessary if we have users with the same file?
    # What about authentication? Optional authentication / public access?

    # TODO(eric.cousineau): Check if the file has already been uploaded.
    # @note `curl --head ${url}` will fetch the header only.
    # TODO(eric.cousineau): Get token?
    url = "{api_url}/file/hashsum/sha512/{sha}/download".format(sha=sha, **conf.__dict__)
    first_line = subshell("curl -s --head '{}' | head -n 1".format(url))
    print(first_line)
    if first_line == "HTTP/1.1 404 Not Found":
        return False
    elif first_line == "HTTP/1.1 303 See Other":
        return True
    else:
        raise RuntimeError("Unknown response: {}".format(first_line))


def get_sha_cache_path(conf, sha, create_dir=False):
    a = sha[0:2]
    b = sha[2:4]
    out_dir = os.path.join(conf.cache_dir, a, b)
    if create_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    return os.path.join(out_dir, sha)


# --- General Utilities ---

def subshell(cmd, strip=True):
    output = subprocess.check_output(cmd, shell=isinstance(cmd, str))
    if strip:
        return output.strip()
    else:
        return output

def subshellc(cmd, strip=True):
    try:
        return subshell(cmd, strip)
    except subprocess.CalledProcessError as e:
        return None


def run(cmd, input, strip=True):
    PIPE = subprocess.PIPE
    p = subprocess.Popen(cmd, shell=isinstance(cmd, str), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(input)
    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, err)
    if strip:
        return output.strip()
    else:
        return output

def runc(cmd, input, strip=True):
    try:
        return run(cmd, input, strip)
    except subprocess.CalledProcessError as e:
        return None

def eprint(*args):
    print(*args, file=sys.stderr)
