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
    def _bin_dir(self):
        return self._base_dir.joinpath("bin")

    @property
    def _script_dir(self):
        if self.settings.os == "Windows":
            return self._bin_dir.joinpath("Scripts")
        return self._bin_dir.joinpath("bin")

    @property
    def _site_packages(self):
        if self.settings.os == "Windows":
            return self._bin_dir.joinpath("Lib", "site-packages")
        py_version = tools.Version(self.deps_cpp_info["cpython"].version)
        return self._bin_dir.joinpath("lib", f"python{py_version.major}.{py_version.minor}", "site-packages")

    @property
    def _py_interp(self):
        py_interp = self._bin_dir.joinpath(Path(self.deps_user_info["cpython"].python).name)
        if self.settings.os == "Windows":
            py_interp = Path(*[f'"{p}"' if " " in p else p for p in py_interp.parts])
        return py_interp

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
        self.folders.generators = Path(self.folders.build, "conan")

        self.cpp.package.libdirs = [os.path.join("site-packages", "cura")]
        self.cpp.package.bindirs = ["bin"]
        self.cpp.package.resdirs = ["resources", "plugins", "pip_requirements"]  # pip_requirements should be the last item in the list

    def generate(self):
        vr = VirtualRunEnv(self)
        vr.generate()

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

        # Copy resources of cura_binary_data
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[0],
                       dst = "venv/share/cura", keep_path = True)
        self.copy("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[1],
                       dst = "venv/share/cura", keep_path = True)

        self.copy("*.dll", src = "@bindirs", dst = "venv/Lib/site-packages")
        self.copy("*.pyd", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy("*.pyi", src = "@libdirs", dst = "venv/Lib/site-packages")
        self.copy("*.dylib", src = "@libdirs", dst = "venv/bin")

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

        # Copy resources of cura_binary_data
        self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[0],
                       dst = self._share_dir.joinpath("cura"), keep_path = True)
        self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[1],
                       dst = self._share_dir.joinpath("uranium"), keep_path = True)
        if self.settings.os == "Windows":
            self.copy_deps("*", root_package = "cura_binary_data", src = self.deps_cpp_info["cura_binary_data"].resdirs[2],
                           dst = self._share_dir.joinpath("windows"), keep_path = True)

        # Copy CPython to user space
        self.copy_deps("*", root_package = "cpython", src = "@bindirs", dst = self._bin_dir, keep_path = True)

        # Copy other shared libs and compiled python modules
        self.copy_deps("*.dll", src = "@bindirs", dst = self._site_packages)
        self.copy_deps("*.pyd", src = "@libdirs", dst = self._site_packages)
        self.copy_deps("*.pyi", src = "@libdirs", dst = self._site_packages)
        self.copy_deps("*.dylib", src = "@libdirs", dst = self._site_packages)

        run_env = VirtualRunEnv(self)
        env = run_env.environment()
        env.define_path("PYTHONPATH", str(self._site_packages))
        env.unset("PYTHONHOME")

        for dy_path in [self._bin_dir, self._script_dir, self._site_packages, self._site_packages.joinpath("PyQt6", "Qt6", "bin")]:
            env.prepend_path("PATH", str(dy_path))
            env.prepend_path("LD_LIBRARY_PATH", str(dy_path))
            env.prepend_path("DYLD_LIBRARY_PATH", str(dy_path))

        envvars = env.vars(self, scope = "run")
        envvars.save_ps1(str(self._base_dir.joinpath("cura_activate.ps1")))
        envvars.save_bat(str(self._base_dir.joinpath("cura_activate.bat")))
        envvars.save_sh(str(self._base_dir.joinpath("cura_activate.sh")))

        # Install the requirements*.txt for Cura her dependencies
        # Note: user_info only stores str()
        self.run(f"{self._py_interp} -m pip install wheel setuptools sip==6.5.1 -t {str(self._site_packages)} --upgrade --isolated",
                 run_environment = True, env = "conanrun")

        # FIXME: PyQt6, somehow still finds the system Python lib. This cause it fail when importing QtNetwork
        #  possible solution is to force pip to compile the binaries from source: `--no-binary :all:` but that currently fails with sip.
        #  Maybe we should only compile PyQt6-*** deps
        for dep_name in self.deps_user_info:
            dep_user_info = self.deps_user_info[dep_name]
            pip_req_paths = [req_path for req_path in self.deps_cpp_info[dep_name].resdirs if req_path == "pip_requirements"]
            if len(pip_req_paths) != 1:
                continue
            pip_req_base_path = Path(pip_req_paths[0])
            if hasattr(dep_user_info, "pip_requirements"):
                req_txt = pip_req_base_path.joinpath(dep_user_info.pip_requirements)
                if req_txt.exists():
                    self.run(f"{self._py_interp} -m pip install -r {req_txt} -t {str(self._site_packages)} --upgrade --isolated", run_environment = True, env = "conanrun")
                    self.output.success(f"Dependency {dep_name} specifies pip_requirements in user_info installed!")
                else:
                    self.output.warn(f"Dependency {dep_name} specifies pip_requirements in user_info but {req_txt} can't be found!")

            if hasattr(dep_user_info, "pip_requirements_git"):
                req_txt = pip_req_base_path.joinpath(dep_user_info.pip_requirements_git)
                if req_txt.exists():
                    self.run(f"{self._py_interp} -m pip install -r {req_txt} -t {str(self._site_packages)} --upgrade --isolated", run_environment = True, env = "conanrun")
                    self.output.success(f"Dependency {dep_name} specifies pip_requirements_git in user_info installed!")
                else:
                    self.output.warn(f"Dependency {dep_name} specifies pip_requirements_git in user_info but {req_txt} can't be found!")

        # Install Cura requirements*.txt
        pip_req_base_path = Path(self.cpp_info.rootpath, self.cpp_info.resdirs[-1])
        # Add the dev reqs needed for pyinstaller
        self.run(f"{self._py_interp} -m pip install -r {pip_req_base_path.joinpath(self.user_info.pip_requirements_build)} -t {str(self._site_packages)} --upgrade --isolated",
                 run_environment = True, env = "conanrun")

        # Install the requirements.text for cura
        self.run(f"{self._py_interp} -m pip install -r {pip_req_base_path.joinpath(self.user_info.pip_requirements_git)} -t {str(self._site_packages)} --upgrade --isolated",
                 run_environment = True, env = "conanrun")
        # Do the final requirements last such that these dependencies takes precedence over possible previous installed Python modules.
        # Since these are actually shipped with Cura and therefore require hashes and pinned version numbers in the requirements.txt
        self.run(f"{self._py_interp} -m pip install -r {pip_req_base_path.joinpath(self.user_info.pip_requirements)} -t {str(self._site_packages)} --upgrade --isolated",
                 run_environment = True,
                 env = "conanrun")

    def package(self):
        self.copy("cura_app.py", src = ".", dst = self.cpp.package.bindirs[0])
        self.copy("*", src = "cura", dst = self.cpp.package.libdirs[0])
        self.copy("*", src = "resources", dst = self.cpp.package.resdirs[0])
        self.copy("*", src = "plugins", dst = self.cpp.package.resdirs[1])
        self.copy("requirement*.txt", src = ".", dst = self.cpp.package.resdirs[-1])

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
