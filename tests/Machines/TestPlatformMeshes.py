import pytest

import os
import os.path


__exclude_filenames = ["UltimakerRobot_support.stl"]


def collecAllPlatformMeshes():
    result = []
    for root, directories, filenames in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "meshes"))):
        for filename in filenames:
            if os.path.basename(filename) not in __exclude_filenames:
                result.append(os.path.join(root, filename))
    return result


platform_mesh_filepaths = collecAllPlatformMeshes()
MAX_MESH_FILE_SIZE = 1 * 1024 * 1024  # 1MB


# Check if the platform meshes adhere to the maximum file size (1MB)
@pytest.mark.parametrize("file_name", platform_mesh_filepaths)
def test_validatePlatformMeshSizes(file_name):
    assert os.path.getsize(file_name) <= MAX_MESH_FILE_SIZE, \
        "Platform mesh {} should be less than {}KB. Current file size: {}KB.".format(
            file_name,
            round(MAX_MESH_FILE_SIZE / 1024),
            round(os.path.getsize(file_name) / 1024, 2)
        )
