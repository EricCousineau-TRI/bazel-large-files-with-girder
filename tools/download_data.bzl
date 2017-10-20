#load(':hack.bzl', 'sh_binary_env')

def _impl(ctx):
    print("Rule name = %s, package = %s" % (ctx.label.name, ctx.label.package))

    # Check if the file exists in the input workspace.
    f = ctx.file.file
    print("File: {}".format(ctx.path(f)))
        sha_file = "{}.sha512".format(file)

    native.genrule(
      name = name,
      srcs = [sha_file],
      outs = [f],
      cmd = "$(location //tools:download_data_script) $(location {}) $@".format(sha_file),
      tools = ["//tools:download_data_script"],
      tags = ["large_file"],
      # local = 1,  # Just changes `execroot`, but paths are still verbose.
      visibility = ["//visibility:public"],
    )


_large_file = repository_rule(
    implementation = _impl,
    attrs = {
        "file": attr.label(mandatory=True, allow_files=True, single_file=True),
        "sha_file": attr.label(mandatory=True, allow_files=True, single_file=True),
    },
)

# Macro for defining a large file
def large_file(file, download_mode='normal'):
    """
    download_mode: "normal", "skip", "force"
    """

    name = "download_{}".format(file)
    sha_file = "{}.sha512".format(file)

    _large_file(
        name = name,
        sha_file = sha_file,
    )

    # Cannot access environment for this file...
    # Use this?
    # https://docs.bazel.build/versions/master/skylark/lib/actions.html#run_shell
    # Nope. Only allows using existing PATH / LD_LIBRARY_PATH or not.

    # sh_binary_env(
    #     name = name,
    #     srcs = [sha_file],
    #     outs = [file],
    #     tool = "//tools:download_data.sh",
    #     arguments = ["$(location {})".format(sha_file), file],
    #     visibility = ["//visibility:public"],
    # )

    # native.genrule(
    #   name = name,
    #   srcs = [sha_file],
    #   outs = [file],
    #   cmd = "$(location //tools:download_data_script) $(location {}) $@".format(sha_file),
    #   tools = ["//tools:download_data_script"],
    #   tags = ["large_file"],
    #   # local = 1,  # Just changes `execroot`, but paths are still verbose.
    #   visibility = ["//visibility:public"],
    # )
