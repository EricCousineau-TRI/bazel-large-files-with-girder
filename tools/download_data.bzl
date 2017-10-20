#load(':hack.bzl', 'sh_binary_env')

ENABLE_WARN = True

# Macro for defining a large file
def large_file(file, mode='normal'):
    """
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
            print("external_data: Using workspace for file '{}'".format(file))
            print("  Please upload this file and commit the *.sha512 file.")
        native.exports_files([file])
    elif mode in ['normal', 'no_cache']:
        name = "download_{}".format(file)
        sha_file = "{}.sha512".format(file)

        cmd = "$(location //tools:download_data_script) "
        if mode == 'no_cache':
            cmd += "--no_cache "
        cmd += "$(location {}) $@".format(sha_file)

        native.genrule(
          name = name,
          srcs = [sha_file],
          outs = [file],
          cmd = cmd,
          tools = ["//tools:download_data_script"],
          tags = ["large_file"],
          local = 1,  # Just changes `execroot`, but paths are still Bazel-fied.
          visibility = ["//visibility:public"],
        )
    else:
        fail("Invalid mode: {}".format(mode))
