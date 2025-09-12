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
    
    log_info "Dependencies check passed."
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

# Build the Flatpak
build_flatpak() {
    log_info "Building Flatpak..."
    
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
    rm -rf "$BUILD_DIR" "$INSTALL_DIR"
    log_info "Cleanup completed."
}

# Main function
main() {
    case "${1:-build}" in
        "check")
            check_dependencies
            ;;
        "setup")
            check_dependencies
            setup_runtimes
            ;;
        "build")
            check_dependencies
            setup_runtimes
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
            setup_runtimes
            build_flatpak
            install_flatpak
            ;;
        *)
            echo "Usage: $0 [check|setup|build|install|run|clean|all]"
            echo ""
            echo "Commands:"
            echo "  check   - Check for required dependencies"
            echo "  setup   - Setup required Flatpak runtimes"
            echo "  build   - Build the Flatpak package"
            echo "  install - Install the built Flatpak locally"
            echo "  run     - Run the installed Flatpak"
            echo "  clean   - Clean build artifacts"
            echo "  all     - Run setup, build, and install in sequence"
            exit 1
            ;;
    esac
}

main "$@"