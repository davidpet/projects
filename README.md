# Bazel Setup

## Mac

`brew install bazel` then restart the shell.

## Linux

Follow instructions at https://bazel.build/install/ubuntu and ignore apt-transport-https failure.

## Windows

Download the binary and put it somewhere in the PATH or that can be referenced directly (eg. C:\bazel.exe).

## Verifying

`bazel --version`

# Environment Setup for TensorFlow on GPU

In order to run any code/tests that involve TensorFlow in Python (and have it execute on GPU).

## MacOS (M1)

### Base Environment

One-time steps for your Mac machine:

1. Install Xcode command line tools which includes stuff like make:

   `xcode-select --install`

1. Install the Apple Silicon version of Conda/Miniforge from here: https://github.com/conda-forge/miniforge

1. If you don't like for conda to always activate the default environment for every shell session, run this once to disable that:

   `conda config --set auto_activate_base false`

### Conda Environment

Each time you need to create/re-create a conda environment:

1. Create a conda environment with Python 3.10. Ideally, we want to use 3.11, but tensorflow-deps currently doesn't support it. As soon as it does, we will move to it. For instance, to create an environment called 'ai' using Python 3.10:

   `conda create -n ai python=3.10`

1. Activate the environment for the next steps:

   `conda activate ai`

1. Install dependencies built for M1 in Apple's repo that make TensorFlow GPU possible on Mac M1:

   `conda install -c apple tensorflow-deps`

   Note that this includes some packages (built for M1) already that we would normally install separately, including:

   - numpy
   - grpcio
   - protobuf

1. Take note of grpcio and protobuf versions because due to an issue with how the packages are set up, we will have to restore them later:

   `conda list`

