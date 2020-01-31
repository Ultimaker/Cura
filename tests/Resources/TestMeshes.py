# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path  # To find the platform meshes.
import os  # To test the file size of platform meshes.
import pytest  # To define parametrised tests.

# Make sure we have the paths to the platform meshes.
all_meshes = sorted(os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "meshes")))
all_meshes = [os.path.join(os.path.dirname(__file__), "..", "..", "resources", "meshes", filename) for filename in all_meshes]

@pytest.mark.parametrize("file_path", all_meshes)
def test_meshSize(file_path: str) -> None:
    """
    Tests if the mesh files are not too big.

    Our policy is that platform meshes should not exceed 1MB.
    :param file_path: The path to the platform mesh to test.
    """
    assert os.stat(file_path).st_size < 1024 * 1024 * 1.1  # Even though our policy is 1MB, allow for 10% leniency.