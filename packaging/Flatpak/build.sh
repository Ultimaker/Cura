#!/bin/bash
# Build script for UltiMaker Cura Flatpak
# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

set -e

# Configuration
FLATPAK_DIR="$(dirname "$(realpath "$0")")"
REPO_DIR="$(dirname "$(dirname "$FLATPAK_DIR")")"
BUILD_DIR="${BUILD_DIR:-/tmp/flatpak-cura-build}"
INSTALL_DIR="${INSTALL_DIR:-/tmp/flatpak-cura-install}"
REPO_NAME="${REPO_NAME:-cura-repo}"
APP_ID="com.ultimaker.cura"

# Conan and build configuration
CURA_CONAN_VERSION="${CURA_CONAN_VERSION:-}"
CONAN_ARGS="${CONAN_ARGS:-}"
ENTERPRISE="${ENTERPRISE:-false}"
STAGING="${STAGING:-false}"
PRIVATE_DATA="${PRIVATE_DATA:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v flatpak-builder &> /dev/null; then
        log_error "flatpak-builder not found. Please install it."
        exit 1
    fi
    
    if ! command -v flatpak &> /dev/null; then
        log_error "flatpak not found. Please install it."
        exit 1
    fi
    
    if ! command -v conan &> /dev/null; then
        log_error "conan not found. Please install it."
        log_error "Run: pip install conan"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found. Please install it."
        exit 1
    fi
    
    log_info "Dependencies check passed."
}

# Setup Conan
setup_conan() {
    log_info "Setting up Conan..."
    
    # Create Conan profile if it doesn't exist
    if ! conan profile detect --force; then
        log_error "Failed to create Conan profile"
        exit 1
    fi
    
    log_info "Conan setup completed."
}

# Setup required runtimes
setup_runtimes() {
    log_info "Setting up Flatpak runtimes..."
    
    # Add Flathub repository if not already added
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo --user
    
    # Install required runtime and SDK
    flatpak install -y --user flathub org.kde.Platform//6.7 || log_warn "Runtime may already be installed"
    flatpak install -y --user flathub org.kde.Sdk//6.7 || log_warn "SDK may already be installed"
}

# Build Cura with Conan and PyInstaller
build_cura_distribution() {
    log_info "Building Cura distribution with Conan and PyInstaller..."
    
    cd "$REPO_DIR"
    
    # Clean previous builds
    rm -rf cura_inst dist
    
    # Determine Cura version to build
    local cura_version="cura/$(python3 -c "import sys; sys.path.append('.'); from CuraVersion import CuraVersion; print(CuraVersion)")@ultimaker/testing"
    if [ -n "$CURA_CONAN_VERSION" ]; then
        cura_version="$CURA_CONAN_VERSION"
    fi
    
    log_info "Building Cura version: $cura_version"
    
    # Prepare Conan arguments
    local conan_cmd="conan install --requires \"$cura_version\" $CONAN_ARGS --build=missing --update -of cura_inst --deployer-package=\"*\""
    
    # Add enterprise/staging/private flags
    if [ "$ENTERPRISE" = "true" ]; then
        conan_cmd="$conan_cmd -o \"cura/*:enterprise=True\""
    fi
    if [ "$STAGING" = "true" ]; then
        conan_cmd="$conan_cmd -o \"cura/*:staging=True\""
    fi
    if [ "$PRIVATE_DATA" = "true" ]; then
        conan_cmd="$conan_cmd -o \"cura/*:internal=True\""
    fi
    
    # Install dependencies with Conan
    log_info "Installing dependencies with Conan..."
    eval $conan_cmd
    
    # Activate Conan environment
    source cura_inst/conanrun.sh
    
    # Create virtual environment for PyInstaller
    python3 -m venv cura_installer_venv
    source cura_installer_venv/bin/activate
    
    # Install PyInstaller requirements
    if ls cura_inst/packaging/pip_requirements_*core*.txt 1> /dev/null 2>&1; then
        pip install -r cura_inst/packaging/pip_requirements_*core*.txt
    fi
    if ls cura_inst/packaging/pip_requirements_*installer*.txt 1> /dev/null 2>&1; then
        pip install -r cura_inst/packaging/pip_requirements_*installer*.txt
    fi
    
    # Create the distribution with PyInstaller
    log_info "Creating distribution with PyInstaller..."
    if [ -f "cura_inst/UltiMaker-Cura.spec" ]; then
        pyinstaller ./cura_inst/UltiMaker-Cura.spec
    else
        log_error "PyInstaller spec file not found at cura_inst/UltiMaker-Cura.spec"
        exit 1
    fi
    
    # Deactivate virtual environment
    deactivate
    
    log_info "Cura distribution built successfully at dist/UltiMaker-Cura/"
}

