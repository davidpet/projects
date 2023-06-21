SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/../../setup/python-tools.sh"

echo "Linting Python Files: $@"

lint-python "$@"
