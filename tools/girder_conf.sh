#!/bin/bash
set -e -u

cur_dir=$(cd $(dirname $0) && pwd)
repo_conf=${cur_dir}/girder.gitconfig

verbose=1

eecho() { echo "$@" >&2; }

get_conf() {
    key=bazel-girder.${1}
    default=${2-}
    if ! git config ${key}; then
        # Attempt to use repostiory local configuration.
        if ! git config -f ${repo_conf} ${key}; then
            # Use default
            if [[ -n ${default} ]]; then
                [[ -n ${verbose} ]] && eecho "Use default"
                echo ${default};
            else
                eecho "Could not resolve 'git config ${key}'"
                exit 1
            fi
        else
            [[ -n ${verbose} ]] && eecho "Use ${repo_conf}"
        fi
    else
        [[ -n ${verbose} ]] && eecho "Use git config"
    fi
}

get_conf "$@"
