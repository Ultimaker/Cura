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
        update_conandata(self, {"version": self.version})

    def export_sources(self):
        copy(self, "*", os.path.join(self.recipe_folder, "definitions"), os.path.join(self.export_sources_folder, "resources", "definitions"))
        copy(self, "*", os.path.join(self.recipe_folder, "extruders"), os.path.join(self.export_sources_folder, "resources", "extruders"))
        copy(self, "*", os.path.join(self.recipe_folder, "intent"), os.path.join(self.export_sources_folder, "resources", "intent"))
        copy(self, "*", os.path.join(self.recipe_folder, "meshes"), os.path.join(self.export_sources_folder, "resources", "meshes"))
        copy(self, "*", os.path.join(self.recipe_folder, "quality"), os.path.join(self.export_sources_folder, "resources", "quality"))
        copy(self, "*", os.path.join(self.recipe_folder, "variants"), os.path.join(self.export_sources_folder, "resources", "variants"))

    def validate(self):
        if Version(self.version) <= Version("4"):
            raise ConanInvalidConfiguration("Only versions 5+ are support")

    def package(self):
        copy(self, "*", os.path.join(self.export_sources_folder, "resources"), os.path.join(self.package_folder, "res", "resources"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = ["res"]

    def package_id(self):
        self.info.clear()
