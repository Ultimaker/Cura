import os
from pathlib import Path

from platform import python_version

from jinja2 import Template

from conan import ConanFile
from conan.tools import files
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
    no_copy_source = True  # We won't build so no need to copy sources to the build folder

    # FIXME: Remove specific branch once merged to main
    # Extending the conanfile with the UMBaseConanfile https://github.com/Ultimaker/conan-ultimaker-index/tree/CURA-9177_Fix_CI_CD/recipes/umbase
    python_requires = "umbase/[>=0.1.1]@ultimaker/testing"
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

    def configure(self):
        self.options["*"].shared = True
        if self.settings.os == "Windows":
            # Needed to compile CPython on Windows with our configuration voor Visual Studio
            self.options["mpdecimal"].cxx = True
            self.options["mpdecimal"].shared = False
            self.options["libffi"].shared = False

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

    def generate(self):
        # TODO: handle materials when running from source and using the fdm_materials

        with open(Path(self.source_folder, "cura", "CuraVersion.py.jinja"), "r") as f:
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

        # Create the Ultimaker-Cura.spec
        # TODO: Create a generator for this
        # TODO: Create exception for not in_local_cache
        # TODO: Allow for paths to be determine when installing from local cache without root_folder
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
