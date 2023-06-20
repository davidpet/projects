SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/../../setup/java-tools.sh"

echo "Formatting Java Files: $@"

format-java "$@"
