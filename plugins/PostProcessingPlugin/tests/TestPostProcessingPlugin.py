
import os
import sys
from unittest.mock import patch, MagicMock

from UM.Resources import Resources
from UM.Trust import Trust
from ..PostProcessingPlugin import PostProcessingPlugin

# not sure if needed
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

""" In this file, commnunity refers to regular Cura for makers."""


# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_community_user_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed("blaat.py")

# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_community_bundled_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed(_bundled_file_path())

# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", True)
def test_enterprise_unsigned_user_script_not_allowed():
    assert not PostProcessingPlugin._isScriptAllowed("blaat.py")

# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", True)
def test_enterprise_signed_user_script_allowed():
    mocked_trust = MagicMock()
    mocked_trust.signedFileCheck = MagicMock(return_value=True)

    realSignatureFileExistsFor = Trust.signatureFileExistsFor
    Trust.signatureFileExistsFor = MagicMock(return_value=True)

    with patch("UM.Trust.Trust.getInstanceOrNone", return_value=mocked_trust):
        assert PostProcessingPlugin._isScriptAllowed("blaat.py")

    # cleanup
    Trust.signatureFileExistsFor = realSignatureFileExistsFor

# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_enterprise_bundled_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed(_bundled_file_path())


def _bundled_file_path():
    return os.path.join(
        Resources.getStoragePath(Resources.Resources) + "scripts/blaat.py"
    )
