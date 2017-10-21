from __future__ import absolute_import, print_function
import os
import subprocess
import sys
import json
import time

cur_dir = os.path.dirname(__file__)

conf_exe = os.path.join(cur_dir, 'girder', 'conf.sh')

class _Config(object):
    def __init__(self, remote="master", do_auth=False):
        d = self.__dict__

        self.remote = remote
        self.server = _get_conf('remote.{remote}.server'.format(**d))
        self.folder_id = _get_conf('remote.{remote}.folder-id'.format(**d))
        self.api_url = "{server}/api/v1".format(**d)
        self.cache_dir = _get_conf('core.cache-dir', os.path.expanduser("~/.cache/bazel-girder"))

        # For now, disable project root stuff.
        # TODO(eric.cousineau): Figure out how to robustly determine this, especially when running
        # `upload.py` from Bazel.
        self.project_root = None

        if do_auth:
            self.api_key = _get_conf('server.{server}.api-key'.format(**d))
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
    url = "{conf.api_url}/file/hashsum/sha512/{sha}/download".format(conf=conf, sha=sha)
    first_line = subshell(
        'curl -s -H "Girder-Token: {conf.token}" --head "{url}" | head -n 1'.format(conf=conf, url=url))
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

def _lock_path(filepath):
    return filepath + ".lock"

def wait_file_read_lock(filepath, timeout=60):
    timeout = 60
    lock = _lock_path(filepath)
    if os.path.isfile(lock):
        now = time.time()
        while os.path.isfile(lock):
            time.sleep(0.1)
            elapsed = time.time() - now
            if elapsed > timeout:
                raise RuntimeError()

class FileWriteLock(object):
    def __init__(self, filepath):
        self.lock = _lock_path(filepath)
    def __enter__(self):
        if os.path.isfile(self.lock):
            raise RuntimeError("Lock already acquired? {}".format(self.lock))
        # Touch the file.
        with open(self.lock, 'w') as f:
            pass
    def __exit__(self, *args):
        assert os.path.isfile(self.lock)
        os.remove(self.lock)

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


def runc(cmd, input):
    PIPE = subprocess.PIPE
    p = subprocess.Popen(cmd, shell=isinstance(cmd, str), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(input)
    return (p.returncode, output, err)

def run(cmd, input):
    out = run(cmd, input)
    if out[0] != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, err)

def eprint(*args):
    print(*args, file=sys.stderr)
