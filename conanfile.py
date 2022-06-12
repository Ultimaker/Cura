import os

from platform import python_version

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
    short_paths = True
    generators = "VirtualPythonEnv"
    options = {
        "python_version": "ANY",
        "enterprise": [True, False],
        "staging": [True, False],
        "external_engine": [True, False],
        "devtools": [True, False]
    }
    default_options = {
        "python_version": "system",
        "enterprise": False,
        "staging": False,
        "external_engine": False,
        "devtools": False
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

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
            if tools.Version(self.version) <= tools.Version("4"):
                raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        self.requires("curaengine/latest@ultimaker/cura-9365")  # FIXME: change to ultimaker/stable once the curaengine PR for CURA-9365 has been merged
        self.requires("arcus/latest@ultimaker/cura-9365")  # FIXME: change to ultimaker/stable once the arcus PR for CURA-9365 has been merged
        self.requires("savitar/latest@ultimaker/cura-9365")  # FIXME: change to ultimaker/stable once the savitar PR for CURA-9365 has been merged
        self.requires("pynest2d/latest@ultimaker/cura-9365")  # FIXME: change to ultimaker/stable once the pynest2d PR for CURA-9365 has been merged

    def generate(self):
        pass

    def layout(self):
        self.folders.source = "."
        self.folders.build = "venv"
        self.folders.generators = os.path.join(self.folders.build, "conan")

        # FIXME: Once libCharon en Uranium are also Packages
        if "PYTHONPATH" in os.environ:
            self.runenv_info.append_path("PYTHONPATH", os.environ["PYTHONPATH"])

    def imports(self):
        self.copy("CuraEngine.exe", root_package = "curaengine", src = "@bindirs", dst = self.source_folder, keep_path = False)
        self.copy("CuraEngine", root_package = "curaengine", src = "@bindirs", dst = self.source_folder, keep_path = False)
        self.copy("*.dll", src = "@bindirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.pyd", src = "@libdirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.pyi", src = "@libdirs", dst = os.path.join(self.folders.build, "Lib", "site-packages"))
        self.copy("*.dylib", src = "@libdirs", dst = os.path.join(self.folders.build, "bin"))
