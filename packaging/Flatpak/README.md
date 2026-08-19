# UltiMaker Cura Flatpak Package

This directory contains the necessary files to build UltiMaker Cura as a Flatpak package for Linux distributions.

## Overview

Flatpak is a universal package format for Linux that provides sandboxed applications with consistent dependencies across different distributions. This packaging allows Cura to run on any Linux distribution that supports Flatpak.

**Build Process**: This Flatpak implementation follows the same build workflow as the AppImage packaging:

1. **Conan Dependencies**: Uses Conan to install and build all required dependencies
2. **PyInstaller Distribution**: Creates a packaged application using PyInstaller 
3. **Flatpak Packaging**: Packages the PyInstaller distribution into a Flatpak

This ensures consistency with the existing build infrastructure and leverages the proven Conan dependency chain.

## Files

- `com.ultimaker.cura.json` - Flatpak manifest that packages PyInstaller distribution
- `cura.desktop` - Desktop entry file for application launcher integration
- `cura.appdata.xml` - AppStream metadata for software centers  
- `build.sh` - Build script with Conan + PyInstaller + Flatpak workflow
- `README.md` - This documentation file
- `LIMITATIONS.md` - Current limitations and future improvements

## Prerequisites

1. **Python 3**: Python 3.8 or newer with pip
   ```bash
   # Ubuntu/Debian
   sudo apt install python3 python3-pip python3-venv
   
   # Fedora  
   sudo dnf install python3 python3-pip
   
   # Arch Linux
   sudo pacman -S python python-pip
   ```

2. **Conan**: Install Conan package manager
   ```bash
   pip install conan
   ```

3. **Flatpak**: Install Flatpak on your system
   ```bash
   # Ubuntu/Debian
   sudo apt install flatpak
   
   # Fedora
   sudo dnf install flatpak
   
   # Arch Linux
   sudo pacman -S flatpak
   ```

4. **Flatpak Builder**: Install the Flatpak builder tool
   ```bash
   # Ubuntu/Debian
   sudo apt install flatpak-builder
   
   # Fedora
   sudo dnf install flatpak-builder
   
   # Arch Linux
   sudo pacman -S flatpak-builder
   ```

5. **Development Tools**: GCC, CMake, and other build tools
   ```bash
   # Ubuntu/Debian
   sudo apt install build-essential cmake git
   
   # Fedora
   sudo dnf groupinstall "Development Tools" && sudo dnf install cmake git
   
   # Arch Linux  
   sudo pacman -S base-devel cmake git
   ```

## Building the Flatpak

### Automated Build

Use the provided build script for the easiest build process:

```bash
# From the repository root
cd packaging/Flatpak

# Build everything (setup, build Conan + PyInstaller, build Flatpak, install)
./build.sh all

# Or step by step:
./build.sh check       # Check dependencies (Conan, Flatpak, Python)
./build.sh setup       # Setup Conan profiles and Flatpak runtimes
./build.sh build-conan # Build Cura with Conan + PyInstaller  
./build.sh build-flatpak # Build Flatpak from PyInstaller distribution
./build.sh install     # Install Flatpak locally
./build.sh run         # Run the application
```

### Environment Variables

The build script supports several environment variables for customization:

```bash
# Specify a particular Cura version
export CURA_CONAN_VERSION="cura/5.6.0@ultimaker/stable"

# Enterprise build
export ENTERPRISE=true

# Staging API
export STAGING=true  

# Private/internal data
export PRIVATE_DATA=true

# Additional Conan arguments
export CONAN_ARGS="--profile myprofile"

./build.sh build
```

### Manual Build

If you prefer to build manually, the process involves three stages:

**Stage 1: Build Cura Distribution**
```bash
cd /path/to/Cura/repository

# Install dependencies with Conan
conan install --requires "cura/latest@ultimaker/testing" --build=missing --update -of cura_inst --deployer-package="*"

# Activate Conan environment and build with PyInstaller
source cura_inst/conanrun.sh
python3 -m venv cura_installer_venv
source cura_installer_venv/bin/activate
pip install -r cura_inst/packaging/pip_requirements_*core*.txt
pip install -r cura_inst/packaging/pip_requirements_*installer*.txt
pyinstaller ./cura_inst/UltiMaker-Cura.spec
```

**Stage 2: Setup Flatpak Environment**
```bash
flatpak install --user flathub org.kde.Platform//6.7
flatpak install --user flathub org.kde.Sdk//6.7
```

