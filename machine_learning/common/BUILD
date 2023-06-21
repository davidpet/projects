# TODO: consider using pip_install target or docker to hermetize
# the following dependencies:
#    (ai) conda environment (with a lot of packages included)

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
        ":visualization_test",
    ],
)
