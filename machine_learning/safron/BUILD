# 'bazel run //machine_learning/safron'
py_binary(
    name = "safron",
    srcs = ["safron.py"],
    data = glob(["messages/**"]),
    deps = [
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)
