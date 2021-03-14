from typing import Union

from cura import ApplicationMetadata
from cura.UltimakerCloud import UltimakerCloudConstants


class CloudApiModel:
    sdk_version = ApplicationMetadata.CuraSDKVersion  # type: Union[str, int]
    cloud_api_version = UltimakerCloudConstants.CuraCloudAPIVersion  # type: str
    cloud_api_root = UltimakerCloudConstants.CuraCloudAPIRoot  # type: str
    api_url = "{cloud_api_root}/cura-packages/v{cloud_api_version}/cura/v{sdk_version}".format(
            cloud_api_root = cloud_api_root,
            cloud_api_version = cloud_api_version,
            sdk_version = sdk_version
        )  # type: str

    # https://api.ultimaker.com/cura-packages/v1/user/packages
    api_url_user_packages = "{cloud_api_root}/cura-packages/v{cloud_api_version}/user/packages".format(
        cloud_api_root=cloud_api_root,
        cloud_api_version=cloud_api_version,
    )

    @classmethod
    def userPackageUrl(cls, package_id: str) -> str:
        """https://api.ultimaker.com/cura-packages/v1/user/packages/{package_id}"""

        return (CloudApiModel.api_url_user_packages + "/{package_id}").format(
            package_id=package_id
        )
