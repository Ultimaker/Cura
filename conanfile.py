import os
from pathlib import Path

from jinja2 import Template

from conan import ConanFile
from conan.tools.files import copy, rmdir, save, mkdir
from conan.tools.microsoft import unix_path
from conan.tools.env import VirtualRunEnv, Environment
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration, ConanException

required_conan_version = ">=1.52.0"


class CuraConan(ConanFile):
    name = "cura"
    license = "LGPL-3.0"
    author = "UltiMaker"
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt5", "qt", "qml", "3d-printing", "slicer")
    build_policy = "missing"
    exports = "LICENSE*", "UltiMaker-Cura.spec.jinja", "CuraVersion.py.jinja"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True  # We won't build so no need to copy sources to the build folder

    # FIXME: Remove specific branch once merged to main
    # Extending the conanfile with the UMBaseConanfile https://github.com/Ultimaker/conan-ultimaker-index/tree/CURA-9177_Fix_CI_CD/recipes/umbase
    python_requires = "umbase/[>=0.1.7]@ultimaker/stable", "translationextractor/[>=1.0.0]@ultimaker/stable"
    python_requires_extend = "umbase.UMBaseConanfile"

    options = {
        "enterprise": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "staging": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "devtools": [True, False],  # FIXME: Split this up in testing and (development / build (pyinstaller) / system installer) tools
        "cloud_api_version": "ANY",
        "display_name": "ANY",  # TODO: should this be an option??
        "cura_debug_mode": [True, False],  # FIXME: Use profiles
        "internal": [True, False]
    }
    default_options = {
        "enterprise": "False",
        "staging": "False",
        "devtools": False,
        "cloud_api_version": "1",
        "display_name": "UltiMaker Cura",
        "cura_debug_mode": False,  # Not yet implemented
        "internal": False,
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    @property
    def _pycharm_targets(self):
        return self.conan_data["pycharm_targets"]

    # FIXME: These env vars should be defined in the runenv.
    _cura_env = None

    @property
    def _cura_run_env(self):
        if self._cura_env:
            return self._cura_env

        self._cura_env = Environment()
        self._cura_env.define("QML2_IMPORT_PATH", str(self._site_packages.joinpath("PyQt6", "Qt6", "qml")))
        self._cura_env.define("QT_PLUGIN_PATH", str(self._site_packages.joinpath("PyQt6", "Qt6", "plugins")))

        if self.settings.os == "Linux":
            self._cura_env.define("QT_QPA_FONTDIR", "/usr/share/fonts")
            self._cura_env.define("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
            self._cura_env.define("QT_XKB_CONFIG_ROOT", "/usr/share/X11/xkb")
        return self._cura_env

    @property
    def _staging(self):
        return self.options.staging in ["True", 'true']

    @property
    def _enterprise(self):
        return self.options.enterprise in ["True", 'true']

    @property
    def _app_name(self):
        if self._enterprise:
            return str(self.options.display_name) + " Enterprise"
        return str(self.options.display_name)

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
    def _cura_latest_url(self):
        return "https://software.ultimaker.com/latest.json"

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
        if self.in_local_cache:
            return Path(self.install_folder)
        else:
            return Path(self.source_folder, "venv")

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
        py_version = Version(self.deps_cpp_info["cpython"].version)
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

        # If you want a specific Cura version to show up on the splash screen add the user configuration `user.cura:version=VERSION`
        # the global.conf, profile, package_info (of dependency) or via the cmd line `-c user.cura:version=VERSION`
        cura_version = Version(self.conf.get("user.cura:version", default = self.version, check_type = str))
        pre_tag = f"-{cura_version.pre}" if cura_version.pre else ""
        build_tag = f"+{cura_version.build}" if cura_version.build else ""
        internal_tag = f"+internal" if self.options.internal else ""
        cura_version = f"{cura_version.major}.{cura_version.minor}.{cura_version.patch}{pre_tag}{build_tag}{internal_tag}"

        with open(Path(location, "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self._app_name,
                cura_version = cura_version,
                cura_build_type = "Enterprise" if self._enterprise else "",
                cura_debug_mode = self.options.cura_debug_mode,
                cura_cloud_api_root = self._cloud_api_root,
                cura_cloud_api_version = self.options.cloud_api_version,
                cura_cloud_account_api_root = self._cloud_account_api_root,
                cura_marketplace_root = self._marketplace_root,
                cura_digital_factory_url = self._digital_factory_url,
                cura_latest_url = self._cura_latest_url))

    def _generate_pyinstaller_spec(self, location, entrypoint_location, icon_path, entitlements_file):
        pyinstaller_metadata = self._um_data()["pyinstaller"]
        datas = [(str(self._base_dir.joinpath("conan_install_info.json")), ".")]
        for data in pyinstaller_metadata["datas"].values():
            if not self.options.internal and data.get("internal", False):
                continue

            if "package" in data:  # get the paths from conan package
                if data["package"] == self.name:
                    if self.in_local_cache:
                        src_path = Path(self.package_folder, data["src"])
                    else:
                        src_path = Path(self.source_folder, data["src"])
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
                self.output.warning(f"Source path for binary {binary['binary']} does not exist")
                continue

            for bin in src_path.glob(binary["binary"] + "*[.exe|.dll|.so|.dylib|.so.]*"):
                binaries.append((str(bin), binary["dst"]))
            for bin in src_path.glob(binary["binary"]):
                binaries.append((str(bin), binary["dst"]))

        # Make sure all Conan dependencies which are shared are added to the binary list for pyinstaller
        for _, dependency in self.dependencies.host.items():
            for bin_paths in dependency.cpp_info.bindirs:
                binaries.extend([(f"{p}", ".") for p in Path(bin_paths).glob("**/*.dll")])
            for lib_paths in dependency.cpp_info.libdirs:
                binaries.extend([(f"{p}", ".") for p in Path(lib_paths).glob("**/*.so*")])
                binaries.extend([(f"{p}", ".") for p in Path(lib_paths).glob("**/*.dylib*")])

        # Copy dynamic libs from lib path
        binaries.extend([(f"{p}", ".") for p in Path(self._base_dir.joinpath("lib")).glob("**/*.dylib*")])
        binaries.extend([(f"{p}", ".") for p in Path(self._base_dir.joinpath("lib")).glob("**/*.so*")])

        # Collect all dll's from PyQt6 and place them in the root
        binaries.extend([(f"{p}", ".") for p in Path(self._site_packages, "PyQt6", "Qt6").glob("**/*.dll")])

        with open(Path(__file__).parent.joinpath("UltiMaker-Cura.spec.jinja"), "r") as f:
            pyinstaller = Template(f.read())

        version = self.conf_info.get("user.cura:version", default = self.version, check_type = str)
        cura_version = Version(version)

        with open(Path(location, "UltiMaker-Cura.spec"), "w") as f:
            f.write(pyinstaller.render(
                name = str(self.options.display_name).replace(" ", "-"),
                display_name = self.options.display_name,
                entrypoint = entrypoint_location,
                datas = datas,
                binaries = binaries,
                venv_script_path = str(self._script_dir),
                hiddenimports = pyinstaller_metadata["hiddenimports"],
                collect_all = pyinstaller_metadata["collect_all"],
                icon = icon_path,
                entitlements_file = entitlements_file,
                osx_bundle_identifier = "'nl.ultimaker.cura'" if self.settings.os == "Macos" else "None",
                upx = str(self.settings.os == "Windows"),
                strip = False,  # This should be possible on Linux and MacOS but, it can also cause issues on some distributions. Safest is to disable it for now
                target_arch = "'x86_64'" if self.settings.os == "Macos" else "None",  # FIXME: Make this dependent on the settings.arch_target
                macos = self.settings.os == "Macos",
                version = f"'{version}'",
                short_version = f"'{cura_version.major}.{cura_version.minor}.{cura_version.patch}'",
            ))

    def set_version(self):
        if self.version is None:
            self.version = self._umdefault_version()

    def configure(self):
        self.options["pyarcus"].shared = True
        self.options["pysavitar"].shared = True
        self.options["pynest2d"].shared = True
        self.options["cpython"].shared = True

    def validate(self):
        version = self.conf_info.get("user.cura:version", default = self.version, check_type = str)
        if version and Version(version) <= Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        for req in self._um_data()["requirements"]:
            self.requires(req)
        if self.options.internal:
            for req in self._um_data()["internal_requirements"]:
                self.requires(req)

    def build_requirements(self):
        if self.options.devtools:
            if self.settings.os != "Windows" or self.conf.get("tools.microsoft.bash:path", check_type = str):
                # FIXME: once m4, autoconf, automake are Conan V2 ready use self.win_bash and add gettext as base tool_requirement
                self.tool_requires("gettext/0.21", force_host_context=True)

    def layout(self):
        self.folders.source = "."
        self.folders.build = "venv"
        self.folders.generators = Path(self.folders.build, "conan")

        self.cpp.package.libdirs = [os.path.join("site-packages", "cura")]
        self.cpp.package.bindirs = ["bin"]
        self.cpp.package.resdirs = ["resources", "plugins", "packaging", "pip_requirements"]  # pip_requirements should be the last item in the list

    def build(self):
        if self.options.devtools:
            if self.settings.os != "Windows" or self.conf.get("tools.microsoft.bash:path", check_type = str):
                # FIXME: once m4, autoconf, automake are Conan V2 ready use self.win_bash and add gettext as base tool_requirement
                cpp_info = self.dependencies["gettext"].cpp_info
                for po_file in self.source_path.joinpath("resources", "i18n").glob("**/*.po"):
                    mo_file = self.build_path.joinpath(po_file.with_suffix('.mo').relative_to(self.source_path))
                    mkdir(self, str(unix_path(self, mo_file.parent)))
                    self.run(f"{cpp_info.bindirs[0]}/msgfmt {po_file} -o {mo_file} -f", env="conanbuild", ignore_errors=True)

    def generate(self):
        cura_run_envvars = self._cura_run_env.vars(self, scope = "run")
        ext = ".ps1" if self.settings.os == "Windows" else ".sh"
        cura_run_envvars.save_script(self.folders.generators.joinpath(f"cura_run_environment{ext}"))

        vr = VirtualRunEnv(self)
        vr.generate()

        self._generate_cura_version(Path(self.source_folder, "cura"))

        if self.options.devtools:
            entitlements_file = "'{}'".format(Path(self.source_folder, "packaging", "MacOS", "cura.entitlements"))
            self._generate_pyinstaller_spec(location = self.generators_folder,
                                            entrypoint_location = "'{}'".format(Path(self.source_folder, self._um_data()["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                            icon_path = "'{}'".format(Path(self.source_folder, "packaging", self._um_data()["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                            entitlements_file = entitlements_file if self.settings.os == "Macos" else "None")

            # Update the po files
            if self.settings.os != "Windows" or self.conf.get("tools.microsoft.bash:path", check_type = str):
                # FIXME: once m4, autoconf, automake are Conan V2 ready use self.win_bash and add gettext as base tool_requirement
                cpp_info = self.dependencies["gettext"].cpp_info

                # Extract all the new strings and update the existing po files
                extractTool = self.python_requires["translationextractor"].module.ExtractTranslations(self)
                extractTool.extract(self.source_path, self.source_path.joinpath("resources", "i18n"), "cura.pot")

                for po_file in self.source_path.joinpath("resources", "i18n").glob("**/*.po"):
                    pot_file = self.source_path.joinpath("resources", "i18n", po_file.with_suffix('.pot').name)
                    mkdir(self, str(unix_path(self, pot_file.parent)))
                    self.run(f"{cpp_info.bindirs[0]}/msgmerge --no-wrap --no-fuzzy-matching -width=140 -o {po_file} {po_file} {pot_file}",
                             env = "conanbuild", ignore_errors = True)

    def imports(self):
        self.copy("CuraEngine.exe", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)
        self.copy("CuraEngine", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)

        rmdir(self, os.path.join(self.source_folder, "resources", "materials"))
        self.copy("*.fdm_material", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)
        self.copy("*.sig", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)

        if self.options.internal:
            self.copy("*.fdm_material", root_package = "fdm_materials_private", src = "@resdirs", dst = "resources/materials", keep_path = False)
            self.copy("*.sig", root_package = "fdm_materials_private", src = "@resdirs", dst = "resources/materials", keep_path = False)
            self.copy("*", root_package = "cura_private_data", src = self.deps_cpp_info["cura_private_data"].resdirs[0],
                           dst = self._share_dir.joinpath("cura", "resources"), keep_path = True)

        # Copy resources of cura_binary_data
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[0],
                       dst = self._share_dir.joinpath("cura", "resources"), keep_path = True)
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[1],
                       dst =self._share_dir.joinpath("uranium", "resources"), keep_path = True)

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

        # Copy internal resources
        if self.options.internal:
            self.copy_deps("*.fdm_material", root_package = "fdm_materials_private", src = self.deps_cpp_info["fdm_materials_private"].resdirs[0],
                           dst = self._share_dir.joinpath("cura", "resources", "materials"), keep_path = False)
            self.copy_deps("*.sig", root_package = "fdm_materials_private", src = self.deps_cpp_info["fdm_materials_private"].resdirs[0],
                           dst = self._share_dir.joinpath("cura", "resources", "materials"), keep_path = False)
            self.copy_deps("*", root_package = "cura_private_data", src = self.deps_cpp_info["cura_private_data"].resdirs[0],
                           dst = self._share_dir.joinpath("cura", "resources"), keep_path = True)
            self.copy_deps("*", root_package = "cura_private_data", src = self.deps_cpp_info["cura_private_data"].resdirs[1],
                           dst = self._share_dir.joinpath("cura", "plugins"), keep_path = True)

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
        version = self.conf_info.get("user.cura:version", default = self.version, check_type = str)
        cura_version = Version(version)
        env_prefix = "Env:" if self.settings.os == "Windows" else ""
        activate_github_actions_version_env = Template(r"""echo "CURA_VERSION_MAJOR={{ cura_version_major }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_MINOR={{ cura_version_minor }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_PATCH={{ cura_version_patch }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_BUILD={{ cura_version_build }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_VERSION_FULL={{ cura_version_full }}" >> ${{ env_prefix }}GITHUB_ENV
echo "CURA_APP_NAME={{ cura_app_name }}" >> ${{ env_prefix }}GITHUB_ENV
        """).render(cura_version_major = cura_version.major,
                    cura_version_minor = cura_version.minor,
                    cura_version_patch = cura_version.patch,
                    cura_version_build = cura_version.build if cura_version.build != "" else "0",
                    cura_version_full = self.version,
                    cura_app_name = self._app_name,
                    env_prefix = env_prefix)

        ext = ".sh" if self.settings.os != "Windows" else ".ps1"
        save(self, self._script_dir.joinpath(f"activate_github_actions_version_env{ext}"), activate_github_actions_version_env)

        self._generate_cura_version(Path(self._site_packages, "cura"))

        entitlements_file = "'{}'".format(Path(self.cpp_info.res_paths[2], "MacOS", "cura.entitlements"))
        self._generate_pyinstaller_spec(location = self._base_dir,
                                        entrypoint_location = "'{}'".format(Path(self.cpp_info.bin_paths[0], self._um_data()["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                        icon_path = "'{}'".format(Path(self.cpp_info.res_paths[2], self._um_data()["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                        entitlements_file = entitlements_file if self.settings.os == "Macos" else "None")

    def package(self):
        copy(self, "cura_app.py", src = self.source_path, dst = self.package_path.joinpath(self.cpp.package.bindirs[0]))
        copy(self, "*", src = self.source_path.joinpath("cura"), dst = self.package_path.joinpath(self.cpp.package.libdirs[0]))
        copy(self, "*", src = self.source_path.joinpath("resources"), dst = self.package_path.joinpath(self.cpp.package.resdirs[0]), excludes="*.po")
        copy(self, "*", src = self.build_path.joinpath("resources"), dst = self.package_path.joinpath(self.cpp.package.resdirs[0]))
        copy(self, "*", src = self.source_path.joinpath("plugins"), dst = self.package_path.joinpath(self.cpp.package.resdirs[1]))
        copy(self, "requirement*.txt", src = self.source_path, dst = self.package_path.joinpath(self.cpp.package.resdirs[-1]))
        copy(self, "*", src = self.source_path.joinpath("packaging"), dst = self.package_path.joinpath(self.cpp.package.resdirs[2]))

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
