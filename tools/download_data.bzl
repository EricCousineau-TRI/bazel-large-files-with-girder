#load(':hack.bzl', 'sh_binary_env')

# Macro for defining a large file
def large_file(file, use_workspace = False, download_mode='normal'):
    """
    download_mode: "normal", "skip", "force"
    """

    # Cannot access environment for this file...
    # Use this?
    # https://docs.bazel.build/versions/master/skylark/lib/actions.html#run_shell
    # Nope. Only allows using existing PATH / LD_LIBRARY_PATH or not.

    if use_workspace:
        native.exports_files([file])
    else:
        name = "download_{}".format(file)
        sha_file = "{}.sha512".format(file)

        native.genrule(
          name = name,
          srcs = [sha_file],
          outs = [file],
          cmd = "$(location //tools:download_data_script) $(location {}) $@".format(sha_file),
          tools = ["//tools:download_data_script"],
          tags = ["large_file"],
          # local = 1,  # Just changes `execroot`, but paths are still verbose.
          visibility = ["//visibility:public"],
        )
