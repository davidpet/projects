SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/../../setup/python-tools.sh"

echo "Formatting Python Files: $@"

format-python "$@"
