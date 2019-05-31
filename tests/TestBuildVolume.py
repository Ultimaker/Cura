from unittest.mock import MagicMock, patch

import pytest

from cura.BuildVolume import BuildVolume

@pytest.fixture
def build_volume():
    mocked_application = MagicMock()
    mocked_platform = MagicMock(name="platform")
    with patch("cura.BuildVolume.Platform", mocked_platform):
        return BuildVolume(mocked_application)


def test_buildVolumeSetSizes(build_volume):
    build_volume.setWidth(10)
    assert build_volume.getDiagonalSize() == 10

    build_volume.setWidth(0)
    build_volume.setHeight(100)
    assert build_volume.getDiagonalSize() == 100

    build_volume.setHeight(0)
    build_volume.setDepth(200)
    assert build_volume.getDiagonalSize() == 200


