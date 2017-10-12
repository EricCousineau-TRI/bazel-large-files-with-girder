
# Macro for defining a large file
def large_file(name):
    sha_file = "{}.sha512".format()
    genrule(
      name="download_dragon_obj",
      srcs=["dragon.obj.sha512"],
      outs=["dragon.obj"],
      cmd="$(location //tools:download_data_script) $(location dragon.obj.sha512) $@",
      tools=["//tools:download_data_script"],
      visibility=["//visibility:public"],
    )
