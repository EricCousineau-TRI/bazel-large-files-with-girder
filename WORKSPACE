workspace(name = "bazel_large_files_with_girder")

new_http_archive(
    name = "objviewerArchive",
    url = "https://github.com/jcfr/bazel-large-files-with-girder/releases/download/objviewer/objviewer-linux-amd64.tar.gz",
    sha256 = "4e4aa66f3fe34def52402d9ca237d8abbac49f08bab7bffed16f4a4e03b9ada0",
    build_file_content = "exports_files(['objviewer'])"
)

# TODO(eric.cousineau): Package items to be better-deployed with Bazel.
# Move tests (with symlinks) to another location? Or just copy them?
local_repository(
    name = "external_data_bazel_pkg",
    path = "thirdparty/external_data_bazel",
)
