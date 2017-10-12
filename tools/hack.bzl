def _impl(ctx):
    ctx.actions.run(
        inputs = ctx.files.srcs,
        outputs = ctx.outputs.outs,
        arguments = ctx.attr.arguments,
        executable = ctx.executable.tool,
        mnemonic="GenruleShell",
        use_default_shell_env=True,
    )

sh_binary_env = rule(
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "tool": attr.label(
            cfg = "host",
            executable = True,
            allow_files = True,
            mandatory = True,
        ),
        "arguments": attr.string_list(),
        "outs": attr.output_list(),
    },
    output_to_genfiles = False,
    implementation = _impl,
)
