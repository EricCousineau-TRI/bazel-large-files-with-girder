ENABLE_WARN = True
VERBOSE = False

SHA_SUFFIX = ".sha512"

def external_data(file, mode='normal'):
    """
    Macro for defining a large file.

    file: Name of the file to be downloaded.
    mode:
        'normal' - Use cached file if possible. Otherwise download the file.
        'devel' - Use local workspace (for development).
        'no_cache' - Download the file, do not use the cache.
    """

    # Cannot access environment for this file...
    # Use this?
    # https://docs.bazel.build/versions/master/skylark/lib/actions.html#run_shell
    # Nope. Only allows using existing PATH / LD_LIBRARY_PATH or not.

    if mode == 'devel':
        # TODO(eric.cousineau): It'd be nice if there is a way to (a) check if there is
        # a `*.sha512` file, and if so, (b) check the sha of the input file.
        if ENABLE_WARN:
            # TODO(eric.cousineau): Print full location of given file?
            print("\nexternal_data(file = '{}', mode = 'devel'):".format(file) +
                  "\n  Using local workspace file in development mode." +
                  "\n  Please upload this file and commit the *.sha512 file.")
        native.exports_files([file])
    elif mode in ['normal', 'no_cache']:
        name = "download_{}".format(file)
        sha_file = file + SHA_SUFFIX
        tool_name = "download"
        tool = "//tools/external_data:{}".format(tool_name)

        # Binary:
        cmd = "$(location {}) ".format(tool)
        # Argument: Ensure that we can permit relative paths.
        cmd += "--is_bazel_build "
        # Argument: Caching.
        if mode == 'no_cache':
            cmd += "--no_cache "
        else:
            # Use symlinking to avoid needing to copy data to sandboxes.
            # The cache files are made read-only, so even if a test is run
            # with `--spawn_strategy=standalone`, there should be a permission error
            # when attempting to write to the file.
            cmd += "--symlink_from_cache "
        # Argument: SHA file or SHA.
        cmd += "$(location {}) ".format(sha_file)
        # Argument: Output file.
        cmd += "--output $@ "

        if VERBOSE:
            print("\nexternal_data(file = '{}', mode = '{}'):".format(file, mode) +
                  "\n  cmd: {}".format(cmd))

        native.genrule(
          name = name,
          srcs = [sha_file],
          outs = [file],
          cmd = cmd,
          tools = [tool],
          tags = ["external_data"],
          local = 1,  # Just changes `execroot`, but paths are still Bazel-fied.
          visibility = ["//visibility:public"],
        )
    else:
        fail("Invalid mode: {}".format(mode))


def external_data_group(name, files, mode='normal'):
    """ @see external_data """
    for file in files:
        external_data(file, mode)
    native.filegroup(
        name = name,
        srcs = files,
    )


def external_data_sha_group(name, sha_files, sha_files_devel = [], mode='normal'):
    """ Enable globbing of *.sha512 files.
    @see external_data """
    files = []
    files_devel = []
    sha_files_devel_consumed = []
    for sha_file in sha_files:
        if not sha_file.endswith(SHA_SUFFIX):
            fail("SHA file does end with '{}': '{}'".format(SHA_SUFFIX, sha_file))
        file = sha_file[:-len(SHA_SUFFIX)]
        if sha_file in sha_files_devel:
            files_devel.append(file)
            sha_files_devel_consumed.append(sha_file)
        else:
            files.append(file)

    if mode == 'devel' or not files_devel:
        # Define normally.
        external_data_group(
            name = name,
            files = files,
            mode = mode,
        )
    else:
        # Ensure that `sha_files_devel` is a subset of `sha_files`
        for sha_file in sha_files_devel:
            if sha_file not in sha_files_devel_consumed:
                fail("Devel sha file is NOT a subset of `sha_files`: {}".format(sha_file))

        # Define non-devel group.
        external_data_group(
            name = name + "_nondevel",
            files = files,
            mode = mode,
        )
        # Define devel group.
        external_data_group(
            name = name + "_devel",
            files = files_devel,
            mode = "devel",
        )
        # Define same group.
        native.filegroup(
            name = name,
            srcs = [
                name + "_nondevel",
                name + "_devel",
            ],
        )
