# TODO: consider using pip_install target or docker to hermetize
# the following dependencies:
#    (ai) conda environment (with a lot of packages included)

load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "checks_lib",
    srcs = ["checks.py"],
)

py_library(
    name = "datasets_lib",
    srcs = ["datasets.py"],
)

py_library(
    name = "error_analysis_lib",
    srcs = ["error_analysis.py"],
    deps = [":visualization_lib"],
)

py_library(
    name = "models_lib",
    srcs = ["models.py"],
)

py_library(
    name = "openai_lib",
    srcs = ["openai_api.py"],
    data = glob(["openai_api/**"]),
    deps = [":utilities_lib"],
)

py_library(
    name = "utilities_lib",
    srcs = ["utilities.py"],
)

py_library(
    name = "visualization_lib",
    srcs = ["visualization.py"],
)

py_test(
    name = "checks_test",
    srcs = ["checks_test.py"],
    deps = [":checks_lib"],
)

py_test(
    name = "datasets_test",
    srcs = ["datasets_test.py"],
    deps = [":datasets_lib"],
)

py_test(
    name = "error_analysis_test",
    srcs = ["error_analysis_test.py"],
    deps = [":error_analysis_lib"],
)

py_test(
    name = "models_test",
    srcs = ["models_test.py"],
    deps = [":models_lib"],
)

py_test(
    name = "utilities_test",
    srcs = [
        "utilities_test.py",
        "utilities_test_data/subfolder_module.py",
    ],
    data = [
        "utilities_test_data/file.json",
        "utilities_test_data/file.txt",
        "utilities_test_data/otherfile.txt",
    ],
    deps = [":utilities_lib"],
)

py_test(
    name = "visualization_test",
    srcs = ["visualization_test.py"],
    deps = [":visualization_lib"],
)

test_suite(
    name = "all_tests",
    tests = [
        ":checks_test",
        ":datasets_test",
        ":error_analysis_test",
        ":models_test",
        ":utilities_test",
        ":visualization_test",
    ],
)

py_package(
    name = "all_libs",
    deps = [
        ":checks_lib",
        ":datasets_lib",
        ":error_analysis_lib",
        ":models_lib",
        ":openai_lib",
        ":utilities_lib",
        ":visualization_lib",
    ],
)

py_wheel(
    name = "all_libs_wheel",
    distribution = "example_minimal_library",
    python_tag = "py3",
    version = "0.0.1",
    deps = [
        ":all_libs",
    ],
)
