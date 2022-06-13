import os
import shutil
from pathlib import Path

from platform import python_version

from jinja2 import Template

from conan import ConanFile
from conans import tools
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
    exports = "LICENSE*"
    settings = "os", "compiler", "build_type", "arch"
    generators = "VirtualPythonEnv"
    options = {
        "python_version": "ANY",
        "enterprise": ["True", "False", "true", "false"],
        "staging": ["True", "False", "true", "false"],
        "devtools": [True, False],
        "cloud_api_version": "ANY",
        "display_name": "ANY"
    }
    default_options = {
        "python_version": "system",
        "enterprise": "False",
        "staging": "False",
        "devtools": False,
        "cloud_api_version": "1",
        "display_name": "Ultimaker Cura"
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    @property
    def conandata_version(self):
        version = tools.Version(self.version)
        version = f"{version.major}.{version.minor}.{version.patch}-{version.prerelease}"
        if version in self.conan_data:
            return version
        return "dev"

    def set_version(self):
        if not self.version:
            if "CURA_VERSION" in os.environ:
                self.version = os.environ["CURA_VERSION"]
            else:
                self.version = "dev"

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
            return ["requirements.txt", "requirements-dev.txt"]
        return "requirements.txt"

    def config_options(self):
        if self.options.python_version == "system":
            self.options.python_version = python_version()

    def configure(self):
        self.options["*"].shared = True

    def validate(self):
        if self.version:
            if self.version != "dev" and tools.Version(self.version) <= tools.Version("4"):
                raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        for req in self.conan_data[self.conandata_version]["conan"].values():
            self.requires(req)

    def generate(self):
        for source in self.conan_data[self.conandata_version]["sources"].values():
            src_path = Path(self.source_folder, source["root"], source["src"])
            if not src_path.exists():
                continue
            dst_root_path = Path(self.source_folder, source["dst"])
            if dst_root_path.exists():
                shutil.rmtree(dst_root_path, ignore_errors = True)
            dst_root_path.mkdir(parents = True)
            if "filter" in source:
                for pattern in source["filter"]:
                    for file in src_path.glob(pattern):
                        rel_file = file.relative_to(src_path)
                        dst_file = dst_root_path.joinpath(rel_file)
                        if not dst_file.parent.exists():
                            dst_file.parent.mkdir(parents = True)
                        shutil.copy(file, dst_file)
            else:
                shutil.copytree(src_path, dst_root_path)

        with open(Path(self.source_folder, "cura", "CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        with open(Path(self.source_folder, "cura", "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self.options.display_name,
                cura_version = self.version if self.version else "dev",
                cura_build_type = "Enterprise" if self._enterprise else "",
                cura_debug_mode = self.settings.build_type != "Release",
                cura_cloud_api_root = self._cloud_api_root,
                cura_cloud_api_version = self.options.cloud_api_version,
                cura_cloud_account_api_root = self._cloud_account_api_root,
                cura_marketplace_root = self._marketplace_root,
                cura_digital_factory_url = self._digital_factory_url))

        if self.options.devtools:
            # Create the Ultimaker-Cura.spec based on the data in the conandata.yml
            with open(Path(self.source_folder, "Ultimaker-Cura.spec.jinja"), "r") as f:
                pyinstaller = Template(f.read())

            pyinstaller_metadata = self.conan_data[self.conandata_version]["pyinstaller"]
            datas = []
            for data in pyinstaller_metadata["datas"].values():
                if "package" in data:  # get the paths from conan package
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

            pathex = [str(Path(self.source_folder, p)) for p in pyinstaller_metadata["pathex"]]

            with open(Path(self.source_folder, "Ultimaker-Cura.spec"), "w") as f:
                f.write(pyinstaller.render(
                    name = str(self.options.display_name).replace(" ", "-"),
                    entrypoint = str(Path(self.source_folder, "cura_app.py")),
                    datas = datas,
                    binaries = binaries,
                    hiddenimports = pyinstaller_metadata["hiddenimports"],
                    collect_all = pyinstaller_metadata["collect_all"],
                    pathex = pathex,
                    icon = str(Path(self.source_folder, pyinstaller_metadata["icon"]))
                ))

    def layout(self):
        self.folders.source = "."
        self.folders.build = "venv"
        self.folders.generators = os.path.join(self.folders.build, "conan")

        # FIXME: Once libCharon en Uranium are also Packages
        self.runenv_info.append_path("PYTHONPATH", str(Path(__file__).parent))
        self.runenv_info.append_path("PYTHONPATH", str(Path(__file__).parent.parent.joinpath("uranium")))
        self.runenv_info.append_path("PYTHONPATH", str(Path(__file__).parent.parent.joinpath("libcharon")))

    def imports(self):
        self.copy("CuraEngine.exe", root_package = "curaengine", src = "@bindirs", dst = self.source_folder, keep_path = False)
        self.copy("CuraEngine", root_package = "curaengine", src = "@bindirs", dst = self.source_folder, keep_path = False)
        self.copy("*.dll", src = "@bindirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.pyd", src = "@libdirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.pyi", src = "@libdirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.dylib", src = "@libdirs", dst = os.path.join(self.folders.build, "bin"))
