#!/usr/bin/env bash
#
# OpenGolfCoach Rust Extension Installer
# Automatically downloads and installs the appropriate wheel for your platform
#
# Usage:
#   ./install_rust_extension.sh                          # Auto-download from latest release
#   ./install_rust_extension.sh /path/to/wheel.whl       # Install from local file
#   ./install_rust_extension.sh --version 0.2.0          # Specify version to download
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="TaylorOpenLaunch"
REPO_NAME="homeassistant-opengolfcoach"
PACKAGE_NAME="opengolfcoach_rust"
DEFAULT_VERSION="latest"

# Print colored message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [WHEEL_FILE]

Install OpenGolfCoach Rust extension for Home Assistant

OPTIONS:
    --version VERSION    Specify version to download (default: latest)
    --help              Show this help message

EXAMPLES:
    $0                                      # Auto-download latest release
    $0 --version 0.2.0                     # Download specific version
    $0 /path/to/opengolfcoach_rust.whl     # Install from local file

EOF
}

# Detect platform
detect_platform() {
    local os arch platform_tag

    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)

    case "$os" in
        linux)
            # Check if running on Home Assistant OS (Alpine Linux)
            local is_haos=false
            if [ -f "/etc/os-release" ]; then
                if grep -qi "alpine" /etc/os-release 2>/dev/null || [ -f "/usr/src/homeassistant/bin/python" ]; then
                    is_haos=true
                fi
            fi

            case "$arch" in
                x86_64)
                    if [ "$is_haos" = true ]; then
                        platform_tag="musllinux_1_2_x86_64"
                        print_info "Detected Home Assistant OS (Alpine Linux)"
                    else
                        platform_tag="manylinux_2_28_x86_64"
                    fi
                    ;;
                aarch64|arm64)
                    if [ "$is_haos" = true ]; then
                        platform_tag="musllinux_1_2_aarch64"
                        print_info "Detected Home Assistant OS (Alpine Linux)"
                    else
                        platform_tag="manylinux_2_28_aarch64"
                    fi
                    ;;
                *)
                    print_error "Unsupported Linux architecture: $arch"
                    exit 1
                    ;;
            esac
            ;;
        darwin)
            case "$arch" in
                x86_64)
                    platform_tag="macosx_11_0_x86_64"
                    ;;
                arm64)
                    platform_tag="macosx_11_0_arm64"
                    ;;
                *)
                    print_error "Unsupported macOS architecture: $arch"
                    exit 1
                    ;;
            esac
            ;;
        mingw*|msys*|cygwin*)
            platform_tag="win_amd64"
            ;;
        *)
            print_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac

    echo "$platform_tag"
}

# Detect Python version
detect_python_version() {
    local python_cmd python_version is_ha_python

    # Try Home Assistant Python path first
    if [ -f "/usr/src/homeassistant/bin/python" ]; then
        python_cmd="/usr/src/homeassistant/bin/python"
        is_ha_python=true
    elif command -v python3 &> /dev/null; then
        python_cmd="python3"
        is_ha_python=false
    elif command -v python &> /dev/null; then
        python_cmd="python"
        is_ha_python=false
    else
        print_error "Python not found. Please install Python 3.9 or later."
        exit 1
    fi

    # Get Python version (e.g., "311" for Python 3.11) - suppress stderr
    python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')" 2>/dev/null)

    # Print AFTER capturing the version (to avoid polluting the output)
    if [ "$is_ha_python" = true ]; then
        print_info "Found Home Assistant Python: $python_cmd"
    else
        print_info "Using system Python: $python_cmd"
    fi
    print_info "Detected Python version: cp${python_version}"

    # Verify minimum version (Python 3.9 = version 39)
    if [ "$python_version" -lt 39 ]; then
        print_error "Python 3.9 or later is required. Found: Python 3.${python_version#3}"
        exit 1
    fi

    echo "$python_version"
}

