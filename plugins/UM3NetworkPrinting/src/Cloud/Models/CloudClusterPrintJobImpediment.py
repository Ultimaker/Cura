# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


## Class representing the reasons that prevent this job from being printed on the associated printer
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterPrintJobImpediment(BaseCloudModel):
    ## Creates a new print job constraint.
    #  \param translation_key: A string indicating a reason the print cannot be printed, such as 'does_not_fit_in_build_volume'
    #  \param severity: A number indicating the severity of the problem, with higher being more severe
    def __init__(self, translation_key: str, severity: int, **kwargs) -> None:
        self.translation_key = translation_key
        self.severity = severity
        super().__init__(**kwargs)
