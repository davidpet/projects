load("@rules_proto//proto:defs.bzl", "proto_library")
load ("//bazel:defs.bzl", "python_grpc_library")

proto_library(
    name = "spacebot_proto",
    srcs = ["spacebot.proto"],
    deps = ["//:google_proto_lib"],
)

python_grpc_library(
    name = "spacebot_python_proto",
    srcs = [":spacebot_proto"],
    deps = ["//:google_python_grpc_proto_lib"],
)

py_library(
    name = "spacebot_python_lib",
    srcs = [":spacebot_python_proto"],
)

py_library(
    name = "client_lib",
    srcs = ["client.py"],
    deps = [
        ":spacebot_python_lib",
    ],
)

py_library(
    name = "server_lib",
    srcs = ["server.py"],
    data = glob(["server_messages/**"]),
    deps = [
        ":spacebot_python_lib",
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)

# 'bazel run //machine_learning/spacebot' to use default port
# 'bazel run //machine_learning/spacebot -- 8000' to use specific port
py_binary(
    name = "spacebot",
    srcs = ["spacebot.py"],
    deps = [
        ":client_lib",
        ":server_lib",
        ":spacebot_python_lib",
    ],
)
