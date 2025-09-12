# UltiMaker Cura Flatpak Package

This directory contains the necessary files to build UltiMaker Cura as a Flatpak package for Linux distributions.

## Overview

Flatpak is a universal package format for Linux that provides sandboxed applications with consistent dependencies across different distributions. This packaging allows Cura to run on any Linux distribution that supports Flatpak.

## Files

- `com.ultimaker.cura.json` - Flatpak manifest defining the build process and dependencies
- `cura.desktop` - Desktop entry file for application launcher integration
- `cura.appdata.xml` - AppStream metadata for software centers
- `cura-wrapper` - Shell script wrapper to set up the runtime environment
- `build.sh` - Build script to automate the Flatpak creation process
- `README.md` - This documentation file

## Prerequisites

1. **Flatpak**: Install Flatpak on your system
   ```bash
   # Ubuntu/Debian
   sudo apt install flatpak
   
   # Fedora
   sudo dnf install flatpak
   
   # Arch Linux
   sudo pacman -S flatpak
   ```

2. **Flatpak Builder**: Install the Flatpak builder tool
   ```bash
   # Ubuntu/Debian
   sudo apt install flatpak-builder
   
   # Fedora
   sudo dnf install flatpak-builder
   
   # Arch Linux
   sudo pacman -S flatpak-builder
   ```

3. **Flathub**: Add the Flathub repository (for dependencies)
   ```bash
   flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo --user
   ```

## Building the Flatpak

### Automated Build

Use the provided build script for the easiest build process:

```bash
# From the repository root
cd packaging/Flatpak

# Build everything (setup runtimes, build, and install)
./build.sh all

# Or step by step:
./build.sh check    # Check dependencies
./build.sh setup    # Setup required runtimes
./build.sh build    # Build the Flatpak
./build.sh install  # Install locally
./build.sh run      # Run the application
```

### Manual Build

If you prefer to build manually:

1. **Setup the runtime environment**:
   ```bash
   flatpak install --user flathub org.kde.Platform//6.7
   flatpak install --user flathub org.kde.Sdk//6.7
   ```

2. **Build the Flatpak**:
   ```bash
   cd /path/to/Cura/repository
   flatpak-builder --force-clean --repo=/tmp/cura-repo /tmp/cura-build packaging/Flatpak/com.ultimaker.cura.json
   ```

3. **Install locally**:
   ```bash
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

### Flatpak Manifest Structure

The `com.ultimaker.cura.json` manifest defines:
- **Runtime**: Uses `org.kde.Platform` 6.7 for Qt6 and KDE integration
- **Permissions**: Filesystem access, graphics acceleration, network access
- **Environment**: Python paths, Qt settings, library paths
- **Build modules**: ImageMagick (for image processing) and Cura itself

### Wrapper Script

The `cura-wrapper` script:
- Sets up the Python environment and library paths
- Configures Qt settings for optimal Linux integration
- Launches the Cura application with proper environment isolation

### Desktop Integration

The package provides:
- Application launcher integration via `cura.desktop`
- AppStream metadata for software centers via `cura.appdata.xml`
- MIME type associations for 3D model files
- Icon integration at multiple resolutions

## Permissions

The Flatpak has the following permissions:
- **Graphics**: Hardware acceleration (DRI), X11, Wayland
- **Filesystem**: Home directory, common media locations, desktop/documents folders
- **System Integration**: File manager, desktop portals

## Troubleshooting

### Build Issues

1. **Missing dependencies**: Ensure all prerequisites are installed
2. **Runtime not found**: Run `./build.sh setup` to install required runtimes
3. **Build failures**: Check the build log for specific Python/dependency issues

### Runtime Issues

1. **Application won't start**: Check if the runtime is properly installed
2. **File access issues**: Verify filesystem permissions in the manifest
3. **Qt/GUI problems**: The wrapper sets Qt environment variables for compatibility

### Debugging

To debug the application:
```bash
# Run with debug output
flatpak run --devel --command=sh com.ultimaker.cura
# Then inside the sandbox:
python3 cura_app.py
```

## Integration with AppImage

This Flatpak packaging is inspired by and compatible with the existing AppImage packaging:
- Uses the same application metadata (desktop file, AppData)
- Shares the same icon resources
- Maintains the same application ID (`com.ultimaker.cura`)
- Provides equivalent functionality and user experience

## Contributing

When making changes to the Flatpak packaging:
1. Test the build process on multiple distributions
2. Verify that all application features work correctly
3. Update this README if you add new files or change the build process
4. Consider the impact on both new and existing users

## License

UltiMaker Cura is released under the terms of the LGPLv3 or higher.
The Flatpak packaging files in this directory are also licensed under LGPLv3.