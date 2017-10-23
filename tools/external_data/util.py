from __future__ import absolute_import, print_function
import os
import subprocess
import sys
import json
import time

# TODO(eric.cousineau): If `girder_client` is sufficiently lightweight, we can make this a proper Bazel
# dependency.
# If it's caching mechanism is efficient and robust against Bazel, we should use that as well.

cur_dir = os.path.dirname(__file__)

class _Config(object):
    def __init__(self, project_root, remote="master", mode='download'):
        d = self.__dict__

        self.project_root = project_root
        self._conf_exe = os.path.join(self.project_root, 'tools/external_data/girder/conf.sh')

        self.cache_dir = self._get_conf('core.cache-dir', os.path.expanduser("~/.cache/bazel-girder"))

        self.remote = remote
        self.server = self._get_conf('remote.{remote}.server'.format(**d))
        self.folder_id = self._get_conf('remote.{remote}.folder-id'.format(**d))
        self.api_url = "{server}/api/v1".format(**d)

        self.api_key = self._get_conf('server.{server}.api-key'.format(**d))
        token_raw = subshell("curl -L -s --data key={api_key} {api_url}/api_key/token".format(**d))
        self.token = json.loads(token_raw)["authToken"]["token"]

    def _get_conf(self, key, default=None):
        # TODO(eric.cousineau): 
        cmd = [self._conf_exe, key]
        if default:
            cmd.append(default)
        return subshell(cmd)


def get_all_conf(*args, **kwargs):
    return _Config(*args, **kwargs)


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


def find_project_root(start_dir):
    # Ideally, it'd be nice to just use `git rev-parse --show-top-level`.
    # However, because Bazel does symlink magic that is not easily parseable,
    # we should not rely on something like `symlink -f ${file}`, because
    # if a directory is symlink'd, then we will go to the wrong directory.
    # Instead, we should just do one `readlink` on `.project-root`, and expect
    # that it is not a link.
    # As an alternative, we could also use `.git`, but require that it either be
    # a file or a directory, but NOT a symlink.
    root_file = find_file_sentinel(start_dir, '.project-root')
    if os.path.islink(root_file):
        root_file = os.readlink(root_file)
        assert os.path.isabs(root_file)
        if os.path.islink(root_file):
            raise RuntimeError(".project-root should only have one level of an absolute-path symlink.")
    return os.path.dirname(root_file)

def parse_project_root_arg(project_root_arg):
    if project_root_arg == '[find]':
        project_root = find_project_root(os.getcwd())
    else:
        project_root = os.path.abspath(project_root_arg)
    assert os.path.isdir(project_root)
    return project_root


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

def find_file_sentinel(start_dir, sentinel_file, max_depth=6):
    cur_dir = start_dir
    assert len(cur_dir) > 0
    for i in xrange(max_depth):
        assert os.path.isdir(cur_dir)
        test_path = os.path.join(cur_dir, sentinel_file)
        if os.path.isfile(test_path):
            return test_path
        cur_dir = os.path.dirname(cur_dir)
        if len(cur_dir) == 0:
            break
    raise RuntimeError("Could not find project root")


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
