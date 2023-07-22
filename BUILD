load("@com_github_bazelbuild_buildtools//buildifier:def.bzl", "buildifier")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@npm//:defs.bzl", "npm_link_all_packages")
load("@aspect_rules_js//js:defs.bzl", "js_library")
load("//bazel:defs.bzl", "package_local", "python_grpc_library")
load("//bazel:angular-bazel.bzl", "ng_config")

# TODO: lock this down later (and move exports to proper targets)
package(default_visibility = ["//visibility:public"])

# Link npm packages as //:node_modules.
npm_link_all_packages(name = "node_modules")

js_library(
    name = "package_json_jslib",
    srcs = ["package.json"],
)

js_library(
    name = "karma_conf_js",
    srcs = [
        "karma.conf.js",
    ],
)

ng_config(
    name = "ng-config",
)

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
    visibility = ["//:__subpackages__"],
)

# Make python files for the google protos.
python_grpc_library(
    name = "google_python_grpc_proto_lib",
    srcs = [":google_proto_lib"],
    visibility = ["//:__subpackages__"],
)