1. Install TensorFlow and Metal (Mac equivalent of CUDA) from the Apple team. Why you have to do this via pip instead of conda (which won't work) I cannot begin to guess.

   `pip install tensorflow-macos tensorflow-metal`

   As a side effect of this, grpcio and protobuf get upgraded to later versions, but via pip, which means they're not built for M1 anymore and will fail if used. You have to do some extra work to restore them to a working state. You can see the issue by running `python3 -m grpc` - if grpcio is working correctly, you should only see an error about importing modules, rather than a C++ compilation error, which is what you get when it's not built for M1.

1. Restore grpcio and protobuf to a working state. In this example, I assumed two specific versions of these libraries based on last time I did this. You should adjust based on the versions you noted from `conda list` above.

   `pip uninstall grpcio protobuf`  
   `conda install protobuf==3.19.6 grpcio==1.46.3`  
   `python3 -m grpc`

   The result of the last command should be an error about importing modules, not a C++ error.

   Note that this is downgrading the version of grpcio and protobuf from what tensorflow-macos installs, but making it match what tensorflow-deps installs. This is an inconsistency created by the process from the Apple team and cannot be resolved by us. It's possible there might be some side effects of the version mismatch within TensorFlow but it's hard to say.

1. Proceed with `All Environments` steps below.

## Windows

### CUDA+Conda Environment

1. Update your video driver.

1. Install the Windows version of Conda/Miniforge from here: https://github.com/conda-forge/miniforge

1. Follow [these instructions](https://towardsdatascience.com/how-to-finally-install-tensorflow-gpu-on-windows-10-63527910f255) which will get you to create a Conda environment (use the proper python version instead of 3.8 in the example) and install TensorFlow. While following these instructions, note the following:

   1. As of 5/8/23, these were the versions:
      - TF 2.12.0
      - Python 3.11
      - CUDA 11.8
      - cuDNN 8.6
   1. While installing CUDA toolkit, you only need to check the stuff under category "CUDA." Do not check anything that has a "current version" listed - especially "display driver" which will overwrite your driver with an old one if you check it.
   1. If you get an error during installation about Visual Studio version, you need to install an older version (eg. 2019). It can coexist with the newer versions.
   1. You may have to install TensorFlow 2.10 instead of the newer versions on Windows because TensorFlow 2.11 abandoned support for Windows GPU execution. You can still use the dependencies for later TensorFlow if you are planning to run in WSL/Linux - the TensorFlow on your Windows system is mostly only for making sure the CUDA stuff can load in that case. If you want to see whether the installed version of TensorFlow has CUDA support (regardless of whether it's actually set up on the system): `tf.test.is_built_with_cuda()`
   1. Instead of jupyter labs like in the instructions, install `notebook` and use `python -m notebook` to run it. This is different from both Mac and Linux.

1. Resume with the `All Environments` steps below as needed.
   1. You can skip the jupyter installation step.
   1. To run the jupyter notebook, you will need to copy it into your home directory because that's how jupyter works on Windows.
   1. If you are just setting up on Windows for the benefit of WSL/Linux, you can probably stop after running the benchmark and not bother to set up the rest of the libraries, as you're going to set them up in WSL/Linux again.

## Linux/WSL

### Base Environment

1. Follow `Windows` setup first so that the host system has working CUDA tools that will be needed. Note that the TensorFlow from the host system will not be used in Linux, so it's ok if the version doesn't match. Make sure the Windows environment has the right CUDA versions for the version of TF you want to install in Linux.

1. miniforge doesn’t seem to work for me in this context, so install miniconda instead
   1. `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
   1. `bash Miniconda3-latest-Linux-x86_64.sh`
      NOTE: you still get conda, so things like sharing yaml environments between mac and pc should still work
   1. When prompted, pick a non-symlinked install location instead of ~. Otherwise, environment creation will fail.
      eg. /home/davidpet
   1. Other things like .condarc being in ~ still seem to work
1. If you don't want conda to auto-activate on each shell session: `conda config --set auto_activate_base false`

### Conda Environment

1. Follow [these steps](https://www.tensorflow.org/install/pip?_gl=1*o4xwez*_ga*NzIxMzA4OTEyLjE2NzQzMDkwMjA.*_ga_W0YLR4190T*MTY3NTE2NDMyMC4xMy4xLjE2NzUxNjYwNzcuMC4wLjA.#windows-wsl2_1) to set up a Conda environment with CUDA and TensorFlow setup. You should use the same CUDA and toolkit version as the windows host, and then they'll be able to communicate so that the Linux TF can use the GPU. Note the following caveats:

   1. You need to reactivate the conda environment after the “export” step or it won’t apply the variables when you test tensorflow.
   1. You get annoying numa errors in repl, but it shouldn’t affect anything
      eg. in notebook you won’t see the errors from imports
   1. Although we're stuck with Python 3.10 on Mac for now, I've been using 3.11 on Linux because I want the performance improvements. Hopefully this inconsistency won't last long.

1. Resume with the `All Environments` steps below for each conda environment you create, but note that you have to do some extra work to get Jupyter notebooks to work:

   1. `pip install –upgrade cchardet Cython chardet`
   1. Add `export JUPYTER_ALLOW_INSECURE_WRITES=true` to your .bashrc
   1. When calling jupyter from the shell, add the `--no-browser` flag (eg. make an alias in your .bashrc). This is needed because Jupyter run from WSL Linux will try to use the WSL Linux browser instead of the Windows one. So instead, you need to copy and paste the url (it changes, so don't bookmark it) into your browser to load the jupyter UI.

## Linux (native)

I haven't tried this yet because I use a Macbook and a PC w/ WSL, but it should work similarly to the Mac setup above but with `tensorflow-gpu` instead of `tensorflow-macos`. None of the other Apple conda stuff should be needed since it has nothing to do with Apple. See [here](https://hackmd.io/@husohome/Byb6kP6WP#:~:text=Thus%2C%20all%20you%20have%20to,gpu%20%2C%20which%20should%20do%20it)

## All Environments

These are steps that should be performed next (for each conda environment you create) regardless of whether you're on a Mac, Linux, etc:

1. `conda install jupyter`
1. At this point, Tensorflow should be runnable on the GPU regardless of OS. To check that, run [this notebook](https://github.com/davidpet/tutorials/blob/master/Jupyter/benchmark.ipynb) using a command such as `jupyter notebook --notebook-dir=~/repos/tutorials/Jupyter`. Follow the instructions in the text cells to tailor it to your environment slightly (eg. Import a DLL on Windows, change to legacy Adam on Mac, etc.). If it works, the output of the last code cell should report 1 GPU available and all 12 training epochs should complete. You can also use the `wall time` as a benchmark to compare your machines or test environment optimizations.

1. `conda install numpy`

   You might not want to do this on Mac to avoid issues with tensorflow-deps (as it already installed a verison of numpy).
   NOTE: TensorFlow might already do this - I'll check next time I rebuild my environment.

1. `conda install pandas`

1. `pip install tensorflow_datasets`

1. The following libraries might be conda-installable to get a better version than pip (need to check next time I rebuild):

   1. `pip install matplotlib`
   1. `pip install scikit-learn`
   1. `pip install unittest (built-in)`
   1. `pip install yapf`
   1. `pip install pylint`
   1. `pip install pytype [on hold until supports 3.11]`
   1. `pip install termcolor`

1. The following should be added to your .bashrc, .bash_profile, etc. to make Python and PyLint work correctly in development:
   1. _PYTHONPATH_ set to the location of this repo so that you can import modules relative to it.
   1. _PYLINTRC_ set to the .pylintrc file in this repo (TODO: revisit this procedure later).

# Environment Setup for OpenAI API

In order to run [openai_apy.py](machine_learning/common/openai_api.py) and any targets that use it, the following needs to be set up.

NOTE: technically the grpcio-tools part is not needed to run that api but is needed for the apps that use it in order to really make use of it (to allow for client/server communication). If just running python code to call openai, that step can be skipped.

1. Create a conda environment with Python 3.11.
1. If going to generate Jupyter notebooks (eg. via SnippetMaster), `conda install jupyter` (if didn't already do it from TensorFlow setup).
1. `pip install termcolor`
1. `pip install python_dotnev`
1. `pip install openai`
1. If on Mac, and you already installed TensorFlow for GPU, make sure to fix the damaged grpcio and protobuf libraries as described in that setup above.
1. `conda install grpcio-tools`
   This will install grpcio and protobuf as well if you don't have them yet.

   NOTE: if you installed TensorFlow GPU stuff and are on a Mac, this won't work, so you will have to do it in a separate Conda environment.

   NOTE: I currently have it set up so that you have to have a conda environment called `bazel-protoc` with grpcio-tools that bazel builds will call into for compiling python protobufs/grpc. That is because you can't have tensorflow and grpcio-tools in the same environment on M1 due to dependency version issues. This environment does not need to be manually activated but is expected by some bazel steps.

   NOTE: I am currently building the grpc stuff with the newest but using the older one to run it - that may cause issues

   - there is no other way because grpcio-tools on conda doesn't support old grpcio
   - if any issues are noted later, I might have to look into docker-izing specific parts of the repo or something
     - or let some things be broken on Mac, which would get rid of these issues, but since I use my Mac a lot, that would suck

1. Before running any openai API stuff, you need to have a file `~/openai.env` containing `OPENAI_API_KEY=` followed by your API key. Do not commit this file to any repo, or people on the internet will steal your money. Alternatively, you could have it as an environment variable to override whatever is in openai.env.

# Environment Setup for Java

TODO: add details here

# Environment Setup for TypeScript/JavaScript/Angular

## JavaScript/NodeJS Setup

1. Install [Nvm](https://github.com/nvm-sh/nvm) via Curl and shell script
   1. It will download some stuff to ~/.nvm and add some stuff to ~/.bashrc (similar to what Conda does)
   1. `command -v nvm` should now output `nvm`
1. `nvm install node`
   Install latest version of Node and auto-activates it on every shell instance (silently). In the simple case, you won't need any other versions and won't need to ever activate/deactivate anything or care about Conda for TS/JS/Angular stuff. The one exception is that you need to activate a conda environment to run _jupyter notebooks_, so that creates a bit of a weird cross-dependency.

   After this step, you should be able to run `node` and `npm` from any new terminal instance without doing anything else. Global npm packages (installed with `npm -g packageName`) will install to subfolders of ~/.nvm). Without -g, they will install to a `node_modules` folder in the current folder or its ancestry.

1. Add JavaScript support to Jupyter Notebooks (assuming jupyter setup as in TensorFlow GPU steps above). This will apply to the current _Conda_ environment.

   `npm install -g ijavascript`

   `ijsinstall`

## TypeScript Setup

1. `npm install -g typescript`

1. `npm install -g ts-node`

   `ts-node` is like `node` in that it gives you a TypeScript REPL.

1. Add TypeScript supprot to Jupyter Notebooks (assuming jupyter setup as in TensorFlow GPU steps above). This will apply to the current _Conda_ environment.

   `npm install -g itypescript`

   `its --install=local`

## Angular Setup

1. `npm install -g @angular/cli`
1. You may need to move the ng completion script below the nvm stuff in your .bashrc or .bash_profile.
1. `npm install` in this repo after syncing to make sure all packaged listed in _package.json_ get installed to _node_modules_ locally.

   This is both a one-time and an ongoing step.

## Other Global NPM Packages to Install

1. prettier
1. eslint
1. @typescript-eslint/parser
1. @typescript-eslint/eslint-plugin
1. @jquery
1. pnpm
1. @bazel/ibazel

# VSCode Setup

## General

You probably want to set up setting sync and make a workspace for this repo (at least).

## Bazel

Recommended Extensions:

1. bazel

Other Settings:

1. file association: \*.bazelrc -> shellscript (for syntax highlighting)

## Python

Recommended Extensions:

1.  Python (set the interpreter to the one for your environment)
1.  PyLint
1.  autoDocstring (google style)
1.  TensorFlow 2.0 Snippets
1.  Pandas Basic Snippets
1.  WSL (if on Windows using WSL)

Other Settings:

1.  Set yapf as formatting provider and add the args '--style' and 'google' for yapf

## Java

TBD

## TypeScript/JavaScript/Angular

Recommended Extensions:

1. Angular Essentials (John Papa)

Other Settings:

1. Add this to _settings.json_ so that prettier is used by default formatting except for Python.

```javascript
  editor.defaultFormatter": "esbenp.prettier-vscode", "[python]": {
    "editor.defaultFormatter": "ms-python.python",
  }
```

2. .eslint.js

   TODO: add here from my other repo and make sure it works

# Running Tests

`bazel test //...`

`test.py` was a script I used for testing python before I converted everything to use Bazel.

I'm working on a script to run tests of only changed files relative to the latest git commit, but it's not working yet.

# Before Commiting

TODO: make hook(s)

## Bazel

1. `bazel run //:buildifier`

## Python

There are aliases for these [here](setup/python-tools.sh). There is also a [script](projects/scripts/changed.sh) to format and lint all changed files in all supported languages (in progrss).

1. `yapf --style google --recursive --in-place [repoPath]`
1. `pylint [repoPath]`
   - NOTE: this will catch more things than pylint in VSCode will catch
1. TODO: type checking step when pytype is ready for 3.11
1. Manually run formatting in jupyter notebooks changed

## Java

TODO: add details here

## JS and TS

TODO: add here (using prettier and eslint)

## General

1. `bazel test //...`

   Eventually, I will have a script to only run tests that are necessary for a change.

# Executing

- `machine_learning/spacebot/run_local.sh` to run SpaceBot client and server (both python)
  - see comments [here](machine_learning/spacebot/BUILD) for running client and server separately
- For `Kaggle Titanic` run [this notebook](projects/machine_learning/kaggle_titanic/titanic.ipynb)
- For the web app for SpaceBot, it is still under development, but there will likely be a shell script to spin up the Python server plus an Envoy proxy plus the Angular app (via ng serve).
- For `SnippetMaster`, run `bazel run //machine_learning/snippet_master`. For now, output will be printed to the console and generated in `bazel-bin/machine_learning/snippet_master/snippet_master.runfiles/__main__`. You can manually copy the outline and/or .ipynb files to a snippets repo, for instance. It is generally ok to use ctrl-c to stop in the middle of generation. Notebooks are not written until the end of each notebook, so if you don't kill it right at that moment, it's not likely to cause a problem.
- For `Safron`, run `bazel run //machine_learning/safron`. It will ask you for a debate topic, a number of rounds, a filename, etc. If you don't give a file, it will not write a file. Either way, the results will show at the console. The filename can contain spaces and should not be quoted. It can contain `~` for your home directory. If you don't give the file an extension, it will automatically get a `.txt` extension.

# Angular Workspace

## General Info

The root of this repo is also the root of the Angular workspace due to the presence of angular.json. The repo is set up to build angular via bazel in a hybrid way (can use either `ng` or `bazel` commands and still use schematics).

Angular CLI sees the SpaceBot app as `spacebot-app` (eg. `ng serve spacebot-app`).

The code for the app is located in the `app` folder of the `spacebot` subfolder within the repo.

NPM Dependencies (global):

- pnpm (for generating lock file manually - not used by build yet)

## CLI Version

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 16.0.2.

## Development server

Run `ng serve spacebot-app` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

Run `bazel run //machine_learning/spacebot/app:serve` for the bazel version.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build spacebot-app` to build the project. The build artifacts will be stored in the `dist/` directory.

Run `bazel build //machine_learning/spacebot/app` for the bazel version. The build artifacts will be stored in `bazel-bin/machine_learning/spacebot/app-dist/spacebot-app`.

## Running unit tests

Run `ng test spacebot-app` to execute the unit tests via [Karma](https://karma-runner.github.io).

Run `bazel test //machine_learning/spacebot/app:test` for the bazel version.

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.

# OpenMusic

The [openmusic](openmusic) folder contains Lisp libraries and OpenMusic workspaces using those libraries. It is not currently integrated into Bazel. I'm not even sure storing it in Git is the best thing, since it has a lot of artifacts and system dependencies, but for now this is where I put it.

Requirements to Use:

- Windows (because of how paths are configured)(for now)
- OM 7.1 Installed
- symlinks because OM only likes to use C:\
  - _C:\OpenMusic_ should point to [openmusic/workspaces](openmusic/workspaces)
  - _C:\OpenMusic Code_ should point to [openmusic/libraries](openmusic/libraries)
- any paths you configure or load in OM using these workspaces should be relative to those C:\ symlink paths, not the real paths
- install OM libraries referenced by the workspaces:
  - OM-JI
  - OMRC
  - OMCS
  - Chaos
  - Cloud
  - Situation
  - Profile
  - LZ
  - RepMus
  - Alea
  - Esquisse
  - OMTristan
  - OMio
  - OM-Sox (different process - have to get snapshot from develop branch in Sourceforge)(retrieved on 1/8/23)
- Do "exclude process" if AV (such as Norton) tries to delete PNG of library (such as OMCS) when you load it
- Enable listener input
- If you need to use MIDI, Mac and Windows have separate steps to set up routing for that
  - use Ableton/Serum on Windows and GarageBand on Mac

# ToDo

1. Find all ToDo items throughout the repos and consolidate and/or monitor with some kind of automation.

- in the short term, the most important ones are in the BUILD file for SpaceBot

1. Encapsulate repetitive install steps with scripts where possible.
1. Document the need for extraPaths and manual import fixing to make proto imports work properly in VSCode.
1. Improve SpaceBot prompt injection rejection:

   - Ideas:
     - include more chat context
     - semantic encapsulation (semantic containerization?) - have the AI translate the chat to a story and then write more of the story, then turn back into a chat
     - break the detection into smaller steps with a rubric-like structure and aggregate

1. Possibly Improve SnippetMaster to generate things besides programming languages (eg. library examples).
1. Add tests to SnippetMaster.
1. Web app for SnippetMaster? (maybe not - it his the API key pretty hard)
1. Add option to switch between GPT 3.5 or 4 (since 4 is so expensive)
1. Investigate if using the right model and endpoint for code generation
1. Fix SnippetMaster BUILD file generation (names are invalid)
1. Fix SnipetMaster markdown title spacing and always saying "above"
1. Make table of langauges so far and what SnippetMaster options used (and how found)
1. More SnippetMaster languages: Lisp & Clojure (new FP outline needed), Dart, C#, Bash (scripting outline needed)
1. Next Next Project: tax chatbot for my wife's business

   - at first I thought this wouldn't work because of the GPT knowledge cutoff
   - then after watching deeplearning.ai courses, I realized I can just download (automatically hopefully) the latest tax docs and put into a vector store, then apply the "chatting with your data" course principles

1. Other Possible Projects:

   - domain adapters for using LLM for non-LLM things

     - eg. music melodies
     - idea is that humans learn a lot by language and LLMs have millions of dollars of training to leverage
       - limitation is that some things are also learned by direct sensory experience in addition to or instead of by language

   - get caught up on the new stuff that's been coming out (Llama, etc.)

     - more deeplearning.ai short courses

   - horizontal snippet generator (considering SnippetMaster to be vertical)
     - eg. cmopare what inheriting interface looks like in a list of languages

1. Figure out how to make OpenMusic paths system independent
1. See if getting Lisp and OM into Bazel is desirable and feasible

   - also make Lisp snippets
