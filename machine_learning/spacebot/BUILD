load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_proto_grpc//python:defs.bzl", "python_proto_library")

proto_library(
    name = "spacebot_proto",
    srcs = ["spacebot.proto"],
    deps = ["@com_google_protobuf//:empty_proto"],
)

python_proto_library(
    name = "spacebot_python_proto",
    output_mode = "NO_PREFIX",
    protos = [":spacebot_proto"],
)

py_library(
    name = "definitions_lib",
    srcs = ["definitions.py"],
    deps = [":spacebot_python_proto"],
)

py_library(
    name = "client_lib",
    srcs = ["client.py"],
    deps = [
        ":definitions_lib",
        ":spacebot_python_proto",
    ],
)

py_library(
    name = "server_lib",
    srcs = ["server.py"],
    data = glob(["server_messages/**"]),
    deps = [
        ":definitions_lib",
        ":spacebot_python_proto",
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)

py_binary(
    name = "spacebot",
    srcs = ["spacebot.py"],
    deps = [
        ":client_lib",
        ":server_lib",
    ],
)
