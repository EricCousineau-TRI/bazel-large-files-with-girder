# Motivating Workflows

## Notes

* This is intended to work namely in Bazel. You may run this outside of Bazel, via `bazel-bin/`, but due to verbosity, it's recommended to use the Bazel command.
* Since this is intended to run under Bazel (`download` out of necessity, `upload` for the reasons listed above), we must specify absolute paths.
    * This can be done via the shorthand `~+` in `bash`, or via `${PWD}` or `$(pwd)`.

## Configuration

* Inspect the configuration in `tools/external_data/girder.gitconfig`. This is for the repository.
* Inspect `tools/external_data/girder.gitconfig.user.tpl`. This is a template, which should live in `~/.girder.gitconfig`. Ensure you add the appropriate API key so that you have authorized access.

## Start Drafting a Large File

Say you're in `/data`, and want to author `dragon.obj` to be used in a Bazel
test.

1. Add a Bazel target for this file indicating that it's external data and that you're in the process of developing the file. In `data/BUILD.bazel`:

        external_data(
            file = "dragon.obj",
            mode = "devel",  # Delete once you've uploaded.
        )

    NOTE: Under the hood, this simply uses `exports_files(...)` to make the file a proper target, using the same name. This is useful for later points in time, when you want to edit a file that has already been versioned.

2. Write a test, e.g. `//test:inspect_dragon`, that consumes this file:

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
    repository (`/data/dragon.obj`) for server-side versioning.

2. Update `/data/BUILD.bazel` to indicate that you're now using the uploaded version (this tells Bazel to expect `~+/dragon.obj.sha512`):

        external_data(
            file = "dragon.obj",
        )

3. To test if Bazel can download this file, execute this in `/data`:

        bazel build :dragon.obj

    This should have downloaded, cached, and exposed this file in Bazel's workspace.
    Now run `//test:inspect_dragon` (which should use Bazel's cached version) and ensure this works.

4. Now commit the `*.sha512` file in Git.

## Edit the File Later

Let's say you've removed `dragon.obj` from `/data`, but a month later you wish to revise it. To update the file:

1. Download the corresponding SHA file:

        cd data
        bazel run //tools/external_data:download -- ~+/dragon.obj.sha512

2. Change `/data/BUILD.bazel` back to development mode:

        external_data(
            file = "dragon.obj",
            mode = "devel",  # Add this line back in.
        )

3. Make the appropriate changes.

4. Follow the steps in "Upload the File for Deployment".

## Use `*.sha512` globs in `BUILD.bazel`

If you have a set of `*.sha512` files that you do not want to specify individual Bazel `external_data` targets for, you may use `external_data_sha_group`. As an example in `/data`:

    external_data_sha_group(
        name = "meshes",
        sha_files = glob([
            '**/*.obj.sha512'
        ]),
    )

You may now use `:meshes` in tests to get all of these files. Note that you may also use `mode = "devel"` if you wish to edit *all* of them. You *must* have these files present in your workspace; to make this happen, so below.

If you wish to expose all of these files within the Bazel build sandbox, you may execute:

    bazel build :meshes

NOTE: This interface will cache the files under `~/.cache/bazel-girder`, and thus you will not need to re-download these files.

## Download a Set of Files

NOT YET IMPLEMENTED

If you wish to download *all* files of a given extension at the specified revision under a certain directory, you may use `find` (and ensure that you use `~+` so that it returns absolute paths):

    find ~+ -name '*.obj.sha512' | xargs bazel run //tools/external_data:download --

For each `${file}.sha512` that is found, the file will be downloaded to `${file}`. Note that this will fail if one of the outputs already exists.

As above, these files are cached.

## Download One File to a Specific Location

NOT YET IMPLEMENTED

This is used in Bazel via `macros.bzl`:

    bazel run //tools/external_data:download -- ${file}.sha512 --output ${file}

## TODO

* Make `//tools/external_data` an actual external in Bazel, possibly something like `bazel-external-data`, such that we could do:

        bazel run @external_data//:download -- ~+/${file}.sha512
        # OR
        girder-cli git download ${file}.sha512

        bazel run @external_data//:upload -- ~+/file
        # OR
        girder-cli git download ${file}

* If possible, merge scripts into `girder_client` if appropriate. (Though it may be too heavily Bazel-based.)
* Revisit the use of `git annex` as a frontend with more complex merging mechanisms.