**Stage 3: Build Flatpak**
```bash
# Build Flatpak from PyInstaller distribution
flatpak-builder --force-clean --repo=/tmp/cura-repo /tmp/cura-build packaging/Flatpak/com.ultimaker.cura.json

# Install locally
flatpak remote-add --user --no-gpg-verify cura-local /tmp/cura-repo
flatpak install --user cura-local com.ultimaker.cura
```

## Running Cura

After installation, you can run Cura in several ways:

1. **From the application menu**: Look for "UltiMaker Cura" in your desktop environment's application menu

2. **From command line**:
   ```bash
   flatpak run com.ultimaker.cura
   ```

3. **Using the build script**:
   ```bash
   ./build.sh run
   ```

## Architecture

### Build Process Flow

This Flatpak implementation follows the same workflow as the AppImage:

1. **Conan Dependencies**: Uses Conan to install and build all required dependencies including CuraEngine, PyQt6, and other native libraries
2. **PyInstaller Distribution**: Creates a self-contained application bundle using PyInstaller with all Python dependencies
3. **Flatpak Packaging**: Packages the PyInstaller distribution into a Flatpak with proper sandboxing and desktop integration

### Flatpak Manifest Structure

The `com.ultimaker.cura.json` manifest defines:
- **Runtime**: Uses `org.kde.Platform` 6.7 for Qt6 and KDE integration
- **Permissions**: Filesystem access, graphics acceleration, network access
- **Modules**: Packages the pre-built PyInstaller distribution
- **Desktop Integration**: Icons, MIME types, and application metadata

### Directory Structure

After building, the directory structure looks like:
```
/app/
├── UltiMaker-Cura           # Main executable (from PyInstaller)
├── lib/                     # Libraries and dependencies (from PyInstaller)
├── share/
│   ├── applications/        # Desktop files
│   ├── metainfo/           # AppStream metadata
│   ├── icons/              # Application icons
│   └── cura/               # MIME type information
└── ...                     # Other PyInstaller artifacts
```

## Permissions

The Flatpak has the following permissions:
- **Graphics**: Hardware acceleration (DRI), X11, Wayland
- **Filesystem**: Home directory, common media locations, desktop/documents folders
- **System Integration**: File manager, desktop portals

## Troubleshooting

### Build Issues

1. **Missing dependencies**: Ensure Conan, Python, and build tools are installed
2. **Conan profile issues**: Run `./build.sh setup` to configure Conan profiles
3. **PyInstaller failures**: Check that all pip requirements are installed
4. **Flatpak runtime not found**: Run `./build.sh setup` to install required runtimes

### Runtime Issues

1. **Application won't start**: Check if all dependencies were properly bundled by PyInstaller
2. **File access issues**: Verify filesystem permissions in the manifest
3. **Library loading problems**: The PyInstaller bundle should contain all required libraries

### Debugging

To debug the application:
```bash
# Run with debug output
flatpak run --devel --command=sh com.ultimaker.cura
# Then inside the sandbox:
./UltiMaker-Cura
```

You can also inspect the PyInstaller distribution before packaging:
```bash
# After running build-conan
ls -la dist/UltiMaker-Cura/
./dist/UltiMaker-Cura/UltiMaker-Cura  # Test directly
```

## Integration with Existing Build Infrastructure

This Flatpak implementation is designed to integrate with Cura's existing build infrastructure:

- **Same Dependencies**: Uses the exact same Conan packages and versions as AppImage
- **Same Build Process**: Follows the same Conan → PyInstaller workflow
- **Same Metadata**: Shares desktop files, icons, and AppData with AppImage
- **Same Application ID**: Uses `com.ultimaker.cura` for consistency

The only difference is the final packaging step: instead of creating an AppImage, the PyInstaller distribution is packaged into a Flatpak.

## CI/CD Integration

This Flatpak build process can be integrated into GitHub Actions workflows similarly to the AppImage:

```yaml
- name: Build Cura Flatpak
  run: |
    cd packaging/Flatpak
    ./build.sh build
    
- name: Upload Flatpak
  uses: actions/upload-artifact@v4
  with:
    name: UltiMaker-Cura-Flatpak
    path: /tmp/flatpak-cura-build/cura-repo/
```

## Contributing

When making changes to the Flatpak packaging:
1. Test the build process on multiple distributions
2. Verify that all application features work correctly
3. Update this README if you add new files or change the build process
4. Ensure consistency with the AppImage build workflow

## License

UltiMaker Cura is released under the terms of the LGPLv3 or higher.
The Flatpak packaging files in this directory are also licensed under LGPLv3.