# Flatpak Packaging Limitations

This document outlines current limitations and future improvements for the UltiMaker Cura Flatpak packaging.

## Current Status

The Flatpak implementation follows the same build workflow as AppImage packaging:
- ✅ **Conan Integration**: Uses Conan for dependency management
- ✅ **PyInstaller Distribution**: Creates application using PyInstaller
- ✅ **Desktop Integration**: Full desktop environment integration
- ✅ **Cross-distribution Support**: Works on any Linux with Flatpak

## Known Limitations

### 1. Build Complexity

**Issue**: The build process requires multiple tools (Conan, PyInstaller, Flatpak Builder) and can be complex for contributors.

**Impact**: Higher barrier to entry for building and testing Flatpak packages.

**Future Work**: 
- Containerized build environment using Docker
- Pre-built dependency caches to speed up builds
- Integration with existing CI/CD pipelines

### 2. Size Optimization

**Issue**: PyInstaller bundles can be large due to including all Python dependencies and libraries.

**Impact**: Larger download size compared to distribution-specific packages.

**Future Work**:
- Investigate using Flatpak base apps to share common dependencies
- Optimize PyInstaller exclusions to reduce bundle size
- Consider using separate extension packages for optional components

### 3. Sandboxing Limitations

**Issue**: Some advanced features may be limited by Flatpak's security model.

**Specific Areas**:
- Access to certain system hardware may be restricted
- Network printer discovery might be limited
- Serial/USB device access requires additional permissions

**Future Work**:
- Fine-tune permissions based on user feedback
- Implement portal-based solutions where appropriate
- Document any feature limitations clearly

### 4. Distribution and Updates

**Issue**: Currently builds local Flatpak packages, not distributed through a repository.

**Impact**: Users must build locally, no automatic updates.

**Future Work**:
- Publish to Flathub or other Flatpak repositories
- Implement automatic update mechanisms
- Provide signed packages for security

## Performance Considerations

### Startup Time

**Current**: PyInstaller applications can have slower startup times due to unpacking.

**Mitigation**: Most impact is only on first startup; subsequent launches benefit from filesystem caching.

### Resource Usage

**Current**: Flatpak adds some memory overhead for sandboxing.

**Mitigation**: Modern systems typically have sufficient resources; benefits of isolation outweigh costs.

## Testing Coverage

### Tested Platforms
- ✅ Ubuntu 22.04 (development environment)

### Needs Testing
- Other Ubuntu versions (20.04, 24.04)
- Fedora (38, 39, 40)
- Arch Linux
- openSUSE
- Other distributions with Flatpak support

### Test Areas
- Basic application functionality
- File format support and import/export
- Printer connectivity and management
- Plugin system functionality
- System integration (file associations, etc.)

## Future Improvements

### Short Term (Next Release)

1. **CI Integration**: Add Flatpak build to GitHub Actions workflow
2. **Error Handling**: Improve error messages in build script
3. **Documentation**: Add troubleshooting guides for common issues
4. **Testing**: Expand testing coverage to more distributions

### Medium Term (Next 2-3 Releases)

1. **Repository Publishing**: Submit to Flathub for distribution
2. **Size Optimization**: Reduce package size through better bundling
3. **Feature Parity**: Ensure all Cura features work within Flatpak sandbox
4. **Performance**: Optimize startup time and resource usage

### Long Term

1. **Modular Architecture**: Split into base app + extensions for optional features
2. **Shared Dependencies**: Use Flatpak extension system for common libraries
3. **Advanced Integration**: Better system integration while maintaining security
4. **Alternative Runtimes**: Evaluate different base runtimes for optimization

## Development Workflow Integration

### Current Process

The Flatpak build now follows the same process as AppImage:
1. Use Conan to install and build all dependencies
2. Use PyInstaller to create the application distribution
3. Package the PyInstaller output with Flatpak

### Integration Points

1. **Shared Dependencies**: Uses the same Conan packages as AppImage
2. **Same Build Tools**: Uses PyInstaller like other Cura packages
3. **Consistent Metadata**: Shares desktop files, icons, and AppData
4. **Version Alignment**: Uses the same versioning scheme

## Community Feedback Areas

We are particularly interested in feedback on:

1. **Build Process**: Is it easy enough to build locally?
2. **Feature Completeness**: Are there missing features compared to other packages?
3. **Performance**: How does it compare to native packages?
4. **Distribution Compatibility**: Does it work on your Linux distribution?
5. **Integration**: How well does it integrate with your desktop environment?

## Contributing

To help improve the Flatpak packaging:

1. **Test on Different Distributions**: Try building and running on various Linux distros
2. **Report Issues**: File GitHub issues for any problems encountered
3. **Optimize Build Process**: Suggest improvements to the build scripts
4. **Documentation**: Help improve documentation and troubleshooting guides

## Technical Debt

### Areas for Refactoring

1. **Build Script**: The current build.sh could be modularized for better maintainability
2. **Error Handling**: More graceful handling of build failures
3. **Configuration**: Better support for customizing build options
4. **Logging**: Improved logging and debugging capabilities

### Code Quality

1. **Testing**: Automated testing of the build process
2. **Validation**: Validation of the final Flatpak package
3. **Documentation**: Inline documentation in scripts and manifests