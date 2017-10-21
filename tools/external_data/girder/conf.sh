#!/bin/bash
set -e -u

cur_dir=$(cd $(dirname $0) && pwd)
verbose=

repo_conf=${cur_dir}/girder.gitconfig
user_conf=~/.girder.gitconfig

eecho() { echo "$@" >&2; }
debug() { [[ -n ${verbose} ]] && eecho "$@" || :; }

get_conf() {
    key=${1}
    default=${2-}
    if git config -f ${repo_conf} ${key}; then
        debug "Use repo: ${repo_conf}"
    elif git config -f ${user_conf} ${key}; then
        debug "Use user: ${user_conf}"
    elif [[ -n ${default} ]]; then
        echo ${default}
        debug "Use default"
    else
        eecho "Could not resolve key: ${key}"
        exit 1
    fi
}

get_conf "$@"
