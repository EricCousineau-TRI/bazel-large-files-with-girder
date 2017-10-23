load("//tools/external_data:macros.bzl", "external_data", "external_data_sha_group")

#
# Larger file associated with a key file and available
# on Girder file server can be added as a test dependency
# after specifying a rule that will automatically download
# them when needed.
#

external_data(
    file = "dragon.obj",
    # mode = 'devel',
)

# external_data_sha_group(
#     name = "extra",
#     sha_files = glob(['extra*.sha512']),
# )

external_data_sha_group(
    name = "extra_nondevel",
    sha_files = glob(
        include = ['extra*.obj.sha512'],
        exclude = ['extra2.obj.sha512'],
    ),
)
external_data(
    file = "extra2.sha512",
    mode = "devel",
)
filegroup(
    name = "extra",
    srcs = [
        ":extra_nondevel",
        ":extra2.obj",
    ],
)
