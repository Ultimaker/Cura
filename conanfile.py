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

required_conan_version = ">=1.58.0 <2.0.0"


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

    # FIXME: Remove specific branch once merged to main
    python_requires = "translationextractor/[>=2.2.0]@ultimaker/stable"

    options = {
        "enterprise": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "staging": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "devtools": [True, False],  # FIXME: Split this up in testing and (development / build (pyinstaller) / system installer) tools
        "cloud_api_version": "ANY",
        "display_name": "ANY",  # TODO: should this be an option??
        "cura_debug_mode": [True, False],  # FIXME: Use profiles
        "internal": ["True", "False", "true", "false"],  # Workaround for GH Action passing boolean as lowercase string
        "enable_i18n": [True, False],
    }
    default_options = {
        "enterprise": "False",
        "staging": "False",
        "devtools": False,
        "cloud_api_version": "1",
        "display_name": "UltiMaker Cura",
        "cura_debug_mode": False,  # Not yet implemented
        "internal": "False",
        "enable_i18n": False,
    }

    def set_version(self):
        if not self.version:
            self.version = self.conan_data["version"]

    @property
    def _i18n_options(self):
        return self.conf.get("user.i18n:options", default = {"extract": True, "build": True}, check_type = dict)

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
        if not self.in_local_cache:
            self._cura_env.define("CURA_DATA_ROOT", str(self._share_dir.joinpath("cura")))

        if self.settings.os == "Linux":
            self._cura_env.define("QT_QPA_FONTDIR", "/usr/share/fonts")
            self._cura_env.define("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")
            self._cura_env.define("QT_XKB_CONFIG_ROOT", "/usr/share/X11/xkb")
        return self._cura_env

    @property
    def _enterprise(self):
        return self.options.enterprise in ["True", 'true']

    @property
    def _internal(self):
        return self.options.internal in ["True", 'true']

    @property
    def _app_name(self):
        if self._enterprise:
            return str(self.options.display_name) + " Enterprise"
        return str(self.options.display_name)

    @property
    def _urls(self):
        if self.options.staging in ["True", 'true']:
            return "staging"
        return "default"

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
                "version": dependency.ref.version,
                "revision": dependency.ref.revision
            }
        return conan_installs

    def _python_installs(self):
        self.output.info("Collecting python installs")
        python_installs = {}

        # list of python installs
        run_env = VirtualRunEnv(self)
        env = run_env.environment()
        env.prepend_path("PYTHONPATH", str(self._site_packages.as_posix()))
        venv_vars = env.vars(self, scope = "run")

        outer = '"' if self.settings.os == "Windows" else "'"
        inner = "'" if self.settings.os == "Windows" else '"'
        buffer = StringIO()
        with venv_vars.apply():
            self.run(f"""python -c {outer}import pkg_resources;  print({inner};{inner}.join([(s.key+{inner},{inner}+ s.version) for s in pkg_resources.working_set])){outer}""",
                          env = "conanrun",
                          output = buffer)

        packages = str(buffer.getvalue()).split("-----------------\n")
        packages = packages[1].strip('\r\n').split(";")
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
        internal_tag = f"+internal" if self._internal else ""
        cura_version = f"{cura_version.major}.{cura_version.minor}.{cura_version.patch}{pre_tag}{build_tag}{internal_tag}"

        with open(os.path.join(location, "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self._app_name,
                cura_version = cura_version,
                cura_build_type = "Enterprise" if self._enterprise else "",
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

    def _generate_pyinstaller_spec(self, location, entrypoint_location, icon_path, entitlements_file):
        pyinstaller_metadata = self.conan_data["pyinstaller"]
        datas = []
        for data in pyinstaller_metadata["datas"].values():
            if not self._internal and data.get("internal", False):
                continue

            if "package" in data:  # get the paths from conan package
                if data["package"] == self.name:
                    if self.in_local_cache:
                        src_path = os.path.join(self.package_folder, data["src"])
                    else:
                        src_path = os.path.join(self.source_folder, data["src"])
                else:
                    if data["package"] not in self.deps_cpp_info.deps:
                        continue
                    src_path = os.path.join(self.deps_cpp_info[data["package"]].rootpath, data["src"])
            elif "root" in data:  # get the paths relative from the install folder
                src_path = os.path.join(self.install_folder, data["root"], data["src"])
            else:
                continue
            if Path(src_path).exists():
                datas.append((str(src_path), data["dst"]))

        binaries = []
        for binary in pyinstaller_metadata["binaries"].values():
            if "package" in binary:  # get the paths from conan package
                src_path = os.path.join(self.deps_cpp_info[binary["package"]].rootpath, binary["src"])
            elif "root" in binary:  # get the paths relative from the sourcefolder
                src_path = str(self.source_path.joinpath(binary["root"], binary["src"]))
                if self.settings.os == "Windows":
                    src_path = src_path.replace("\\", "\\\\")
            else:
                continue
            if not Path(src_path).exists():
                self.output.warning(f"Source path for binary {binary['binary']} does not exist")
                continue

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

        with open(os.path.join(location, "UltiMaker-Cura.spec"), "w") as f:
            f.write(pyinstaller.render(
                name = str(self.options.display_name).replace(" ", "-"),
                display_name = self._app_name,
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
        copy(self, "requirements.txt", self.recipe_folder, self.export_sources_folder)
        copy(self, "requirements-dev.txt", self.recipe_folder, self.export_sources_folder)
        copy(self, "requirements-ultimaker.txt", self.recipe_folder, self.export_sources_folder)
        copy(self, "cura_app.py", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            del self.options.enable_i18n

    def configure(self):
        self.options["pyarcus"].shared = True
        self.options["pysavitar"].shared = True
        self.options["pynest2d"].shared = True
        self.options["dulcificum"].shared = self.settings.os != "Windows"
        self.options["cpython"].shared = True
        self.options["boost"].header_only = True
        if self.settings.os == "Linux":
            self.options["curaengine_grpc_definitions"].shared = True
            self.options["openssl"].shared = True
        if self.conf.get("user.curaengine:sentry_url", "", check_type=str) != "":
            self.options["curaengine"].enable_sentry = True
            self.options["arcus"].enable_sentry = True
            self.options["clipper"].enable_sentry = True

    def validate(self):
        version = self.conf.get("user.cura:version", default = self.version, check_type = str)
        if version and Version(version) <= Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        for req in self.conan_data["requirements"]:
            if self._internal and "fdm_materials" in req:
                continue
            if not self._enterprise and "native_cad_plugin" in req:
                continue
            self.requires(req)
        if self._internal:
            for req in self.conan_data["requirements_internal"]:
                self.requires(req)
        self.requires("cpython/3.10.4@ultimaker/stable")
        self.requires("clipper/6.4.2@ultimaker/stable")
        self.requires("openssl/3.2.0")
        self.requires("protobuf/3.21.12")
        self.requires("boost/1.82.0")
        self.requires("spdlog/1.12.0")
        self.requires("fmt/10.1.1")
        self.requires("zlib/1.2.13")

    def build_requirements(self):
        if self.options.get_safe("enable_i18n", False):
            self.tool_requires("gettext/0.21", force_host_context = True)

    def layout(self):
        self.folders.source = "."
        self.folders.build = "venv"
        self.folders.generators = os.path.join(self.folders.build, "conan")

        self.cpp.package.libdirs = [os.path.join("site-packages", "cura")]
        self.cpp.package.bindirs = ["bin"]
        self.cpp.package.resdirs = ["resources", "plugins", "packaging", "pip_requirements"]  # pip_requirements should be the last item in the list

    def generate(self):
        copy(self, "cura_app.py", self.source_folder, str(self._script_dir))
        cura_run_envvars = self._cura_run_env.vars(self, scope = "run")
        ext = ".ps1" if self.settings.os == "Windows" else ".sh"
        cura_run_envvars.save_script(os.path.join(self.folders.generators, f"cura_run_environment{ext}"))

        vr = VirtualRunEnv(self)
        vr.generate()

        self._generate_cura_version(os.path.join(self.source_folder, "cura"))

        if not self.in_local_cache:
            # Copy CuraEngine.exe to bindirs of Virtual Python Environment
            curaengine = self.dependencies["curaengine"].cpp_info
            copy(self, "CuraEngine.exe", curaengine.bindirs[0], self.source_folder, keep_path = False)
            copy(self, "CuraEngine", curaengine.bindirs[0], self.source_folder, keep_path = False)

            # Copy the external plugins that we want to bundle with Cura
            rmdir(self,str(self.source_path.joinpath("plugins", "CuraEngineGradualFlow")))
            curaengine_plugin_gradual_flow = self.dependencies["curaengine_plugin_gradual_flow"].cpp_info
            copy(self, "*", curaengine_plugin_gradual_flow.resdirs[0], str(self.source_path.joinpath("plugins", "CuraEngineGradualFlow")), keep_path = True)
            copy(self, "*", curaengine_plugin_gradual_flow.bindirs[0], self.source_folder, keep_path = False)
            copy(self, "bundled_*.json", curaengine_plugin_gradual_flow.resdirs[1], str(self.source_path.joinpath("resources", "bundled_packages")), keep_path = False)

            if self._enterprise:
                rmdir(self, str(self.source_path.joinpath("plugins", "NativeCADplugin")))
                curaengine_plugin_gradual_flow = self.dependencies["native_cad_plugin"].cpp_info
                copy(self, "*", curaengine_plugin_gradual_flow.resdirs[0], str(self.source_path.joinpath("plugins", "NativeCADplugin")), keep_path = True)
                copy(self, "bundled_*.json", curaengine_plugin_gradual_flow.resdirs[1], str(self.source_path.joinpath("resources", "bundled_packages")), keep_path = False)

        # Copy resources of cura_binary_data
        cura_binary_data = self.dependencies["cura_binary_data"].cpp_info
        copy(self, "*", cura_binary_data.resdirs[0], str(self._share_dir.joinpath("cura")), keep_path = True)
        copy(self, "*", cura_binary_data.resdirs[1], str(self._share_dir.joinpath("uranium")), keep_path = True)
        if self.settings.os == "Windows":
            copy(self, "*", cura_binary_data.resdirs[2], str(self._share_dir.joinpath("windows")), keep_path = True)

        for dependency in self.dependencies.host.values():
            for bindir in dependency.cpp_info.bindirs:
                copy(self, "*.dll", bindir, str(self._site_packages), keep_path = False)
            for libdir in dependency.cpp_info.libdirs:
                copy(self, "*.pyd", libdir, str(self._site_packages), keep_path = False)
                copy(self, "*.pyi", libdir, str(self._site_packages), keep_path = False)
                copy(self, "*.dylib", libdir, str(self._base_dir.joinpath("lib")), keep_path = False)

        # Copy materials (flat)
        rmdir(self, os.path.join(self.source_folder, "resources", "materials"))
        fdm_materials = self.dependencies["fdm_materials"].cpp_info
        copy(self, "*", fdm_materials.resdirs[0], self.source_folder)

        # Copy internal resources
        if self._internal:
            cura_private_data = self.dependencies["cura_private_data"].cpp_info
            copy(self, "*", cura_private_data.resdirs[0], str(self._share_dir.joinpath("cura")))

        if self.options.devtools:
            entitlements_file = "'{}'".format(os.path.join(self.source_folder, "packaging", "MacOS", "cura.entitlements"))
            self._generate_pyinstaller_spec(
                location=self.generators_folder,
                entrypoint_location="'{}'".format(
                    os.path.join(self.source_folder, self.conan_data["pyinstaller"]["runinfo"]["entrypoint"])).replace(
                    "\\", "\\\\"),
                icon_path="'{}'".format(os.path.join(self.source_folder, "packaging",
                                                     self.conan_data["pyinstaller"]["icon"][
                                                         str(self.settings.os)])).replace("\\", "\\\\"),
                entitlements_file=entitlements_file if self.settings.os == "Macos" else "None"
            )

        if self.options.get_safe("enable_i18n", False) and self._i18n_options["extract"]:
            vb = VirtualBuildEnv(self)
            vb.generate()

            # # FIXME: once m4, autoconf, automake are Conan V2 ready use self.win_bash and add gettext as base tool_requirement
            cpp_info = self.dependencies["gettext"].cpp_info
            pot = self.python_requires["translationextractor"].module.ExtractTranslations(self, cpp_info.bindirs[0])
            pot.generate()

    def build(self):
        if self.options.get_safe("enable_i18n", False) and self._i18n_options["build"]:
            for po_file in self.source_path.joinpath("resources", "i18n").glob("**/*.po"):
                mo_file = Path(self.build_folder, po_file.with_suffix('.mo').relative_to(self.source_path))
                mo_file = mo_file.parent.joinpath("LC_MESSAGES", mo_file.name)
                mkdir(self, str(unix_path(self, Path(mo_file).parent)))
                cpp_info = self.dependencies["gettext"].cpp_info
                self.run(f"{cpp_info.bindirs[0]}/msgfmt {po_file} -o {mo_file} -f", env="conanbuild", ignore_errors=True)

    def deploy(self):
        copy(self, "*", os.path.join(self.package_folder, self.cpp.package.resdirs[2]), os.path.join(self.install_folder, "packaging"), keep_path = True)

        # Copy resources of Cura (keep folder structure) needed by pyinstaller to determine the module structure
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.bindirs[0]), str(self._base_dir), keep_path = False)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.libdirs[0]), str(self._site_packages.joinpath("cura")), keep_path = True)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.resdirs[0]), str(self._share_dir.joinpath("cura", "resources")), keep_path = True)
        copy(self, "*", os.path.join(self.package_folder, self.cpp_info.resdirs[1]), str(self._share_dir.joinpath("cura", "plugins")), keep_path = True)

        # Copy resources of Uranium (keep folder structure)
        uranium = self.dependencies["uranium"].cpp_info
        copy(self, "*", uranium.resdirs[0], str(self._share_dir.joinpath("uranium", "resources")), keep_path = True)
        copy(self, "*", uranium.resdirs[1], str(self._share_dir.joinpath("uranium", "plugins")), keep_path = True)
        copy(self, "*", uranium.libdirs[0], str(self._site_packages.joinpath("UM")), keep_path = True)

        # Generate the GitHub Action version info Environment
        version = self.conf.get("user.cura:version", default = self.version, check_type = str)
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
        save(self, os.path.join(self._script_dir, f"activate_github_actions_version_env{ext}"), activate_github_actions_version_env)

        self._generate_cura_version(os.path.join(self._site_packages, "cura"))

        entitlements_file = "'{}'".format(Path(self.cpp_info.res_paths[2], "MacOS", "cura.entitlements"))
        self._generate_pyinstaller_spec(location = self._base_dir,
                                        entrypoint_location = "'{}'".format(os.path.join(self.package_folder, self.cpp_info.bindirs[0], self.conan_data["pyinstaller"]["runinfo"]["entrypoint"])).replace("\\", "\\\\"),
                                        icon_path = "'{}'".format(os.path.join(self.package_folder, self.cpp_info.resdirs[2], self.conan_data["pyinstaller"]["icon"][str(self.settings.os)])).replace("\\", "\\\\"),
                                        entitlements_file = entitlements_file if self.settings.os == "Macos" else "None")

    def package(self):
        copy(self, "cura_app.py", src = self.source_folder, dst = os.path.join(self.package_folder, self.cpp.package.bindirs[0]))
        copy(self, "*", src = os.path.join(self.source_folder, "cura"), dst = os.path.join(self.package_folder, self.cpp.package.libdirs[0]))
        copy(self, "*", src = os.path.join(self.source_folder, "resources"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[0]))
        copy(self, "*.mo", os.path.join(self.build_folder, "resources"), os.path.join(self.package_folder, "resources"))
        copy(self, "*", src = os.path.join(self.source_folder, "plugins"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[1]))
        copy(self, "requirement*.txt", src = self.source_folder, dst = os.path.join(self.package_folder, self.cpp.package.resdirs[-1]))
        copy(self, "*", src = os.path.join(self.source_folder, "packaging"), dst = os.path.join(self.package_folder, self.cpp.package.resdirs[2]))

        # Remove the CuraEngineGradualFlow plugin from the package
        rmdir(self, os.path.join(self.package_folder, self.cpp.package.resdirs[1], "CuraEngineGradualFlow"))
        rm(self, "bundled_*.json", os.path.join(self.package_folder, self.cpp.package.resdirs[0], "bundled_packages"), recursive = False)

        # Remove the fdm_materials from the package
        rmdir(self, os.path.join(self.package_folder, self.cpp.package.resdirs[0], "materials"))

    def package_info(self):
        self.user_info.pip_requirements = "requirements.txt"
        self.user_info.pip_requirements_git = "requirements-ultimaker.txt"
        self.user_info.pip_requirements_build = "requirements-dev.txt"

        if self.in_local_cache:
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
            self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "site-packages"))
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "plugins"))
            self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "plugins"))
        else:
            self.runenv_info.append_path("PYTHONPATH", self.source_folder)
            self.env_info.PYTHONPATH.append(self.source_folder)
            self.runenv_info.append_path("PYTHONPATH", os.path.join(self.source_folder, "plugins"))
            self.env_info.PYTHONPATH.append(os.path.join(self.source_folder, "plugins"))

    def package_id(self):
        self.info.clear()

        # The following options shouldn't be used to determine the hash, since these are only used to set the CuraVersion.py
        # which will als be generated by the deploy method during the `conan install cura/5.1.0@_/_`
        del self.info.options.enterprise
        del self.info.options.staging
        del self.info.options.devtools
        del self.info.options.cloud_api_version
        del self.info.options.display_name
        del self.info.options.cura_debug_mode
        if self.options.get_safe("enable_i18n", False):
            del self.info.options.enable_i18n

        # TODO: Use the hash of requirements.txt and requirements-ultimaker.txt, Because changing these will actually result in a different
        #  Cura. This is needed because the requirements.txt aren't managed by Conan and therefor not resolved in the package_id. This isn't
        #  ideal but an acceptable solution for now.
