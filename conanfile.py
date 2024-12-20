import os
from io import StringIO
from pathlib import Path

from jinja2 import Template

from conan import ConanFile
from conan.tools.files import copy, rmdir, save, mkdir, rm, update_conandata
from conan.tools.microsoft import unix_path
from conan.tools.env import VirtualRunEnv, Environment, VirtualBuildEnv
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration, ConanException

required_conan_version = ">=2.7.0"


class CuraConan(ConanFile):
    name = "cura"
    license = "LGPL-3.0"
    author = "UltiMaker"
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt6", "qt", "qml", "3d-printing", "slicer")
    build_policy = "missing"
    exports = "LICENSE*", "*.jinja"
    settings = "os", "compiler", "build_type", "arch"
    generators = "VirtualPythonEnv"
    tool_requires = "gettext/0.22.5"

    # FIXME: Remove specific branch once merged to main
    python_requires = "translationextractor/[>=2.2.0]@ultimaker/stable"

    options = {
        "enterprise": [True, False],
        "staging": [True, False],
        "cloud_api_version": ["ANY"],
        "display_name": ["ANY"],  # TODO: should this be an option??
        "cura_debug_mode": [True, False],  # FIXME: Use profiles
        "internal": [True, False],
        "i18n_extract": [True, False],
    }
    default_options = {
        "enterprise": False,
        "staging": False,
        "cloud_api_version": "1",
        "display_name": "UltiMaker Cura",
        "cura_debug_mode": False,  # Not yet implemented
        "internal": False,
        "i18n_extract": False,
    }

    def set_version(self):
        if not self.version:
            self.version = self.conan_data["version"]

    @property
    def _app_name(self):
        if self.options.enterprise:
            return str(self.options.display_name) + " Enterprise"
        return str(self.options.display_name)

    @property
    def _urls(self):
        if self.options.staging:
            return "staging"
        return "default"

    @property
    def _root_dir(self):
        return Path(self.deploy_folder if hasattr(self, "deploy_folder") else self.source_folder)

    @property
    def _base_dir(self):
        return self._root_dir.joinpath("venv")

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
        py_version = Version(self.dependencies["cpython"].ref.version)
        return self._base_dir.joinpath("lib", f"python{py_version.major}.{py_version.minor}", "site-packages")

    @property
    def _py_interp(self):
        py_interp = self._script_dir.joinpath(Path(self.deps_user_info["cpython"].python).name)
        if self.settings.os == "Windows":
            py_interp = Path(*[f'"{p}"' if " " in p else p for p in py_interp.parts])
        return py_interp

    @property
    def _pyinstaller_spec_arch(self):
        if self.settings.os == "Macos":
            if self.settings.arch == "armv8":
                return "'arm64'"
            return "'x86_64'"
        return "None"

    def _conan_installs(self):
        self.output.info("Collecting conan installs")
        conan_installs = {}

        # list of conan installs
        for dependency in self.dependencies.host.values():
            conan_installs[dependency.ref.name] = {
                "version": str(dependency.ref.version),
                "revision": dependency.ref.revision
            }
        return conan_installs

    def _python_installs(self):
        self.output.info("Collecting python installs")
        python_installs = {}

        collect_python_installs = "collect_python_installs.py"
        code = f"import importlib.metadata;  print(';'.join([(package.metadata['Name']+','+    package.metadata['Version']) for package in importlib.metadata.distributions()]))"
        save(self, collect_python_installs, code)

        buffer = StringIO()
        self.run(f"""python {collect_python_installs}""", env = "virtual_python_env", stdout = buffer)
        rm(self, collect_python_installs, ".")

        packages = str(buffer.getvalue()).strip('\r\n').split(";")
        for package in packages:
            name, version = package.split(",")
            python_installs[name] = {"version": version}

        return python_installs

    def _generate_cura_version(self, location):
        with open(os.path.join(self.recipe_folder, "CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        # If you want a specific Cura version to show up on the splash screen add the user configuration `user.cura:version=VERSION`
        # the global.conf, profile, package_info (of dependency) or via the cmd line `-c user.cura:version=VERSION`
        cura_version = Version(self.conf.get("user.cura:version", default = self.version, check_type = str))
        pre_tag = f"-{cura_version.pre}" if cura_version.pre else ""
        build_tag = f"+{cura_version.build}" if cura_version.build else ""
        internal_tag = f"+internal" if self.options.internal else ""
        cura_version = f"{cura_version.major}.{cura_version.minor}.{cura_version.patch}{pre_tag}{build_tag}{internal_tag}"

        self.output.info(f"Write CuraVersion.py to {self.recipe_folder}")

        with open(os.path.join(location, "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self._app_name,
                cura_version = cura_version,
                cura_version_full = self.version,
                cura_build_type = "Enterprise" if self.options.enterprise else "",
                cura_debug_mode = self.options.cura_debug_mode,
                cura_cloud_api_root = self.conan_data["urls"][self._urls]["cloud_api_root"],
                cura_cloud_api_version = self.options.cloud_api_version,
                cura_cloud_account_api_root = self.conan_data["urls"][self._urls]["cloud_account_api_root"],
                cura_marketplace_root = self.conan_data["urls"][self._urls]["marketplace_root"],
                cura_digital_factory_url = self.conan_data["urls"][self._urls]["digital_factory_url"],
                cura_latest_url=self.conan_data["urls"][self._urls]["cura_latest_url"],
                conan_installs=self._conan_installs(),
                python_installs=self._python_installs(),
            ))

    def _delete_unwanted_binaries(self, root):
        dynamic_binary_file_exts = [".so", ".dylib", ".dll", ".pyd", ".pyi"]
        prohibited = [
            "qt5compat",
            "qtcharts",
            "qtcoap",
            "qtdatavis3d",
            "qtlottie",
            "qtmqtt",
            "qtnetworkauth",
            "qtquick3d",
            "quick3d",
            "qtquick3dphysics",
            "qtquicktimeline",
            "qtvirtualkeyboard",
            "qtwayland"
        ]
        forbiddens = [x.encode() for x in prohibited]
        to_remove_files = []
        to_remove_dirs = []
        for root, dir_, files in os.walk(root):
            for filename in files:
                if not any([(x in filename) for x in dynamic_binary_file_exts]):
                    continue
                pathname = os.path.join(root, filename)
                still_exist = True
                for forbidden in prohibited:
                    if forbidden.lower() in str(pathname).lower():
                        to_remove_files.append(pathname)
                        still_exist = False
                        break
                if not still_exist:
                    continue
                with open(pathname, "rb") as file:
                    bytez = file.read().lower()
                    for forbidden in forbiddens:
                        if bytez.find(forbidden) >= 0:
                            to_remove_files.append(pathname)
            for dirname in dir_:
                for forbidden in prohibited:
                    if forbidden.lower() in str(dirname).lower():
                        pathname = os.path.join(root, dirname)
                        to_remove_dirs.append(pathname)
                        break
        for file in to_remove_files:
            try:
                os.remove(file)
                print(f"deleted file: {file}")
            except Exception as ex:
                print(f"WARNING: Attempt to delete file {file} results in: {str(ex)}")
        for dir_ in to_remove_dirs:
            try:
                rmdir(self, dir_)
                print(f"deleted dir_: {dir_}")
            except Exception as ex:
                print(f"WARNING: Attempt to delete folder {dir_} results in: {str(ex)}")

    def _generate_pyinstaller_spec(self, location, entrypoint_location, icon_path, entitlements_file, cura_source_folder):
        pyinstaller_metadata = self.conan_data["pyinstaller"]
        datas = []
        for data in pyinstaller_metadata["datas"].values():
            if (not self.options.internal and data.get("internal", False)) or (not self.options.enterprise and data.get("enterprise_only", False)):
                continue

            if "oses" in data and self.settings.os not in data["oses"]:
                continue

            if "package" in data:  # get the paths from conan package
                if data["package"] == self.name:
                    src_path = str(Path(cura_source_folder, data["src"]))
                else:
                    if data["package"] not in self.dependencies:
                        raise ConanException(f"Required package {data['package']} does not exist as a dependency")

                    package_folder = self.dependencies[data['package']].package_folder
                    if package_folder is None:
                        raise ConanException(f"Unable to find package_folder for {data['package']}, check that it has not been skipped")

                    src_path = os.path.join(self.dependencies[data["package"]].package_folder, data["src"])
            elif "root" in data:  # get the paths relative from the install folder
                src_path = os.path.join(self.install_folder, data["root"], data["src"])
            else:
                raise ConanException("Misformatted conan data for pyinstaller datas, expected either package or root option")

            if not Path(src_path).exists():
                raise ConanException(f"Missing folder {src_path} for pyinstaller data {data}")

            datas.append((str(src_path), data["dst"]))

        binaries = []
        for binary in pyinstaller_metadata["binaries"].values():
            if "package" in binary:  # get the paths from conan package
                src_path = os.path.join(self.dependencies[binary["package"]].package_folder, binary["src"])
            elif "root" in binary:  # get the paths relative from the sourcefolder
                src_path = str(Path(self.source_folder, binary["root"], binary["src"]))
                if self.settings.os == "Windows":
                    src_path = src_path.replace("\\", "\\\\")
            else:
                raise ConanException("Misformatted conan data for pyinstaller binaries, expected either package or root option")

            if not Path(src_path).exists():
                raise ConanException(f"Missing folder {src_path} for pyinstaller binary {binary}")

            for bin in Path(src_path).glob(binary["binary"] + "*[.exe|.dll|.so|.dylib|.so.]*"):
                binaries.append((str(bin), binary["dst"]))
            for bin in Path(src_path).glob(binary["binary"]):
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

        with open(os.path.join(self.recipe_folder, "UltiMaker-Cura.spec.jinja"), "r") as f:
            pyinstaller = Template(f.read())

        version = self.conf.get("user.cura:version", default = self.version, check_type = str)
        cura_version = Version(version)

        # filter all binary files in binaries on the blacklist
        blacklist = pyinstaller_metadata["blacklist"]
        filtered_binaries = [b for b in binaries if not any([all([(part in b[0].lower()) for part in parts]) for parts in blacklist])]

        # In case the installer isn't actually pyinstaller (Windows at the moment), outright remove the offending files:
        specifically_delete = set(binaries) - set(filtered_binaries)
        for (unwanted_path, _) in specifically_delete:
            try:
                os.remove(unwanted_path)
                print(f"delete: {unwanted_path}")
            except Exception as ex:
                print(f"WARNING: Attempt to delete binary {unwanted_path} results in: {str(ex)}")

        hiddenimports = pyinstaller_metadata["hiddenimports"]
        collect_all = pyinstaller_metadata["collect_all"]
        if self.settings.os == "Windows":
            hiddenimports += pyinstaller_metadata["hiddenimports_WINDOWS_ONLY"]
            collect_all += pyinstaller_metadata["collect_all_WINDOWS_ONLY"]

        # Write the actual file:
        with open(os.path.join(location, "UltiMaker-Cura.spec"), "w") as f:
            f.write(pyinstaller.render(
                name = str(self.options.display_name).replace(" ", "-"),
                display_name = self._app_name,
                entrypoint = entrypoint_location,
                datas = datas,
                binaries = filtered_binaries,
                venv_script_path = str(self._script_dir),
                hiddenimports = hiddenimports,
                collect_all = collect_all,
                icon = icon_path,
                entitlements_file = entitlements_file,
                osx_bundle_identifier = "'nl.ultimaker.cura'" if self.settings.os == "Macos" else "None",
                upx = str(self.settings.os == "Windows"),
                strip = False,  # This should be possible on Linux and MacOS but, it can also cause issues on some distributions. Safest is to disable it for now
                target_arch = self._pyinstaller_spec_arch,
                macos = self.settings.os == "Macos",
                version = f"'{version}'",
                short_version = f"'{cura_version.major}.{cura_version.minor}.{cura_version.patch}'",
            ))

    def export(self):
        update_conandata(self, {"version": self.version})

    def export_sources(self):
        copy(self, "*", os.path.join(self.recipe_folder, "plugins"), os.path.join(self.export_sources_folder, "plugins"))
        copy(self, "*", os.path.join(self.recipe_folder, "resources"), os.path.join(self.export_sources_folder, "resources"), excludes = "*.mo")
        copy(self, "*", os.path.join(self.recipe_folder, "tests"), os.path.join(self.export_sources_folder, "tests"))
        copy(self, "*", os.path.join(self.recipe_folder, "cura"), os.path.join(self.export_sources_folder, "cura"), excludes="CuraVersion.py")
        copy(self, "*", os.path.join(self.recipe_folder, "packaging"), os.path.join(self.export_sources_folder, "packaging"))
        copy(self, "*", os.path.join(self.recipe_folder, ".run_templates"), os.path.join(self.export_sources_folder, ".run_templates"))
        copy(self, "cura_app.py", self.recipe_folder, self.export_sources_folder)

    def validate(self):
        if self.options.i18n_extract and self.settings.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            raise ConanInvalidConfiguration("Unable to extract translations on Windows without Bash installed")

    def requirements(self):
        for req in self.conan_data["requirements"]:
            if self.options.internal and "fdm_materials" in req:
                continue
            self.requires(req)
        if self.options.internal:
            for req in self.conan_data["requirements_internal"]:
                self.requires(req)
        if self.options.enterprise:
            for req in self.conan_data["requirements_enterprise"]:
                self.requires(req)
        self.requires("cpython/3.12.2")

    def layout(self):
        self.folders.source = "."
        self.folders.build = "build"
        self.folders.generators = os.path.join(self.folders.build, "generators")

        self.cpp.package.libdirs = [os.path.join("site-packages", "cura")]
        self.cpp.package.bindirs = ["bin"]
        self.cpp.package.resdirs = ["resources", "plugins", "packaging"]

    def generate(self):
        copy(self, "cura_app.py", self.source_folder, str(self._script_dir))

        self._generate_cura_version(str(Path(self.source_folder, "cura")))

        # Copy CuraEngine.exe to bindirs of Virtual Python Environment
        curaengine = self.dependencies["curaengine"].cpp_info
        copy(self, "CuraEngine.exe", curaengine.bindirs[0], self.source_folder, keep_path = False)
        copy(self, "CuraEngine", curaengine.bindirs[0], self.source_folder, keep_path = False)

        # Copy the external plugins that we want to bundle with Cura
        if self.options.enterprise:
            rmdir(self, str(Path(self.source_folder, "plugins", "NativeCADplugin")))
            native_cad_plugin = self.dependencies["native_cad_plugin"].cpp_info
            copy(self, "*", native_cad_plugin.resdirs[0], str(Path(self.source_folder, "plugins", "NativeCADplugin")), keep_path = True)
            copy(self, "bundled_*.json", native_cad_plugin.resdirs[1], str(Path(self.source_folder, "resources", "bundled_packages")), keep_path = False)

        # Copy resources of cura_binary_data
        cura_binary_data = self.dependencies["cura_binary_data"].cpp_info
        copy(self, "*", cura_binary_data.resdirs[0], str(self._share_dir.joinpath("cura")), keep_path = True)
        copy(self, "*", cura_binary_data.resdirs[1], str(self._share_dir.joinpath("uranium")), keep_path = True)
        if self.settings.os == "Windows":
            copy(self, "*", cura_binary_data.resdirs[2], str(self._share_dir.joinpath("windows")), keep_path = True)

        for dependency in self.dependencies.host.values():
            for bindir in dependency.cpp_info.bindirs:
                self._delete_unwanted_binaries(bindir)
                copy(self, "*.dll", bindir, str(self._site_packages), keep_path = False)
            for libdir in dependency.cpp_info.libdirs:
                self._delete_unwanted_binaries(libdir)
                copy(self, "*.pyd", libdir, str(self._site_packages), keep_path = False)
                copy(self, "*.pyi", libdir, str(self._site_packages), keep_path = False)
                copy(self, "*.dylib", libdir, str(self._base_dir.joinpath("lib")), keep_path = False)

        # Copy materials (flat)
        rmdir(self, str(Path(self.source_folder, "resources", "materials")))
        fdm_materials = self.dependencies["fdm_materials"].cpp_info
        copy(self, "*", fdm_materials.resdirs[0], self.source_folder)

        # Copy internal resources
        if self.options.internal:
            cura_private_data = self.dependencies["cura_private_data"].cpp_info
            copy(self, "*", cura_private_data.resdirs[0], str(self._share_dir.joinpath("cura")))

        if self.options.i18n_extract:
            vb = VirtualBuildEnv(self)
            vb.generate()

            pot = self.python_requires["translationextractor"].module.ExtractTranslations(self)
            pot.generate()

    def build(self):
        if self.settings.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            self.output.warning("Skipping generation of binary translation files because Bash could not be found and is required")
            return

        for po_file in Path(self.source_folder, "resources", "i18n").glob("**/*.po"):
            mo_file = Path(self.build_folder, po_file.with_suffix('.mo').relative_to(self.source_folder))
            mo_file = mo_file.parent.joinpath("LC_MESSAGES", mo_file.name)
            mkdir(self, str(unix_path(self, Path(mo_file).parent)))
            self.run(f"msgfmt {po_file} -o {mo_file} -f", env="conanbuild")

    def deploy(self):
        ''' Note: this deploy step is actually used to prepare for building a Cura distribution with pyinstaller, which is not
            the original purpose in the Conan philosophy '''

        copy(self, "*", os.path.join(self.package_folder, self.cpp.package.resdirs[2]), os.path.join(self.deploy_folder, "packaging"), keep_path = True)

        # Copy resources of Cura (keep folder structure) needed by pyinstaller to determine the module structure
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.bindirs[0]), str(self._base_dir), keep_path = False)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.libdirs[0]), str(self._site_packages.joinpath("cura")), keep_path = True)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.resdirs[0]), str(self._share_dir.joinpath("cura", "resources")), keep_path = True)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.resdirs[1]), str(self._share_dir.joinpath("cura", "plugins")), keep_path = True)

        # Copy the cura_resources resources from the package
        rm(self, "conanfile.py", os.path.join(self.package_folder, self.cpp.package.resdirs[0]))
        cura_resources = self.dependencies["cura_resources"].cpp_info
        for res_dir in cura_resources.resdirs:
            copy(self, "*", res_dir, str(self._share_dir.joinpath("cura", "resources", Path(res_dir).name)), keep_path = True)

        # Copy resources of Uranium (keep folder structure)
        uranium = self.dependencies["uranium"].cpp_info
        copy(self, "*", uranium.resdirs[0], str(self._share_dir.joinpath("uranium", "resources")), keep_path = True)
        copy(self, "*", uranium.resdirs[1], str(self._share_dir.joinpath("uranium", "plugins")), keep_path = True)
        copy(self, "*", uranium.libdirs[0], str(self._site_packages.joinpath("UM")), keep_path = True)

        self._generate_cura_version(os.path.join(self._site_packages, "cura"))

        self._delete_unwanted_binaries(self._site_packages)
        self._delete_unwanted_binaries(self.package_folder)
        self._delete_unwanted_binaries(self._base_dir)
        self._delete_unwanted_binaries(self._share_dir)

        entitlements_file = "'{}'".format(Path(self.deploy_folder, "packaging", "MacOS", "cura.entitlements"))
        self._generate_pyinstaller_spec(location = self.deploy_folder,
                                        entrypoint_location = "'{}'".format(os.path.join(self.package_folder, self.cpp_info.bindirs[0], self.conan_data["pyinstaller"]["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                        icon_path = "'{}'".format(os.path.join(self.package_folder, self.cpp_info.resdirs[2], self.conan_data["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                        entitlements_file = entitlements_file if self.settings.os == "Macos" else "None",
                                        cura_source_folder = self.package_folder)

    def package(self):
        copy(self, "cura_app.py", src = self.source_folder, dst = os.path.join(self.package_folder, self.cpp.package.bindirs[0]))
        copy(self, "*", src = os.path.join(self.source_folder, "cura"), dst = os.path.join(self.package_folder, self.cpp.package.libdirs[0]))
        copy(self, "*", src = os.path.join(self.source_folder, "resources"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[0]))
        copy(self, "*.mo", os.path.join(self.build_folder, "resources"), os.path.join(self.package_folder, "resources"))
        copy(self, "*", src = os.path.join(self.source_folder, "plugins"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[1]))
        copy(self, "*", src = os.path.join(self.source_folder, "packaging"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[2]))
        copy(self, "pip_requirements_*.txt", src = self.generators_folder, dst = os.path.join(self.package_folder, self.cpp.package.resdirs[-1]))

        # Remove the fdm_materials from the package
        rmdir(self, os.path.join(self.package_folder, self.cpp.package.resdirs[0], "materials"))

        # Remove the cura_resources resources from the package
        rm(self, "conanfile.py", os.path.join(self.package_folder, self.cpp.package.resdirs[0]))
        cura_resources = self.dependencies["cura_resources"].cpp_info
        for res_dir in cura_resources.resdirs:
            rmdir(self, os.path.join(self.package_folder, self.cpp.package.resdirs[0], Path(res_dir).name))

    def package_info(self):
        self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
        self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "plugins"))

    def package_id(self):
        self.info.options.rm_safe("enable_i18n")
