import os
import sys
from pathlib import Path

from io import StringIO

from platform import python_version

from jinja2 import Template

from conan import ConanFile
from conan.tools import files
from conan.tools.env import VirtualRunEnv
from conans import tools
from conan.errors import ConanInvalidConfiguration, ConanException

required_conan_version = ">=1.47.0"


class CuraConan(ConanFile):
    name = "cura"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt5", "qt", "qml", "3d-printing", "slicer")
    build_policy = "missing"
    exports = "LICENSE*", "Ultimaker-Cura.spec.jinja", "CuraVersion.py.jinja", "requirements.txt", "requirements-dev.txt", "requirements-ultimaker.txt"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True  # We won't build so no need to copy sources to the build folder

    # FIXME: Remove specific branch once merged to main
    # Extending the conanfile with the UMBaseConanfile https://github.com/Ultimaker/conan-ultimaker-index/tree/CURA-9177_Fix_CI_CD/recipes/umbase
    python_requires = "umbase/0.1.1@ultimaker/testing"
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
        "cura_debug_mode": False
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    @property
    def _venv_path(self):
        if self.settings.os == "Windows":
            return "Scripts"
        return "bin"

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

    def source(self):
        with open(Path(self.source_folder, "CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        with open(Path(self.source_folder, "cura", "CuraVersion.py"), "w") as f:
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
        self.folders.generators = os.path.join(self.folders.build, "conan")

        self.cpp.package.libdirs = ["site-packages"]
        self.cpp.package.resdirs = ["res"]

    def generate(self):
        if self.options.devtools:
            with open(Path(self.source_folder, "Ultimaker-Cura.spec.jinja"), "r") as f:
                pyinstaller = Template(f.read())

            pyinstaller_metadata = self._um_data(self.version)["pyinstaller"]
            datas = []
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

            with open(Path(self.generators_folder, "Ultimaker-Cura.spec"), "w") as f:
                f.write(pyinstaller.render(
                    name = str(self.options.display_name).replace(" ", "-"),
                    entrypoint = os.path.join("..", "..", self._um_data(self.version)["runinfo"]["entrypoint"]),
                    datas = datas,
                    binaries = binaries,
                    hiddenimports = pyinstaller_metadata["hiddenimports"],
                    collect_all = pyinstaller_metadata["collect_all"],
                    icon = os.path.join("..", "..", pyinstaller_metadata["icon"][str(self.settings.os)])
                ))

    def imports(self):
        self.copy("CuraEngine.exe", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)
        self.copy("CuraEngine", root_package = "curaengine", src = "@bindirs", dst = "", keep_path = False)

        files.rmdir(self, "resources/materials")
        self.copy("*.fdm_material", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)
        self.copy("*.sig", root_package = "fdm_materials", src = "@resdirs", dst = "resources/materials", keep_path = False)

        self.copy("*.dll", src = "@bindirs", dst = "venv/Lib/site-packages")
        self.copy("*.pyd", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy("*.pyi", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy("*.dylib", src = "@libdirs", dst = "venv/bin")

    def deploy(self):
        # Setup the Virtual Python Environment in the user space
        python_interpreter = Path(self.deps_user_info["cpython"].python)

        # When on Windows execute as Windows Path
        if self.settings.os == "Windows":
            python_interpreter = Path(*[f'"{p}"' if " " in p else p for p in python_interpreter.parts])

        # Create the virtual environment
        self.run(f"""{python_interpreter} -m venv {self.install_folder}""", run_environment = True, env = "conanrun")

        # Make sure there executable is named the same on all three OSes this allows it to be called with `python`
        # simplifying GH Actions steps
        if self.settings.os != "Windows":
            python_venv_interpreter = Path(self.install_folder, self._venv_path, "python")
            if not python_venv_interpreter.exists():
                python_venv_interpreter.hardlink_to(Path(self.install_folder, self._venv_path, Path(sys.executable).stem + Path(sys.executable).suffix))
        else:
            python_venv_interpreter = Path(self.install_folder, self._venv_path, Path(sys.executable).stem + Path(sys.executable).suffix)

        if not python_venv_interpreter.exists():
            raise ConanException(f"Virtual environment Python interpreter not found at: {python_venv_interpreter}")
        if self.settings.os == "Windows":
            python_venv_interpreter = Path(*[f'"{p}"' if " " in p else p for p in python_venv_interpreter.parts])

        buffer = StringIO()
        outer = '"' if self.settings.os == "Windows" else "'"
        inner = "'" if self.settings.os == "Windows" else '"'
        self.run(f"{python_venv_interpreter} -c {outer}import sysconfig; print(sysconfig.get_path({inner}purelib{inner})){outer}",
                 env = "conanrun",
                 output = buffer)
        pythonpath = buffer.getvalue().splitlines()[-1]

        run_env = VirtualRunEnv(self)
        env = run_env.environment()

        env.define_path("VIRTUAL_ENV", self.install_folder)
        env.prepend_path("PATH", os.path.join(self.install_folder, self._venv_path))
        env.prepend_path("PYTHONPATH", pythonpath)
        env.unset("PYTHONHOME")

        envvars = env.vars(self.conanfile, scope = "run")

        # Install some base_packages
        self.run(f"""{python_venv_interpreter} -m pip install wheel setuptools""", run_environment = True, env = "conanrun")

        # Install the requirements*.text
        # TODO: loop through dependencies and go over each requirement file per dependency (maybe we should add this to the conandata, or
        # define cpp_user_info in dependencies

        # Copy CuraEngine.exe to bindirs of Virtual Python Environment
        # TODO: Fix source such that it will get the curaengine relative from the executable (Python bindir in this case)
        self.copy_deps("CuraEngine.exe", root_package = "curaengine", src = "@bindirs",
                       dst = os.path.join(self.install_folder, self._venv_path), keep_path = False)
        self.copy_deps("CuraEngine", root_package = "curaengine", src = "@bindirs",
                       dst = os.path.join(self.install_folder, self._venv_path), keep_path = False)

        # Copy resources of Cura (keep folder structure)
        self.copy_deps("*", root_package = "cura", src = "@resdirs", dst = os.path.join(self.install_folder, "share", "cura", "resources"),
                       keep_path = True)

        # Copy materials (flat)
        self.copy_deps("*.fdm_material", root_package = "fdm_materials", src = "@resdirs",
                       dst = os.path.join(self.install_folder, "share", "cura", "resources", "materials"), keep_path = False)
        self.copy_deps("*.sig", root_package = "fdm_materials", src = "@resdirs",
                       dst = os.path.join(self.install_folder, "share", "cura", "resources", "materials"), keep_path = False)

        # Copy resources of Uranium (keep folder structure)
        self.copy_deps("*", root_package = "uranium", src = "@resdirs",
                       dst = os.path.join(self.install_folder, "share", "cura", "resources"), keep_path = True)

        # Copy dynamic libs to site-packages
        self.copy_deps("*.dll", src = "@bindirs", dst = "venv/Lib/site-packages")
        self.copy_deps("*.pyd", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy_deps("*.pyi", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy_deps("*.dylib", src = "@libdirs", dst = "venv/bin")

        # Make sure the CuraVersion.py is up to date with the correct settings
        with open(Path(Path(__file__).parent, "CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        # TODO: Extend

    def package(self):
        self.copy("*", src = "cura", dst = os.path.join(self.cpp.package.libdirs[0], "cura"))
        self.copy("*", src = "plugins", dst = os.path.join(self.cpp.package.libdirs[0], "plugins"))
        self.copy("*", src = "resources", dst = os.path.join(self.cpp.package.resdirs[0], "resources"))

    def package_info(self):
        if self.in_local_cache:
            self.runenv_info.append_path("PYTHONPATH", self.cpp_info.libdirs[0])
        else:
            self.runenv_info.append_path("PYTHONPATH", self.source_folder)

    def package_id(self):
        del self.info.settings.os
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.arch
