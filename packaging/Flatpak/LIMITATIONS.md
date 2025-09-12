# Flatpak Packaging Limitations and Future Work

## Current Status

This Flatpak packaging provides a foundation for building UltiMaker Cura as a Flatpak, but there are some important limitations to be aware of:

### Known Limitations

1. **Complex Dependency Chain**: Cura uses Conan for dependency management with a complex chain of UltiMaker-specific packages (uranium, curaengine, cura_resources, etc.). The current Flatpak manifest uses a simplified approach.

2. **Missing Conan Dependencies**: The full build would require:
   - uranium (framework)
   - curaengine (slicing engine)  
   - cura_resources (printer profiles)
   - cura_binary_data (additional data)
   - fdm_materials (material profiles)
   - pysavitar (3MF reader)
   - pynest2d (2D placement)

3. **Binary Dependencies**: Some dependencies like CuraEngine may need to be built from source or provided as pre-compiled binaries.

## Implementation Approaches

### Approach 1: Simplified Build (Current)
- Install basic Python dependencies via pip
- Copy Cura source code directly  
- May miss some functionality due to missing specialized dependencies

### Approach 2: Full Conan Integration
- Install and configure Conan within the Flatpak build
- Build all dependencies from Conan recipes
- More complex but provides full functionality

### Approach 3: Hybrid Approach
- Pre-build critical binary dependencies (CuraEngine)
- Use existing system packages where possible
- Use pip for pure Python dependencies

## Recommended Next Steps

1. **Test Basic Functionality**: Try building the current manifest to see what works
2. **Identify Critical Missing Pieces**: Determine which dependencies are absolutely required
3. **Add Binary Dependencies**: Include pre-built CuraEngine or build from source
4. **Iterative Improvement**: Gradually add missing dependencies based on runtime errors

## Building a Full Version

For a production-ready Flatpak, consider:

1. **Use the AppImage as Reference**: The AppImage build process shows what dependencies are actually needed at runtime
2. **Binary Compatibility**: Ensure all binary dependencies are compatible with the target runtime
3. **Testing**: Test on multiple distributions and desktop environments  
4. **Performance**: Optimize the build process and final package size

## Contributing

If you work on improving this Flatpak:
- Document any new dependencies you add
- Test the build process thoroughly
- Consider both functionality and package size
- Update the main README.md with any changes