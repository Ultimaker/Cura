import os
import shutil
import pathlib

from conan.tools.env.virtualrunenv import runenv_from_cpp_info, VirtualRunEnv
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conans import ConanFile


class CuraVirtualRunEnv(VirtualRunEnv):
    """
    Creates a shell script that sets the environment with a self consuming Environment.

        Make sure you add CuraVersion.py with the following content to the folder cura::

        import os

        CuraAppDisplayName = os.getenv("CURA_APP_DISPLAY_NAME", "Cura")
        CuraVersion = os.getenv("CURA_VERSION", "master")
        CuraBuildType = os.getenv("CURA_BUILD_TYPE", "")
        CuraDebugMode = True
        CuraCloudAPIRoot = os.getenv("CURA_CLOUD_API_ROOT", "https://api.ultimaker.com")
        CuraCloudAccountAPIRoot = os.getenv("CURA_CLOUD_ACCOUNT_API_ROOT", "https://account.ultimaker.com")
        CuraDigitalFactoryURL = os.getenv("CURA_DIGITAL_FACTORY_URL", "https://digitalfactory.ultimaker.com")

    """

    def environment(self):
        runenv = self._conanfile.runenv_info  # Only difference with the VirtualRunEnv
        host_req = self._conanfile.dependencies.host
        test_req = self._conanfile.dependencies.test
        for _, dep in list(host_req.items()) + list(test_req.items()):
            if dep.runenv_info:
                runenv.compose_env(dep.runenv_info)
            runenv.compose_env(runenv_from_cpp_info(self._conanfile, dep.cpp_info))

        return runenv


class CuraConan(ConanFile):
    name = "Cura"
    version = "4.11.0"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt5", "qt", "qml", "3d-printing", "slicer")
    settings = "os", "compiler", "build_type", "arch"
    revision_mode = "scm"
    build_policy = "missing"
    exports = "LICENSE", str(os.path.join(".conan_gen", "Cura.run.xml.jinja"))
    base_path = pathlib.Path(__file__).parent.absolute()
    python_requires = "VirtualEnvironmentBuildTool/0.1@ultimaker/testing", "PyCharmRunEnvironment/0.1@ultimaker/testing"
    pycharm_targets = [
        {
            "jinja_path": str(os.path.join(base_path, ".conan_gen", "Cura.run.xml.jinja")),
            "name": "cura_app",
            "entry_point": "cura_app.py",
            "arguments": "",
            "run_path": str(os.path.join(base_path, ".run"))
        },
        {
            "jinja_path": str(os.path.join(base_path, ".conan_gen", "Cura.run.xml.jinja")),
            "name": "cura_app_external_engine",
            "entry_point": "cura_app.py",
            "arguments": "--external",
            "run_path": str(os.path.join(base_path, ".run"))
        }
    ]
    options = {
        "enterprise": [True, False],
        "staging": [True, False],
        "external_engine": [True, False]
    }
    default_options = {
        "enterprise": False,
        "staging": False,
        "external_engine": False
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    def build_requirements(self):
        self.build_requires("cmake/[>=3.16.2]")

    def layout(self):
        self.runenv_info.define("CURA_APP_DISPLAY_NAME", self.name)
        self.runenv_info.define("CURA_VERSION", "master")
        self.runenv_info.define("CURA_BUILD_TYPE", "Enterprise" if self.options.enterprise else "")
        staging = "-staging" if self.options.staging else ""
        self.runenv_info.define("CURA_CLOUD_API_ROOT", f"https://api{staging}.ultimaker.com")
        self.runenv_info.define("CURA_CLOUD_ACCOUNT_API_ROOT", f"https://account{staging}.ultimaker.com")
        self.runenv_info.define("CURA_DIGITAL_FACTORY_URL", f"https://digitalfactory{staging}.ultimaker.com")

    def generate(self):
        shutil.copy(os.path.join(self.base_path, ".conan_gen", "CuraVersion.py"), os.path.join(self.base_path, "cura", "CuraVersion.py"))
        rv = CuraVirtualRunEnv(self)
        rv.generate()

        pv = self.python_requires["PyCharmRunEnvironment"].module.PyCharmRunEnvironment(self)
        pv.generate()

        cmake = CMakeDeps(self)
        cmake.generate()

        # Make sure CuraEngine exist at the root
        ext = ""
        if self.settings.os == "Windows":
            ext = ".exe"
        curaengine_src = pathlib.Path(self.deps_user_info["CuraEngine"].CURAENGINE)
        curaengine_dst = pathlib.Path(os.path.join(self.base_path, f"CuraEngine{ext}"))
        if os.path.exists(curaengine_dst):
            os.remove(curaengine_dst)
        try:
            curaengine_dst.symlink_to(curaengine_src)
        except OSError as e:
            self.output.warn("Could not create symlink to CuraEngine copying instead")
            shutil.copy(curaengine_src, curaengine_dst)

        tc = CMakeToolchain(self)
        tc.variables["Python_VERSION"] = self.deps_cpp_info["Python"].version
        tc.variables["URANIUM_CMAKE_PATH"] = self.deps_user_info["Uranium"].URANIUM_CMAKE_PATH
        tc.generate()

        vb = self.python_requires["VirtualEnvironmentBuildTool"].module.VirtualEnvironmentBuildTool(self)
        vb.configure(self.deps_user_info["Python"].interp)
        # FIXME: create propper deps
        vb.build("numpy==1.20.2 scipy==1.6.2 shapely==1.7.1 appdirs==1.4.3 certifi==2019.11.28 cffi==1.14.1 chardet==3.0.4 cryptography==3.4.6 decorator==4.4.0 idna==2.8 importlib-metadata==3.7.2 netifaces==0.10.9 networkx==2.3 numpy-stl==2.10.1 packaging==18.0 pycollada==0.6 pycparser==2.19 pyparsing==2.4.2 PyQt5==5.15.4 pyserial==3.4 python-dateutil==2.8.0 python-utils==2.3.0 requests==2.22.0 sentry-sdk==0.13.5 six==1.12.0 trimesh==3.2.33 twisted==21.2.0 urllib3==1.25.8 zeroconf==0.31.0 keyring==23.0.1")

    def requirements(self):
        self.requires(f"Python/3.8.10@python/testing")
        self.requires(f"Charon/4.11.0@ultimaker/testing")
        self.requires(f"pynest2d/4.11.0@ultimaker/testing")
        self.requires(f"Savitar/4.11.0@ultimaker/testing")
        self.requires(f"Uranium/4.11.0@ultimaker/testing")
        self.requires(f"CuraEngine/4.11.0@ultimaker/testing")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        cmake.install()
