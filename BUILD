load("@com_github_bazelbuild_buildtools//buildifier:def.bzl", "buildifier")
load("@rules_proto//proto:defs.bzl", "proto_library")
load ("//bazel:defs.bzl", "python_grpc_library", "package_local")

buildifier(
    name = "buildifier",
)

# Ideally we only need to include the files the target needs.
# But for now, there aren't that many so it's not too bad.
# We need to use this rule in order to mitigate issues with
# the external verison of the google protobuf path.
package_local(
    name = "google_proto_files",
    srcs = ["@com_google_protobuf//:well_known_type_protos"],
    subpackage = "google/protobuf",
)

# Wrap the local versions of the google protos.
proto_library(
    name = "google_proto_lib",
    srcs = [":google_proto_files"],
    visibility = ['//:__subpackages__'],
)

# Make python files for the google protos.
python_grpc_library(
    name = "google_python_grpc_proto_lib",
    srcs = [":google_proto_lib"],
    visibility = ['//:__subpackages__'],
)
