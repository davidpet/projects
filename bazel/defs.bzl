load("@rules_python//python:defs.bzl", "py_library")
load("@rules_proto//proto:defs.bzl", "ProtoInfo")
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//lib:new_sets.bzl", "sets")

# TODO: test these way more tha the shallow testing I did to hack them together
#       I'm sure there are lots of dragons in there.

def _python_grpc_library_impl(ctx):
    all_proto_files = []
    compiled_proto_files = []
    relative_compiled_proto_files = []
    proto_roots = sets.make([ctx.bin_dir.path, '.'])
    output_py_files = []
    dep_py_files = ctx.files.deps

    if not ctx.attr.generate_pb2 and not ctx.attr.generate_pb2_grpc:
        fail("Because generate_pb2 and generateE_pb2_grpc are both false - this will generate nothing!")

    for src in ctx.attr.srcs:
        all_proto_files.extend(src[ProtoInfo].transitive_sources.to_list())
        compiled_proto_files.extend(src[ProtoInfo].direct_sources)
        relative_compiled_proto_files.extend([paths.relativize(ds.path, paths.join(src[ProtoInfo].proto_source_root, ctx.label.package)) for ds in src[ProtoInfo].direct_sources])
        proto_roots = sets.union(proto_roots, sets.make(src[ProtoInfo].transitive_proto_path.to_list()))

    print('davidpet: all_proto_files')
    for proto_file in all_proto_files:
        print(proto_file.path)
    print('davidpet: compiled_proto_files')
    for proto_file in compiled_proto_files:
        print(proto_file.path)
    print('davidpet: relative_compiled_proto_files')
    for proto_file in relative_compiled_proto_files:
        print(proto_file)
    print('davidpet: proto_roots')
    for proto_root in sets.to_list(proto_roots):
        print(proto_root)
    print('davidpet: dep_py_files')
    for py_file in dep_py_files:
        print(py_file.path)

    for i in range(len(compiled_proto_files)):
        input = compiled_proto_files[i]
        rel_input = relative_compiled_proto_files[i]
        
        if ctx.attr.generate_pb2:
            output_file_pb2 = ctx.actions.declare_file(paths.replace_extension(rel_input, "_pb2.py"))
            output_py_files.append(output_file_pb2)
        if ctx.attr.generate_pb2_grpc:
            output_file_pb2_grpc = ctx.actions.declare_file(paths.replace_extension(rel_input, "_pb2_grpc.py"))
            output_py_files.append(output_file_pb2_grpc)

    print('davidpet: output_py_files')
    for py_file in output_py_files:
        print(py_file.path)

    args = []
    args.extend(['-m', 'grpc_tools.protoc'])
    if ctx.attr.generate_pb2:
        args.append('--python_out="$(realpath "{}")"'.format(ctx.bin_dir.path))
    if ctx.attr.generate_pb2_grpc:
        args.append('--grpc_python_out="$(realpath "{}")"'.format(ctx.bin_dir.path))
    for proto_root in sets.to_list(proto_roots):
        args.append('--proto_path="$(realpath "{}")"'.format(proto_root))
    for proto in relative_compiled_proto_files:
        args.append('"{}"'.format(paths.join(ctx.label.package, proto)))
    protoc_command = 'python3 ' + ' '.join(args)
    print('davidpet: protoc command')
    print(protoc_command)

    ctx.actions.run_shell(
        inputs = all_proto_files,
        outputs = output_py_files,
        mnemonic = 'CondaProtoc',
        use_default_shell_env = True,
        command = """
            export HOME={0}
            conda init bash
            if [[ -f "$HOME/.bashrc" ]]; then
                source "$HOME/.bashrc"
            elif [[ -f "$HOME/.bash_profile" ]]; then
                source "$HOME/.bash_profile"
            fi
            conda activate {1}

            {2}
        """.format(ctx.bin_dir.path, ctx.attr.conda, protoc_command)
    )

    return [
        DefaultInfo(files = depset(output_py_files + dep_py_files)),
    ]

# srcs = proto_library_rules
#       all transitive .proto files will be included during compilation
#       only direct .proto files will be compiled into .py files
# deps = other python_grpc_library rules
#       all transitive .py files will be included with the ones from this rule
# conda = conda workspace to activate for calling protoc
# generate_pb2 = whether to generate normal proto compiled output for each proto in srcs
# geneerate_pb2_grpc = whether to generate grpc python output for each proto in srcs
# output = DefaultInfo for all python files generated plus ones included transitively
# Usage:
#    each proto_library should have a python_grpc_library to generate .py files in its package
#    then the dependency chain of the proto_library files should mirror the python_grpc_library deps
#    then a final py_library rule can operate on the topmost one you need to get all the .py files together
python_grpc_library = rule(
    implementation = _python_grpc_library_impl,
    attrs = {
        "srcs": attr.label_list(providers = [ProtoInfo]),
        "deps": attr.label_list(providers = [DefaultInfo]),
        "conda": attr.string(default='bazel-protoc'),
        "generate_pb2": attr.bool(default = True),
        "generate_pb2_grpc": attr.bool(default = True),
    },
)

def _package_local_impl(ctx):
    outputs = []

    package_path = paths.join(ctx.label.package, ctx.attr.subpackage)
    for src in ctx.files.srcs:
        beg = src.path.rfind(package_path)
        if beg == -1:
            fail("{} is not in a variant of package {}".format(src.path, ctx.label.package))
        trailing_path = src.path[beg:]
        declare_path = paths.relativize(trailing_path, ctx.label.package)
        output = ctx.actions.declare_file(declare_path)
        outputs.append(output)

    for i in range(len(outputs)):
        output = outputs[i]
        src = ctx.files.srcs[i]

        ctx.actions.run_shell(
            inputs = [src],
            outputs = [output],
            command = 'cp "{}" "{}"'.format(src.path, output.path),
        )
    
    return [
        DefaultInfo(files = depset(outputs)),
    ]

# Given files that appear in some variation of this package path plus the subpackage path,
# will copy them to the ctx.bin_dir canonnical output variation of the package plus subpackage path.
# If subpackage is ommitted, it is ignored.  Subpackage need not (and probably should not) be an
# actual package.
# This is a way to consolidate files from srcs, bazel-out, and externals (eg. other repo) into one
# place (bazel-out and then bazel-bin at the end of execution).
package_local = rule(
    implementation = _package_local_impl,
    attrs = {
        "srcs": attr.label_list(),
        "subpackage": attr.string(),
    },
)
