import os

from conan import ConanFile
from conan.tools.files import copy, update_conandata
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=2.7.0"


class CuraResource(ConanFile):
    name = "cura_resources"
    license = ""
    author = "UltiMaker"
    url = "https://github.com/Ultimaker/cura"
    description = "Cura Resources"
    topics = ("conan", "cura")
    no_copy_source = True
    package_type = "shared-library"

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

    def layout(self):
        self.cpp.source.resdirs = self._shared_resources
        self.cpp.package.resdirs = [f"res/{res}" for res in self._shared_resources]

    def package(self):
        copy(self, "*", os.path.join(self.export_sources_folder),
             os.path.join(self.package_folder, "res"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.runenv_info.define("CURA_RESOURCES", os.path.join(self.package_folder, "res"))
        self.runenv_info.define("CURA_ENGINE_SEARCH_PATH", os.path.join(self.package_folder, "res", "definitions"))
        self.runenv_info.define("CURA_ENGINE_SEARCH_PATH", os.path.join(self.package_folder, "res", "extruders"))

    def package_id(self):
        self.info.clear()