# Download wheel from GitHub Releases
download_wheel() {
    local version="$1"
    local platform="$2"
    local py_version="$3"
    local wheel_name release_url download_url temp_dir

    # Build wheel filename
    wheel_name="${PACKAGE_NAME}-${version}-cp${py_version}-cp${py_version}-${platform}.whl"

    print_info "Looking for wheel: $wheel_name"

    # Get release URL
    if [ "$version" = "latest" ]; then
        release_url="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest"
    else
        release_url="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/tags/v${version}"
    fi

    print_info "Fetching release information from GitHub..."

    # Get download URL from GitHub API
    download_url=$(curl -sSL "$release_url" | grep -o "https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/[^\"]*${wheel_name}" | head -n1)

    if [ -z "$download_url" ]; then
        print_error "Could not find wheel for your platform in release"
        print_error "Platform: $platform"
        print_error "Python: $py_version"
        print_error ""
        print_info "You may need to build from source. See:"
        print_info "https://github.com/${REPO_OWNER}/${REPO_NAME}#installation"
        exit 1
    fi

    # Download to temp directory
    temp_dir=$(mktemp -d)
    local wheel_path="${temp_dir}/${wheel_name}"

    print_info "Downloading from: $download_url"

    if ! curl -sSL -o "$wheel_path" "$download_url"; then
        print_error "Failed to download wheel"
        rm -rf "$temp_dir"
        exit 1
    fi

    print_success "Downloaded: $wheel_name"
    echo "$wheel_path"
}

# Install wheel
install_wheel() {
    local wheel_path="$1"
    local python_cmd pip_cmd

    # Determine Python command
    if [ -f "/usr/src/homeassistant/bin/python" ]; then
        python_cmd="/usr/src/homeassistant/bin/python"
        pip_cmd="/usr/src/homeassistant/bin/pip"
    elif command -v python3 &> /dev/null; then
        python_cmd="python3"
        pip_cmd="pip3"
    else
        python_cmd="python"
        pip_cmd="pip"
    fi

    print_info "Installing wheel with: $pip_cmd"

    if ! $pip_cmd install --force-reinstall "$wheel_path"; then
        print_error "Failed to install wheel"
        print_error "Try activating your Home Assistant Python environment:"
        print_error "  source /usr/src/homeassistant/bin/activate"
        exit 1
    fi

    print_success "Wheel installed successfully"

    # Verify installation
    print_info "Verifying installation..."

    if $python_cmd -c "import ${PACKAGE_NAME}; print('${PACKAGE_NAME} version:', ${PACKAGE_NAME}.__version__ if hasattr(${PACKAGE_NAME}, '__version__') else 'unknown')" 2>/dev/null; then
        print_success "Installation verified: ${PACKAGE_NAME} is importable"
        return 0
    else
        print_warning "Wheel installed but import verification failed"
        print_warning "This may be normal if you're not in the HA environment"
        return 1
    fi
}

# Main installation flow
main() {
    local version="$DEFAULT_VERSION"
    local wheel_path=""
    local platform py_version
    local cleanup_wheel=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                version="$2"
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                wheel_path="$1"
                shift
                ;;
        esac
    done

    echo ""
    print_info "OpenGolfCoach Rust Extension Installer"
    echo ""

    # If wheel path provided, use it directly
    if [ -n "$wheel_path" ]; then
        if [ ! -f "$wheel_path" ]; then
            print_error "Wheel file not found: $wheel_path"
            exit 1
        fi
        print_info "Using local wheel: $wheel_path"
    else
        # Auto-download
        print_info "Detecting platform..."
        platform=$(detect_platform)
        print_success "Platform: $platform"

        print_info "Detecting Python version..."
        py_version=$(detect_python_version)
        print_success "Python: cp${py_version}"

        wheel_path=$(download_wheel "$version" "$platform" "$py_version")
        cleanup_wheel=true
    fi

    echo ""
    install_wheel "$wheel_path"

    # Cleanup temp wheel if we downloaded it
    if [ "$cleanup_wheel" = true ] && [ -f "$wheel_path" ]; then
        rm -f "$wheel_path"
        rmdir "$(dirname "$wheel_path")" 2>/dev/null || true
    fi

    echo ""
    print_success "Installation complete!"
    echo ""
    print_info "Next steps:"
    print_info "  1. Restart Home Assistant"
    print_info "  2. Install the integration via HACS"
    print_info "  3. Configure Open Golf Coach in Settings → Integrations"
    echo ""
}

# Run main function
main "$@"
