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

external_data_sha_group(
    name = "extra",
    sha_files = glob(['extra*.sha512']),
)
