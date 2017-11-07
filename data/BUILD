load("//tools:external_data.bzl",
    "external_data",
    "add_external_data_tests",
)


#
# Larger file associated with a key file and available
# on Girder file server can be added as a test dependency
# after specifying a rule that will automatically download
# them when needed.
#

external_data(
    file = "dragon.obj",
    # mode = "devel",
    visibility = ["//visibility:public"],
)

add_external_data_tests()
