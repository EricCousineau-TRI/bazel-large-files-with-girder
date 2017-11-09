workspace(name = "bazel_large_files_with_girder")

new_http_archive(
    name = "objviewerArchive",
    url = "https://github.com/jcfr/bazel-large-files-with-girder/releases/download/objviewer/objviewer-linux-amd64.tar.gz",
    sha256 = "4e4aa66f3fe34def52402d9ca237d8abbac49f08bab7bffed16f4a4e03b9ada0",
    build_file_content = "exports_files(['objviewer'])"
)

http_archive(
    name = "external_data_bazel_pkg",
    url = "https://github.com/EricCousineau-TRI/external_data_bazel/archive/ce71398ac319cf4dedcf3eed3ae5c2c25e4eb1b4.zip",
    sha256 = "9f3ade94ee039f99074809da920d55fe7202e01e4861e9e76f0a5e0c7db39eb0",
    strip_prefix = "external_data_bazel-ce71398ac319cf4dedcf3eed3ae5c2c25e4eb1b4",
)
