# TODO: shell script for testing client and server at same time
# TODO: print server calls to the console
# TODO: real server logging

# TODO: put common stuff for future chatbots into common library

# TODO: docstrings
# TODO: type hint cleanup
# TODO: tests (cheese historian failure case)(Really? failure case)
# TODO: lint errors
# TODO: README (multiple levels) & update/clarify dependencies for different sub-projects

# TODO: contribute some evals to get GPT 4 access and see if that fixes the prompt injection issues
# (https://github.com/openai/evals)

# TODO: consider getting multiple choices for prompt and using those (instead of re-fetch)
# TODO: consider making an enum for role in messages
# TODO: consider making message a proto for py and ts to share

# TODO: start a real bug/task list in GitHub for anything not done on check-in
# TODO: future: make angular client & put client+server on google cloud

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
    name = "spacebot_constants_lib",
    srcs = ["constants.py"],
)

# 'bazel run //machine_learning/spacebot:client' to use default port
# 'bazel run //machine_learning/spacebot:client -- 8000' to use specific port
#
# To use client and server at the same time, build instead of run and then
# run 'bazel-bin/machine_learning/spacebot/client' directly with above options.
#
# Hit enter to end the chat and terminate the client.
py_binary(
    name = "client",
    srcs = ["client.py"],
    deps = [
        ":spacebot_python_lib",
        ":spacebot_constants_lib",
    ],
)

# 'bazel run //machine_learning/spacebot:server' to use default port
# 'bazel run //machine_learning/spacebot:server -- 8000' to use specific port
#
# To use client and server at the same time, build instead of run and then
# run 'bazel-bin/machine_learning/spacebot/server' directly with above options.
# 
# ctrl-c will stop it the proper way while ctrl-z will force stop it.
# Either way seems to release the port properly.
py_binary(
    name = "server",
    srcs = ["server.py"],
    data = glob(["server_messages/**"]),
    deps = [
        ":spacebot_python_lib",
        ":spacebot_constants_lib",
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)
