# Custom Bazel rules originally copied from the Aspect Build Angular Example.
# I added a lot of comments to aid my own understanding and modified some things
# to fit my setup (notated changes where appropriate).

# This loads a generated bzl file to get some rules for interfacing with an npm package.
# In this case, we are interfacing with the Architect CLI package to do Angular Artchitect
# build stuff, just like angular.json specifies.
# We are aliasing the bin folder as architect_cli and then calling things inside that
# such as architect_cli.architect.
# I'm not sure the exact format of binary vs. script vs. argument - but that's the
# general idea.
load("@npm//:@angular-devkit/architect-cli/package_json.bzl", architect_cli = "bin")

# These 3 are just direct imports from repos set up in WORKSPACE.
load("@aspect_bazel_lib//lib:copy_to_bin.bzl", "copy_to_bin")
load("@aspect_bazel_lib//lib:jq.bzl", "jq")
load("@aspect_rules_js//js:defs.bzl", "js_library")

# NOTE:
#  *_DEPS are propagated as deps of the final output
#  *_CONFIG are dependencies only of the architect actions and not propagated

# Global dependencies such as common config files, tools.
# COMMON because used by libraries and apps (as well as tests).
COMMON_CONFIG = [
    # This depends on having an ng_config being used in root BUILD of workspace.
    # (it looks a bit circular but it's not if you trace it all out)
    "//:ng-config",

    # Build-related npm packages needed by everything.
    "//:node_modules/@angular-devkit/build-angular",
    "//:node_modules/@angular-devkit/architect-cli",
]

# Common dependencies of Angular CLI applications
# (used by ng_app macro)
APPLICATION_CONFIG = [
    ":tsconfig.app.json",
    "//:package_json_jslib",
]

# npm packages used by all angular application
APPLICATION_DEPS = [
    "//:node_modules/@angular/common",
    "//:node_modules/@angular/core",
    "//:node_modules/@angular/router",
    "//:node_modules/@angular/platform-browser",
    "//:node_modules/@angular/platform-browser-dynamic",
    "//:node_modules/@types/node",
    "//:node_modules/rxjs",
    "//:node_modules/tslib",
    "//:node_modules/zone.js",
]

# Common dependencies of Angular CLI libraries
# (used by ng_lib macro)
LIBRARY_CONFIG = [
    ":tsconfig.lib.json",
    ":tsconfig.lib.prod.json",
    ":package.json",
]

# npm packages used by all angular libs
LIBRARY_DEPS = [
    "//:node_modules/@angular/common",
    "//:node_modules/@angular/core",
    "//:node_modules/@angular/router",
    "//:node_modules/@types/node",
    "//:node_modules/rxjs",
    "//:node_modules/tslib",
]

# Common dependencies of Angular CLI test suites
# (used by ng_app and ng_lib)
TEST_CONFIG = [
    ":tsconfig.spec.json",
    "//:karma_conf_js",
    ":karma.conf.js",
    "//:node_modules/@types/jasmine",
    "//:node_modules/karma-chrome-launcher",
    "//:node_modules/karma",
    "//:node_modules/karma-jasmine",
    "//:node_modules/karma-jasmine-html-reporter",
    "//:node_modules/karma-coverage",
]
TEST_DEPS = LIBRARY_DEPS + [
    "//:node_modules/@angular/compiler",
    "//:node_modules/@angular/platform-browser",
    "//:node_modules/@angular/platform-browser-dynamic",
    "//:node_modules/jasmine-core",
    "//:node_modules/zone.js",
]

# JQ expressions to update Angular project output paths to be in the bazel-bin output relative to the package.
# If we don't do this, the output files will just be mysteriously missing with no error.
# NOTE: I had to modify this from the original because I used 'libs' instead of 'projects'.
# JQ_DIST_REPLACE_TSCONFIG = ".compilerOptions.paths |= map_values(map(gsub(\"^dist/(?<p>.+)$\"; \"libs/\"+.p+\"/dist\")))"
JQ_DIST_REPLACE_ANGULAR_JSON = """
.projects |= with_entries(
    if .value.projectType == "application"
    then .value.architect.build.options.outputPath = .value.root + "/dist/" + .key
    else .
    end
)
"""
JQ_DIST_REPLACE_NG_PACKAGE = ".dest = \"dist\""

