def _genrule_shell_env_impl(ctx):
    ctx.actions.run(
        inputs = ctx.files.srcs,
        outputs = ctx.outputs.outs,
        arguments = ctx.attr.arguemnts,
        executable = ctx.executable.cmd,
        mnemonic="shell_env",
        use_default_shell_env=True,
    )

_genrule_shell_env = rule(
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "tool": attr.label(
            cfg = "host",
            executable = True,
            single_file = True,
            mandatory = True,
        ),
        "arguments": attr.string_list(),
        "outs": attr.output_list(),
    },
    output_to_genfiles = True,
    implementation = _genrule_shell_env_impl,
)

# Macro for defining a large file
def large_file(file, download_mode='normal'):
    """
    download_mode: "normal", "skip", "force"
    """

    # Cannot access environment for this file...
    # Use this?
    # https://docs.bazel.build/versions/master/skylark/lib/actions.html#run_shell

    name = "download_{}".format(file)
    sha_file = "{}.sha512".format(file)
    _genrule_shell_env(
        name = name,
        srcs = [sha_file],
        outs = [file],
        tool = "//tools:download_data_script",
        arguments = ["$(location {})".format(sha_file), file],
        visibility = ["//visibility:public"],
    )
    # native.genrule(
    #   name = name,
    #   srcs = [sha_file],
    #   outs = [file],
    #   cmd = "$(location //tools:download_data_script) $(location {}) $@".format(sha_file),
    #   tools = ["//tools:download_data_script"],
    #   local = 1,
    #   visibility = ["//visibility:public"],
    # )
