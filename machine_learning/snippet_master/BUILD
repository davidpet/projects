py_binary(
    name = "snippet_master",
    srcs = ["snippet_master.py"],
    data = glob(["prompts/*.txt"]),
    deps = [
        "//machine_learning/common:openai_lib",
        "//machine_learning/common:utilities_lib",
    ],
)
