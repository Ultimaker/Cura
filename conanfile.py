import os
import sys
from pathlib import Path

from io import StringIO

from platform import python_version

from jinja2 import Template

from conans import tools
from conan import ConanFile
from conan.tools import files
from conan.tools.env import VirtualRunEnv
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=1.47.0"


class CuraConan(ConanFile):
    name = "cura"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt5", "qt", "qml", "3d-printing", "slicer")
    build_policy = "missing"
    exports = "LICENSE*", "Ultimaker-Cura.spec.jinja", "CuraVersion.py.jinja"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True  # We won't build so no need to copy sources to the build folder

    # FIXME: Remove specific branch once merged to main
    # Extending the conanfile with the UMBaseConanfile https://github.com/Ultimaker/conan-ultimaker-index/tree/CURA-9177_Fix_CI_CD/recipes/umbase
    python_requires = "umbase/0.1.2@ultimaker/testing"
    python_requires_extend = "umbase.UMBaseConanfile"

    options = {
        "enterprise": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "staging": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "devtools": [True, False],  # FIXME: Split this up in testing and (development / build (pyinstaller) / system installer) tools
        "cloud_api_version": "ANY",
        "display_name": "ANY",  # TODO: should this be an option??
        "cura_debug_mode": [True, False]  # FIXME: Use profiles
    }
    default_options = {
        "enterprise": "False",
        "staging": "False",
        "devtools": False,
        "cloud_api_version": "1",
        "display_name": "Ultimaker Cura",
        "cura_debug_mode": False  # Not yet implemented
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    @property
    def _staging(self):
        return self.options.staging in ["True", 'true']

    @property
    def _enterprise(self):
        return self.options.enterprise in ["True", 'true']

    @property
    def _cloud_api_root(self):
        return "https://api-staging.ultimaker.com" if self._staging else "https://api.ultimaker.com"

    @property
    def _cloud_account_api_root(self):
        return "https://account-staging.ultimaker.com" if self._staging else "https://account.ultimaker.com"

    @property
    def _marketplace_root(self):
        return "https://marketplace-staging.ultimaker.com" if self._staging else "https://marketplace.ultimaker.com"

    @property
    def _digital_factory_url(self):
        return "https://digitalfactory-staging.ultimaker.com" if self._staging else "https://digitalfactory.ultimaker.com"

    @property
    def requirements_txts(self):
        if self.options.devtools:
            return ["requirements.txt", "requirements-ultimaker.txt", "requirements-dev.txt"]
        return ["requirements.txt", "requirements-ultimaker.txt"]

    @property
    def _base_dir(self):
        if self.install_folder is None:
            if self.build_folder is not None:
                return Path(self.build_folder)
            return Path(os.getcwd(), "venv")

        return Path(self.install_folder)  # TODO: add base dir for running from source

    @property
    def _share_dir(self):
        return self._base_dir.joinpath("share")

    @property
    def _script_dir(self):
        if self.settings.os == "Windows":
            return self._base_dir.joinpath("Scripts")
        return self._base_dir.joinpath("bin")

    @property
    def _site_packages(self):
        if self.settings.os == "Windows":
            return self._base_dir.joinpath("Lib", "site-packages")
        py_version = tools.Version(self.deps_cpp_info["cpython"].version)
        return self._base_dir.joinpath("lib", f"python{py_version.major}.{py_version.minor}", "site-packages")

    @property
    def _py_interp(self):
        py_interp = self._script_dir.joinpath(Path(self.deps_user_info["cpython"].python).name)
        if self.settings.os == "Windows":
            py_interp = Path(*[f'"{p}"' if " " in p else p for p in py_interp.parts])
        return py_interp

    def _generate_cura_version(self, location):
        with open(Path(__file__).parent.joinpath("CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        with open(Path(location, "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self.options.display_name,
                cura_version = self.version,
                cura_build_type = "Enterprise" if self._enterprise else "",
                cura_debug_mode = self.options.cura_debug_mode,
                cura_cloud_api_root = self._cloud_api_root,
                cura_cloud_api_version = self.options.cloud_api_version,
                cura_cloud_account_api_root = self._cloud_account_api_root,
                cura_marketplace_root = self._marketplace_root,
                cura_digital_factory_url = self._digital_factory_url))

    def _generate_pyinstaller_spec(self, location, entrypoint_location, icon_path, entitlements_file):
        pyinstaller_metadata = self._um_data(self.version)["pyinstaller"]
        datas = [(self._base_dir.joinpath("conan_install_info.json", "."))]
        for data in pyinstaller_metadata["datas"].values():
            if "package" in data:  # get the paths from conan package
                if data["package"] == self.name:
                    src_path = Path(self.package_folder, data["src"])
                else:
                    src_path = Path(self.deps_cpp_info[data["package"]].rootpath, data["src"])
            elif "root" in data:  # get the paths relative from the sourcefolder
                src_path = Path(self.source_folder, data["root"], data["src"])
            else:
                continue
            if src_path.exists():
                datas.append((str(src_path), data["dst"]))

        binaries = []
        for binary in pyinstaller_metadata["binaries"].values():
            if "package" in binary:  # get the paths from conan package
                src_path = Path(self.deps_cpp_info[binary["package"]].rootpath, binary["src"])
            elif "root" in binary:  # get the paths relative from the sourcefolder
                src_path = Path(self.source_folder, binary["root"], binary["src"])
            else:
                continue
            if not src_path.exists():
                continue
            for bin in src_path.glob(binary["binary"] + ".*[exe|dll|so|dylib]"):
                binaries.append((str(bin), binary["dst"]))
            for bin in src_path.glob(binary["binary"]):
                binaries.append((str(bin), binary["dst"]))

        for _, dependency in self.dependencies.items():
            # if dependency.ref.name == "cpython":
            #     continue
            for bin_paths in dependency.cpp_info.bindirs:
                binaries.extend([(f"{p}", ".") for p in Path(bin_paths).glob("**/*.dll")])
                binaries.extend([(f"{p}", ".") for p in Path(bin_paths).glob("**/*.dylib")])
                binaries.extend([(f"{p}", ".") for p in Path(bin_paths).glob("**/*.so")])

        # Copy dynamic libs from lib path
        binaries.extend([(f"{p}", ".") for p in Path(self._base_dir.joinpath("lib")).glob("**/*.dylib")])

        # Collect all dll's from PyQt6 and place them in the root
        binaries.extend([(f"{p}", ".") for p in Path(self._site_packages, "PyQt6", "Qt6").glob("**/*.dll")])

        with open(Path(__file__).parent.joinpath("Ultimaker-Cura.spec.jinja"), "r") as f:
            pyinstaller = Template(f.read())

        with open(Path(location, "Ultimaker-Cura.spec"), "w") as f:
            f.write(pyinstaller.render(
                name = str(self.options.display_name).replace(" ", "-"),
                entrypoint = entrypoint_location,
                datas = datas,
                binaries = binaries,
                hiddenimports = pyinstaller_metadata["hiddenimports"],
                collect_all = pyinstaller_metadata["collect_all"],
                icon = icon_path,
                entitlements_file = entitlements_file,
                osx_bundle_identifier = "'nl.ultimaker.cura'" if self.settings.os == "Macos" else "None",
                upx = str(self.settings.os == "Windows"),
                strip = False,  # This should be possible on Linux and MacOS but, it can also cause issues on some distributions. Safest is to disable it for now
                target_arch = "'x86_64'" if self.settings.os == "Macos" else "None",  # FIXME: Make this dependent on the settings.arch_target
                macos = self.settings.os == "Macos"
            ))

    def source(self):
        self._generate_cura_version(Path(self.source_folder, "cura"))

    def configure(self):
        self.options["arcus"].shared = True
        self.options["savitar"].shared = True
        self.options["pynest2d"].shared = True
        self.options["cpython"].shared = True

    def validate(self):
        if self.version and tools.Version(self.version) <= tools.Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        for req in self._um_data(self.version)["requirements"]:
            self.requires(req)

    def layout(self):
        self.folders.source = "."
        self.folders.build = "venv"
        self.folders.generators = Path(self.folders.build, "conan")

        self.cpp.package.libdirs = [os.path.join("site-packages", "cura")]
        self.cpp.package.bindirs = ["bin"]
        self.cpp.package.resdirs = ["resources", "plugins", "packaging", "pip_requirements"]  # pip_requirements should be the last item in the list

    def generate(self):
        vr = VirtualRunEnv(self)
        vr.generate()

        if self.options.devtools:
            entitlements_file = "'{}'".format(Path(self.source_folder, "packaging", "dmg", "cura.entitlements"))
            self._generate_pyinstaller_spec(location = self.generators_folder,
                                            entrypoint_location = "'{}'".format(Path(self.source_folder, self._um_data(self.version)["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                            icon_path = "'{}'".format(Path(self.source_folder, "packaging", self._um_data(self.version)["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                            entitlements_file = entitlements_file if self.settings.os == "Macos" else "None")

    def imports(self):
        self.copy("CuraEngine.exe", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)
        self.copy("CuraEngine", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)

        files.rmdir(self, "resources/materials")
        self.copy("*.fdm_material", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)
        self.copy("*.sig", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)

        # Copy resources of cura_binary_data
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[0],
                       dst = "venv/share/cura", keep_path = True)
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[1],
                       dst = "venv/share/uranium", keep_path = True)

        self.copy("*.dll", src = "@bindirs", dst = self._site_packages)
        self.copy("*.pyd", src = "@libdirs", dst = self._site_packages)
        self.copy("*.pyi", src = "@libdirs", dst = self._site_packages)
        self.copy("*.dylib", src = "@libdirs", dst = self._script_dir)

    def deploy(self):
        # Copy CuraEngine.exe to bindirs of Virtual Python Environment
        # TODO: Fix source such that it will get the curaengine relative from the executable (Python bindir in this case)
        self.copy_deps("CuraEngine.exe", root_package = "curaengine", src = self.deps_cpp_info["curaengine"].bindirs[0],
                       dst = self._base_dir,
                       keep_path = False)
        self.copy_deps("CuraEngine", root_package = "curaengine", src = self.deps_cpp_info["curaengine"].bindirs[0], dst = self._base_dir,
                       keep_path = False)

        # Copy resources of Cura (keep folder structure)
        self.copy("*", src = self.cpp_info.bindirs[0], dst = self._base_dir, keep_path = False)
        self.copy("*", src = self.cpp_info.libdirs[0], dst = self._site_packages.joinpath("cura"), keep_path = True)
        self.copy("*", src = self.cpp_info.resdirs[0], dst = self._share_dir.joinpath("cura", "resources"), keep_path = True)
        self.copy("*", src = self.cpp_info.resdirs[1], dst = self._share_dir.joinpath("cura", "plugins"), keep_path = True)

        # Copy materials (flat)
        self.copy_deps("*.fdm_material", root_package = "fdm_materials", src = self.deps_cpp_info["fdm_materials"].resdirs[0],
                       dst = self._share_dir.joinpath("cura", "resources", "materials"), keep_path = False)
        self.copy_deps("*.sig", root_package = "fdm_materials", src = self.deps_cpp_info["fdm_materials"].resdirs[0],
                       dst = self._share_dir.joinpath("cura", "resources", "materials"), keep_path = False)

        # Copy resources of Uranium (keep folder structure)
        self.copy_deps("*", root_package = "uranium", src = self.deps_cpp_info["uranium"].resdirs[0],
                       dst = self._share_dir.joinpath("uranium", "resources"), keep_path = True)
        self.copy_deps("*", root_package = "uranium", src = self.deps_cpp_info["uranium"].resdirs[1],
                       dst = self._share_dir.joinpath("uranium", "plugins"), keep_path = True)
        self.copy_deps("*", root_package = "uranium", src = self.deps_cpp_info["uranium"].libdirs[0],
                       dst = self._site_packages.joinpath("UM"),
                       keep_path = True)
        self.copy_deps("*", root_package = "uranium", src = str(Path(self.deps_cpp_info["uranium"].libdirs[0], "Qt", "qml", "UM")),
                       dst = self._site_packages.joinpath("PyQt6", "Qt6", "qml", "UM"),
                       keep_path = True)

        # Copy resources of cura_binary_data
        self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[0],
                       dst = self._share_dir.joinpath("cura"), keep_path = True)
        self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[1],
                       dst = self._share_dir.joinpath("uranium"), keep_path = True)
        if self.settings.os == "Windows":
            self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[2],
                           dst = self._share_dir.joinpath("windows"), keep_path = True)

        self.copy_deps("*.dll", src = "@bindirs", dst = self._site_packages)
        self.copy_deps("*.pyd", src = "@libdirs", dst = self._site_packages)
        self.copy_deps("*.pyi", src = "@libdirs", dst = self._site_packages)
        self.copy_deps("*.dylib", src = "@libdirs", dst = self._base_dir.joinpath("lib"))

        # Copy packaging scripts
        self.copy("*", src = self.cpp_info.resdirs[2], dst = self._base_dir.joinpath("packaging"))

        # Copy requirements.txt's
        self.copy("*.txt", src = self.cpp_info.resdirs[-1], dst = self._base_dir.joinpath("pip_requirements"))

        # Generate the GitHub Action version info Environment
        cura_version = tools.Version(self.version)
        env_prefix = "Env:" if self.settings.os == "Windows" else ""
        activate_github_actions_version_env = Template(r"""echo "CURA_VERSION_MAJOR={{ cura_version_major }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_MINOR={{ cura_version_minor }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_PATCH={{ cura_version_patch }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_BUILD={{ cura_version_build }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_FULL={{ cura_version_full }}" >> ${{ env_prefix }}GITHUB_ENV
        """).render(cura_version_major = cura_version.major,
                    cura_version_minor = cura_version.minor,
                    cura_version_patch = cura_version.patch,
                    cura_version_build = cura_version.build if cura_version.build != "" else "0",
                    cura_version_full = self.version,
                    env_prefix = env_prefix)

        ext = ".sh" if self.settings.os != "Windows" else ".ps1"
        files.save(self, self._script_dir.joinpath(f"activate_github_actions_version_env{ext}"), activate_github_actions_version_env)

        self._generate_cura_version(Path(self._site_packages, "cura"))

        entitlements_file = "'{}'".format(Path(self.cpp_info.res_paths[2], "dmg", "cura.entitlements"))
        self._generate_pyinstaller_spec(location = self._base_dir,
                                        entrypoint_location = "'{}'".format(Path(self.cpp_info.bin_paths[0], self._um_data(self.version)["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                        icon_path = "'{}'".format(Path(self.cpp_info.res_paths[2], self._um_data(self.version)["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                        entitlements_file = entitlements_file if self.settings.os == "Macos" else "None")

    def package(self):
        self.copy("cura_app.py", src = ".", dst = self.cpp.package.bindirs[0])
        self.copy("*", src = "cura", dst = self.cpp.package.libdirs[0])
        self.copy("*", src = "resources", dst = self.cpp.package.resdirs[0])
        self.copy("*", src = "plugins", dst = self.cpp.package.resdirs[1])
        self.copy("requirement*.txt", src = ".", dst = self.cpp.package.resdirs[-1])
        self.copy("*", src = "packaging", dst = self.cpp.package.resdirs[2])

    def package_info(self):
        self.user_info.pip_requirements = "requirements.txt"
        self.user_info.pip_requirements_git = "requirements-ultimaker.txt"
        self.user_info.pip_requirements_build = "requirements-dev.txt"

        if self.in_local_cache:
            self.runenv_info.append_path("PYTHONPATH", str(Path(self.cpp_info.lib_paths[0]).parent))
            self.runenv_info.append_path("PYTHONPATH", self.cpp_info.res_paths[1])  # Add plugins to PYTHONPATH
        else:
            self.runenv_info.append_path("PYTHONPATH", self.source_folder)
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.source_folder, "plugins"))

    def package_id(self):
        del self.info.settings.os
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.arch

        # The following options shouldn't be used to determine the hash, since these are only used to set the CuraVersion.py
        # which will als be generated by the deploy method during the `conan install cura/5.1.0@_/_`
        del self.info.options.enterprise
        del self.info.options.staging
        del self.info.options.devtools
        del self.info.options.cloud_api_version
        del self.info.options.display_name
        del self.info.options.cura_debug_mode

        # TODO: Use the hash of requirements.txt and requirements-ultimaker.txt, Because changing these will actually result in a different
        #  Cura. This is needed because the requirements.txt aren't managed by Conan and therefor not resolved in the package_id. This isn't
        #  ideal but an acceptable solution for now.
