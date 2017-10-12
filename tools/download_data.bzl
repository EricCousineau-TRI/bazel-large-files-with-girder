
# Macro for defining a large file
def large_file(file, download_mode='normal'):
    """
    download_mode: "normal", "skip", "force"
    """
    name = "download_{}".format(file)
    sha_file = "{}.sha512".format(file)
    native.genrule(
      name = name,
      srcs = [sha_file],
      outs = [file],
      cmd="$(location //tools:download_data_script) $(location {}) $@".format(sha_file),
      tools=["//tools:download_data_script"],
      visibility=["//visibility:public"],
    )
