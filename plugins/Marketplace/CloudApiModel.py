from typing import Union

from cura import ApplicationMetadata
from cura.UltimakerCloud import UltimakerCloudConstants


class CloudApiModel:
    sdk_version: Union[str, int] = ApplicationMetadata.CuraSDKVersion
    cloud_api_version: str = UltimakerCloudConstants.CuraCloudAPIVersion
    cloud_api_root: str = UltimakerCloudConstants.CuraCloudAPIRoot
    api_url: str = "{cloud_api_root}/cura-packages/v{cloud_api_version}/cura/v{sdk_version}".format(
            cloud_api_root = cloud_api_root,
            cloud_api_version = cloud_api_version,
            sdk_version = sdk_version
        )

    # https://api.ultimaker.com/cura-packages/v1/user/packages
    api_url_user_packages = "{cloud_api_root}/cura-packages/v{cloud_api_version}/user/packages".format(
        cloud_api_root = cloud_api_root,
        cloud_api_version = cloud_api_version,
    )

    @classmethod
    def userPackageUrl(cls, package_id: str) -> str:
        """https://api.ultimaker.com/cura-packages/v1/user/packages/{package_id}"""

        return (CloudApiModel.api_url_user_packages + "/{package_id}").format(
            package_id = package_id
        )
