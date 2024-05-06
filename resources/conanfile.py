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
    url = "https://github.com/Ultimaker/cura-private-data"
    description = "Cura Resources"
    topics = ("conan", "cura")
    exports = "LICENSE*"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True

    def set_version(self):
        if not self.version:
            self.version = self.conan_data["version"]

    def export(self):
        copy(self, pattern="conandata.yml", src=os.path.join(self.recipe_folder, ".."), dst=self.export_folder,
             keep_path=False)
        update_conandata(self, {"version": self.version})

    def export_sources(self):
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "definitions"),
             dst=os.path.join(self.export_sources_folder, "definitions"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "extruders"),
             dst=os.path.join(self.export_sources_folder, "extruders"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "images"),
             dst=os.path.join(self.export_sources_folder, "images"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "intent"),
             dst=os.path.join(self.export_sources_folder, "intent"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "meshes"),
             dst=os.path.join(self.export_sources_folder, "meshes"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "quality"),
             dst=os.path.join(self.export_sources_folder, "quality"))
        copy(self, pattern="*", src=os.path.join(self.recipe_folder, "variants"),
             dst=os.path.join(self.export_sources_folder, "variants"))

    def validate(self):
        if Version(self.version) <= Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def layout(self):
        self.cpp.source.resdirs = ["definitions", "extruders", "images", "intent", "meshes", "quality", "variants"]
        self.cpp.package.resdirs = ["res/definitions", "res/extruders", "res/images", "res/intent", "res/meshes", "res/quality", "res/variants"]

    def package(self):
        copy(self, "*", os.path.join(self.export_sources_folder),
             os.path.join(self.package_folder, "res"))

    def package_info(self):
        self.cpp_info.includedirs = []

    def package_id(self):
        self.info.clear()
