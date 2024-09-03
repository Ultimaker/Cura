import os

from conan import ConanFile
from conan.tools.files import copy, update_conandata
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=1.58.0 <2.0.0"


class CuraResource(ConanFile):
    name = "cura_resources"
    license = ""
    author = "UltiMaker"
    url = "https://github.com/Ultimaker/cura"
    description = "Cura Resources"
    topics = ("conan", "cura")
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True


    @property
    def _shared_resources(self):
        return ["definitions", "extruders", "images", "intent", "meshes", "quality", "variants"]

    def set_version(self):
        if not self.version:
            self.version = self.conan_data["version"]

    def export(self):
        copy(self, pattern="LICENSE*", src=os.path.join(self.recipe_folder, ".."), dst=self.export_folder,
             keep_path=False)
        update_conandata(self, {"version": self.version})

    def export_sources(self):
        for shared_resources in self._shared_resources:
            copy(self, pattern="*", src=os.path.join(self.recipe_folder, shared_resources),
                 dst=os.path.join(self.export_sources_folder, shared_resources))

    def validate(self):
        if Version(self.version) <= Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def layout(self):
        self.cpp.source.resdirs = self._shared_resources
        self.cpp.package.resdirs = [f"res/{res}" for res in self._shared_resources]

    def package(self):
        copy(self, "*", os.path.join(self.export_sources_folder),
             os.path.join(self.package_folder, "res"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.runenv_info.append_path("CURA_RESOURCES", os.path.join(self.package_folder, "res"))
        self.runenv_info.append_path("CURA_ENGINE_SEARCH_PATH", os.path.join(self.package_folder, "res", "definitions"))
        self.runenv_info.append_path("CURA_ENGINE_SEARCH_PATH", os.path.join(self.package_folder, "res", "extruders"))
        self.env_info.CURA_RESOURCES.append(os.path.join(self.package_folder, "res"))
        self.env_info.CURA_ENGINE_SEARCH_PATH.append(os.path.join(self.package_folder, "res", "definitions"))
        self.env_info.CURA_ENGINE_SEARCH_PATH.append(os.path.join(self.package_folder, "res", "definitions"))

    def package_id(self):
        self.info.clear()
