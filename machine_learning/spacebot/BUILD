# TODO: server logging (possibly to console but maybe not - consider the normal case and
#       the run_local case)
# TODO: angular app to serve as client
#       - will require proxy to make gRPC into HTTP REST
#       - will require library to do gRPC communication on Angular side (exists already)
#       - need a way to configure server and port for the app on launch
#       - then just need the components (eg. textbox and chat history)
# TODO: simplest possible method of hosting this on Google Cloud for demonstration/test purposes
#       it can get increasingly more realistic/sophisticated over time
#       (eg. authorization, CI/CD, docker, serverless, etc. overall for the repo planned over time)
#       (for now, don't get stuck on that stuff - get something up)
#       (but make sure appropriate limits are in place at openai and google so don't get
#        financially attacked)
# TODO: put common stuff for future chatbots into common library

# TODO: tests (cheese historian failure case)(Really? failure case)
# TODO: lint errors
# TODO: TS lint+format setup
# TODO: README (multiple levels) & update/clarify dependencies for different sub-projects
# TODO: start a real bug/task list in GitHub for anything not done on check-in

# TODO: contribute some evals to get GPT 4 access and see if that fixes the prompt injection issues
# (https://github.com/openai/evals)

# TODO: consider getting multiple choices for prompt and using those (instead of re-fetch)
# TODO: consider making an enum for role in messages
# TODO: consider making message a proto for py and ts to share

load("@rules_proto//proto:defs.bzl", "proto_library")
load("//bazel:defs.bzl", "python_grpc_library")

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
#
# NOTE: As long as they all use the same port as the server, you can run
#       multiple clients at the same time (using the bazel-bin way).
py_binary(
    name = "client",
    srcs = ["client.py"],
    deps = [
        ":spacebot_constants_lib",
        ":spacebot_python_lib",
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
        ":spacebot_constants_lib",
        ":spacebot_python_lib",
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)
