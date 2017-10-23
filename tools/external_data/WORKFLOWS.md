# Motivating Workflows

## Notes

* This is intended to work namely in Bazel. You may run this outside of Bazel, via `bazel-bin/`, but due to verbosity, it's recommended to use the Bazel command.
* Since this is intended to run under Bazel (`download` out of necessity, `upload` for the reasons listed above), we must specify absolute paths.
    * This can be done via the shorthand `~+` in `bash`, or `${PWD}` / `$(pwd)`.


## Configuration

* Inspect the configuration in `./girder/girder.repo.conf`. This is for the repository.
* Inspect `./girder/girder.user.conf`. This is a template, which should live in `~/.girder.conf`. Ensure you add the appropriate API key so that you have authorized access.


## Start Drafting a Large File

Say you're in `:/data`, and want to author `dragon.obj` to be used in a Bazel
test.

1. Add a Bazel target for this file indicating that it's external data and that you're in the process of developing the file. In `:/data/BUILD.bazel`:

        external_data(
            file = "dragon.obj",
            mode = "devel",  # Delete once you've uploaded.
        )

    NOTE: Under the hood, this simply uses `exports_files(...)` to make the file a proper target, using the same name. This is useful for later points in time, when you want to edit a file that has already been versioned.

2. Write a test, e.g. `://test:inspect_dragon`, that consumes this file:

        sh_test(
            name = "inspect_dragon",
            ...,
            args = ["data/dragon.obj"],
            data = ["//data:dragon.obj"],
            tags = ["external_data"],  # Specify so that we can discriminate.
        )

    Run the test to ensure it works as expected.


## Upload the File for Deployment

1. Run the `upload` script given the absolute path of the desired file:

        cd data
        touch dragon.obj
        bazel run //toos/external_data:upload -- ~+/dragon.obj

    If the file does not already exist on the desired server, this creates
    `~+/dragon.obj.sha512`, and will add the path of the file relative to this
    repository (`:/data/dragon.obj`) for server-side versioning.

    NOTE: You may upload multiple files.

2. Update `:/data/BUILD.bazel` to indicate that you're now using the uploaded version (this tells Bazel to expect `~+/dragon.obj.sha512`):

        external_data(
            file = "dragon.obj",
        )

3. To test if Bazel can download this file, execute this in `:/data`:

        bazel build :dragon.obj

    This should have downloaded, cached, and exposed this file in Bazel's workspace.
    Now run `://test:inspect_dragon` (which should use Bazel's cached version) and ensure this works.

4. Now commit the `*.sha512` file in Git.


## Edit the File Later

Let's say you've removed `dragon.obj` from `:/data`, but a month later you wish to revise it. To update the file:

1. Download the corresponding SHA file:

        cd data
        bazel run //tools/external_data:download -- ~+/dragon.obj.sha512

2. Change `:/data/BUILD.bazel` back to development mode:

        external_data(
            file = "dragon.obj",
            mode = "devel",  # Add this line back in.
        )

3. Make the appropriate changes.

4. Follow the steps in "Upload the File for Deployment".

## Use `*.sha512` groups in `BUILD.bazel`

For groups of large data files, you could specify individual Bazel `external_data` targets, or explicitly list the files in  `external_data_group`.

However, if you have a large set of `*.${ext}.sha512` files, it may be easier to use the workspace's directory structure to glob these files. (You cannot reliably use `*.${ext}` without the suffix because these files would not exist normally.)

As an example in `:/data`:

    external_data_group(
        name = "meshes",
        files = strip_sha(glob(['**/*.obj.sha512'])),
    )

You may now use `:meshes` in tests to get all of these files.

If you wish to expose all of these files within the Bazel build sandbox, you may execute:

    bazel build :meshes

NOTE: This interface will cache the files under `~/.cache/bazel-girder`, and thus you will not need to re-download these files.


## Edit Files in a `*.sha512` group

You may also use `mode = "devel"` in `external_data_group` if you wish to edit *all* of the files. If you do want this, you must have downloaded all of the files to your workspace (as shown down below).

If you want to edit a certain file in a group, then you can make two upstream targets, non-devel and devel, and link this as a `filegroup` to the original filegroup.

Alternatively, you may use `external_data_group(..., files_devel)`, which can simplify this process:

    external_data_group(
        name = "meshes_nondevel",
        files = strip_sha(glob(['**/*.obj.sha512'])),
        files_devel = ['robot/to_edit.obj'],
    )

NOTE: You can extend this to use an `*.obj` files in the workspace to assume that they are to be consumed directly:

    external_data_group(
        name = "meshes_nondevel",
        files = strip_sha(glob(['**/*.obj.sha512'])),
        files_devel = glob(['**/*.obj']),
    )


## Download a Set of Files

If you wish to download *all* files of a given extension at the specified revision under a certain directory, you may use `find` (and ensure that you use `~+` so that it returns absolute paths):

    find ~+ -name '*.obj.sha512' | xargs bazel run //tools/external_data:download --

For each `${file}.sha512` that is found, the file will be downloaded to `${file}`.

NOTE: This will fail if one of the outputs already exists; you must specify `--force` to enable overwriting.

As above, these files are cached.


## Download One File to a Specific Location

This is used in Bazel via `macros.bzl`:

    bazel run //tools/external_data:download -- ${file}.sha512 --output ${file}


## Download Files and Expose as Symlinks (Do Not Copy)

If you just need easy read-only access to files (and don't want to deal with Bazel's paths), you can use `--symlink_from_cache`:

    bazel run //tools/external_data:download -- --symlink_from_cache ~+/*.sha512


## TODO

* Make `://tools/external_data` an actual external in Bazel, possibly something like `bazel-external-data`, such that we could do:

        bazel run @external_data//:download -- ~+/${file}.sha512
        # OR
        girder-cli git download ${file}.sha512

        bazel run @external_data//:upload -- ~+/file
        # OR
        girder-cli git download ${file}

* If possible, merge scripts into `girder_client` if appropriate. (Though it may be too heavily Bazel-based.)
* Revisit the use of `git annex` as a frontend with more complex merging mechanisms.
