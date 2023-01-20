# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json  # To parse the deprecated icons files.
import os  # To find the theme folders.
import pytest

theme_base = os.path.join(os.path.split(__file__)[0], "..", "resources", "themes")
theme_paths = [os.path.join(theme_base, theme_folder) for theme_folder in os.listdir(theme_base) if os.path.isdir(os.path.join(theme_base, theme_folder))]

@pytest.mark.parametrize("theme_path", theme_paths)
def test_deprecatedIconsExist(theme_path: str) -> None:
    icons_folder = os.path.join(theme_path, "icons")
    deprecated_icons_file = os.path.join(icons_folder, "deprecated_icons.json")
    if not os.path.exists(deprecated_icons_file):
        return  # No deprecated icons file, there is nothing to go wrong.

    # Find out which icons exist in this theme file.
    existing_icons = {}
    for size in [subfolder for subfolder in os.listdir(icons_folder) if os.path.isdir(os.path.join(icons_folder, subfolder))]:
        existing_icons[size] = set(os.path.splitext(fname)[0] for fname in os.listdir(os.path.join(icons_folder, size)))

    with open(deprecated_icons_file) as f:
        deprecated_icons = json.load(f)

    for entry in deprecated_icons.values():
        assert "new_icon" in entry  # For each deprecated icon we must know which icon replaced it.
        new_icon = entry["new_icon"]
        assert "size" in entry
        size = entry["size"]

        assert size in existing_icons  # The replacement icon must have a size that exists.
        assert new_icon in existing_icons[size]  # The new icon must exist for that size.
