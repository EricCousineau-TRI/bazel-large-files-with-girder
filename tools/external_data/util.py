from __future__ import absolute_import, print_function
import os
import subprocess
import sys

cur_dir = os.path.dirname(__file__)

conf_exe = os.path.join(cur_dir, 'girder', 'conf.sh')

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


def get_conf(key, default=None):
    cmd = [conf_exe, key]
    if default:
        cmd.append(default)
    return subshell(cmd)


def sha_exists(api_url, sha):
    """ Returns true if the given SHA exists on the given server. """
    # TODO(eric.cousineau): Check `folder_id` and ensure it lives in the same place?
    # This is necessary if we have users with the same file?
    # What about authentication? Optional authentication / public access?

    # TODO(eric.cousineau): Check if the file has already been uploaded.
    # @note `curl --head ${url}` will fetch the header only.
    # TODO(eric.cousineau): Get token?
    url = "{api_url}/file/hashsum/sha512/{sha}/download".format(api_url=api_url, sha=sha)
    first_line = subshell("curl -s --head '{}' | head -n 1".format(url))
    print(first_line)
    if first_line == "HTTP/1.1 404 Not Found":
        return False
    elif first_line == "HTTP/1.1 303 See Other":
        return True
    else:
        raise RuntimeError("Unknown response: {}".format(first_line))

def eprint(*args):
    print(*args, file=sys.stderr)
