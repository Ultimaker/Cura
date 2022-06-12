import os
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
    short_paths = True
    generators = "VirtualPythonEnv"
    options = {
        "python_version": "ANY",
        "enterprise": [True, False],
        "staging": [True, False],
        "external_engine": [True, False],
        "devtools": [True, False],
        "cloud_api_version": "ANY",
        "display_name": "ANY"
    }
    default_options = {
        "python_version": "system",
        "enterprise": False,
        "staging": False,
        "external_engine": False,
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

    def set_version(self):
        if not self.version:
            if "CURA_VERSION" in os.environ:
                self.version = os.environ["CURA_VERSION"]
            else:
                self.version = "main"

    @property
    def _cloud_api_root(self):
        return "https://api-staging.ultimaker.com" if self.options.staging else "https://api.ultimaker.com"

    @property
    def _cloud_account_api_root(self):
        return "https://account-staging.ultimaker.com" if self.options.staging else "https://account.ultimaker.com"

    @property
    def _marketplace_root(self):
        return "https://marketplace-staging.ultimaker.com" if self.options.staging else "https://marketplace.ultimaker.com"

    @property
    def _digital_factory_url(self):
        return "https://digitalfactory-staging.ultimaker.com" if self.options.staging else "https://digitalfactory.ultimaker.com"

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
            if self.version != "main" and tools.Version(self.version) <= tools.Version("4"):
                raise ConanInvalidConfiguration("Only versions 5+ are support")

    def requirements(self):
        for req in self.conan_data[self.version]["conan"].values():
            self.requires(req)

    def source(self):
        username = os.environ.get("GIT_USERNAME", None)
        password = os.environ.get("GIT_PASSWORD", None)
        for git_src in self.conan_data[self.version]["git"].values():
            folder = Path(self.source_folder, git_src["directory"])
            should_clone = folder.exists()
            git = tools.Git(folder = folder, username = username, password = password)
            if should_clone:
                git.checkout(git_src["branch"])
            else:
                if username and password:
                    url = git.get_url_with_credentials(git_src["url"])
                else:
                    url = git_src["url"]
                git.clone(url = url, branch = git_src["branch"], shallow = True)

    def generate(self):
        with open(Path(self.source_folder, "cura", "CuraVersion.py.jinja"), "r") as f:
            cura_version_py = Template(f.read())

        with open(Path(self.source_folder, "cura", "CuraVersion.py"), "w") as f:
            f.write(cura_version_py.render(
                cura_app_name = self.name,
                cura_app_display_name = self.options.display_name,
                cura_version = self.version if self.version else "main",
                cura_build_type = "Enterprise" if self.options.enterprise else "",
                cura_debug_mode = self.settings.build_type != "Release",
                cura_cloud_api_root = self._cloud_api_root,
                cura_cloud_api_version = self.options.cloud_api_version,
                cura_cloud_account_api_root = self._cloud_account_api_root,
                cura_marketplace_root = self._marketplace_root,
                cura_digital_factory_url = self._digital_factory_url))

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