# Build the Flatpak
build_flatpak() {
    log_info "Building Flatpak..."
    
    # Ensure Cura distribution exists
    if [ ! -d "$REPO_DIR/dist/UltiMaker-Cura" ]; then
        log_error "Cura distribution not found at dist/UltiMaker-Cura/"
        log_error "Please run 'build-conan' first or 'all' to build everything."
        exit 1
    fi
    
    # Clean previous build
    rm -rf "$BUILD_DIR" "$INSTALL_DIR"
    mkdir -p "$BUILD_DIR" "$INSTALL_DIR"
    
    cd "$REPO_DIR"
    
    # Build the Flatpak
    flatpak-builder \
        --force-clean \
        --ccache \
        --require-changes \
        --repo="$BUILD_DIR/$REPO_NAME" \
        --arch="$(flatpak --default-arch)" \
        "$INSTALL_DIR" \
        "packaging/Flatpak/${APP_ID}.json"
    
    log_info "Flatpak build completed successfully!"
}

# Install the Flatpak locally
install_flatpak() {
    log_info "Installing Flatpak locally..."
    
    # Add local repository
    flatpak remote-add --if-not-exists --user cura-local "$BUILD_DIR/$REPO_NAME" --no-gpg-verify
    
    # Install the application
    flatpak install -y --user cura-local "$APP_ID"
    
    log_info "Flatpak installed successfully!"
}

# Run the application
run_flatpak() {
    log_info "Running UltiMaker Cura..."
    flatpak run "$APP_ID"
}

# Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR" "$INSTALL_DIR" "$REPO_DIR/cura_inst" "$REPO_DIR/dist" "$REPO_DIR/cura_installer_venv"
    log_info "Cleanup completed."
}

# Main function
main() {
    case "${1:-help}" in
        "check")
            check_dependencies
            ;;
        "setup")
            check_dependencies
            setup_conan
            setup_runtimes
            ;;
        "build-conan")
            check_dependencies
            setup_conan
            build_cura_distribution
            ;;
        "build-flatpak")
            check_dependencies
            setup_runtimes
            build_flatpak
            ;;
        "build")
            # Build everything
            check_dependencies
            setup_conan
            setup_runtimes
            build_cura_distribution
            build_flatpak
            ;;
        "install")
            install_flatpak
            ;;
        "run")
            run_flatpak
            ;;
        "clean")
            clean
            ;;
        "all")
            check_dependencies
            setup_conan
            setup_runtimes
            build_cura_distribution
            build_flatpak
            install_flatpak
            ;;
        *)
            echo "Usage: $0 [check|setup|build-conan|build-flatpak|build|install|run|clean|all]"
            echo ""
            echo "Commands:"
            echo "  check        - Check for required dependencies (Conan, Flatpak, Python)"
            echo "  setup        - Setup Conan and Flatpak runtimes"
            echo "  build-conan  - Build Cura distribution using Conan + PyInstaller"
            echo "  build-flatpak- Build Flatpak from existing Cura distribution"
            echo "  build        - Build Cura distribution and Flatpak package"
            echo "  install      - Install the built Flatpak locally"
            echo "  run          - Run the installed Flatpak"
            echo "  clean        - Clean all build artifacts"
            echo "  all          - Run complete build and install process"
            echo ""
            echo "Environment variables:"
            echo "  CURA_CONAN_VERSION - Specific Cura Conan version to build"
            echo "  CONAN_ARGS         - Additional Conan arguments"
            echo "  ENTERPRISE         - Set to 'true' for Enterprise build"
            echo "  STAGING            - Set to 'true' to use staging API"
            echo "  PRIVATE_DATA       - Set to 'true' for internal build"
            exit 1
            ;;
    esac
}

main "$@"