# Macro to define a filegroup called ng-config containing angular.json (copied to output of sandbox
# ) and tsconfig.json (modified to output to individual lib folder dist instead of workspace dist).
# This should be called once in the workspace-root BUILD.
def ng_config(name):
    # Just enforces that the name must be ng-config (this is a singular rule for the workspace).
    # But actually the name becomes the name of the final filegroup.
    if name != "ng-config":
        fail("NG config name must be 'ng-config'")

    # Root config files used throughout.
    # NOTE: The original example doesn't modify angular.json, but I had to because my app is not at
    #       the root of the Angular workspace.
    jq(
        name = "angular",
        srcs = ["angular.json"],
        filter = JQ_DIST_REPLACE_ANGULAR_JSON,
    )

    # Replaces some fields in tsconfig.json for bazel build purposes because bazel builds to a different
    # place than Angular CLI does.
    # NOTE: project dist directories are under the project dir unlike the Angular CLI default of the root dist folder
    #jq(
    #name = "tsconfig",
    #srcs = ["tsconfig.json"],
    #filter = JQ_DIST_REPLACE_TSCONFIG,
    #)
    copy_to_bin(
        name = "tsconfig",
        srcs = ["tsconfig.json"],
    )

    # Package up our modified/copied angular.json and tsconfig.json as a file group named
    # ng-config.
    native.filegroup(
        name = name,
        srcs = [":angular", ":tsconfig"],
    )

# Meant to be used in a BUILD file in the folder of a single app within the
# workspace.
# eg. you can only :serve one target from the package.
# NOTE: Dependencies (such as lib build targets) are passed in via deps arg.
def ng_app(name, project_name = None, deps = [], test_deps = [], **kwargs):
    """
    Bazel macro for compiling an NG application project. Creates :{name}, :test, :serve targets.
    Args:
      name: the rule name
      project_name: the Angular CLI project name, to the rule name
      deps: dependencies of the library
      test_deps: additional dependencies for tests
      **kwargs: extra args passed to main Angular CLI rules
    """

    # Get all src files that aren't test files in the package using this macro.
    srcs = native.glob(
        ["src/**/*"],
        exclude = [
            "src/**/*.spec.ts",
            "src/test.ts",
            "dist/",
        ],
    )

    # Get all test src files in the package using this macro.
    test_srcs = native.glob(["src/test.ts", "src/**/*.spec.ts"])

    project_name = project_name if project_name else name

    # Build the application as the name passed in.
    architect_cli.architect(
        name = name,
        chdir = native.package_name(),
        args = ["%s:build" % project_name],
        out_dirs = ["dist/%s" % project_name],
        srcs = srcs + deps + APPLICATION_DEPS + APPLICATION_CONFIG + COMMON_CONFIG,
        **kwargs
    )

    # Serve the application as a target called :serve in the package calling this.
    architect_cli.architect_binary(
        name = "serve",
        chdir = native.package_name(),
        args = ["%s:serve" % project_name],
        data = srcs + deps + APPLICATION_DEPS + APPLICATION_CONFIG + COMMON_CONFIG,
        **kwargs
    )

    # :test target for the app.
    architect_cli.architect_test(
        name = "test",
        chdir = native.package_name(),
        args = ["%s:test" % project_name],
        data = srcs + test_srcs + deps + test_deps + TEST_DEPS + TEST_CONFIG + COMMON_CONFIG,
        log_level = "debug",
        **kwargs
    )

# Meant to be used in a BUILD file in the folder of a single lib within the
# workspace.
# NOTE: Dependencies (such as lib build targets) are passed in via deps arg.
def ng_lib(name, project_name = None, deps = [], test_deps = [], **kwargs):
    """
    Bazel macro for compiling an NG library project. Creates {name}, test, targets.
    Args:
      name: the rule name
      project_name: the Angular CLI project name, defaults to current directory name
      deps: dependencies of the library
      test_deps: additional dependencies for tests
      **kwargs: extra args passed to main Angular CLI rules
    """

    # Get all src files that aren't test files in the package using this macro.
    srcs = native.glob(
        ["src/**/*"],
        exclude = [
            "src/**/*.spec.ts",
            "src/test.ts",
            "dist/",
        ],
    )

    # Get all test src files in the package using this macro.
    test_srcs = srcs + native.glob(["src/test.ts", "src/**/*.spec.ts"])

    project_name = project_name if project_name else native.package_name().split("/").pop()

    # Modifies one of the json files used by ng libraries.
    # NOTE: dist directories are under the project dir instead of the Angular CLI default of the root dist folder
    jq(
        name = "ng-package",
        srcs = ["ng-package.json"],
        filter = JQ_DIST_REPLACE_NG_PACKAGE,
        visibility = ["//visibility:private"],
    )

    # Build target named _name only visible in calling package.
    architect_cli.architect(
        name = "_%s" % name,
        chdir = native.package_name(),
        args = ["%s:build" % project_name],
        out_dirs = ["dist"],
        srcs = srcs + deps + LIBRARY_DEPS + LIBRARY_CONFIG + COMMON_CONFIG + [":ng-package"],
        visibility = ["//visibility:private"],
        **kwargs
    )

    # Test target named :test.
    architect_cli.architect_test(
        name = "test",
        chdir = native.package_name(),
        args = ["%s:test" % project_name, "--no-watch"],
        data = test_srcs + deps + test_deps + TEST_DEPS + TEST_CONFIG + COMMON_CONFIG + [":ng-package"],
        log_level = "debug",
        **kwargs
    )

    # Output the compiled library and its dependencies as {name}.
    js_library(
        name = name,
        srcs = [":_%s" % name],
        deps = deps + LIBRARY_DEPS,
    )
