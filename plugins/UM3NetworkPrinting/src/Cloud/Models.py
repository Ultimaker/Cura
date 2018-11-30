# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from ..Models import BaseModel


##  Class representing a cloud connected cluster.
class CloudCluster(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_id = None  # type: str
        self.host_guid = None  # type: str
        self.host_name = None  # type: str
        self.host_version = None  # type: str
        self.status = None  # type: str
        super().__init__(**kwargs)

    def validate(self):
        if not self.cluster_id:
            raise ValueError("cluster_id is required on CloudCluster")


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfigurationMaterial(BaseModel):
    def __init__(self, **kwargs):
        self.guid = None  # type: str
        self.brand = None  # type: str
        self.color = None  # type: str
        self.material = None  # type: str
        super().__init__(**kwargs)


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfiguration(BaseModel):
    def __init__(self, **kwargs):
        self.extruder_index = None  # type: str
        self.material = None  # type: CloudClusterPrinterConfigurationMaterial
        self.nozzle_diameter = None  # type: str
        self.printer_core_id = None  # type: str
        super().__init__(**kwargs)


##  Class representing a cluster printer
class CloudClusterPrinter(BaseModel):
    def __init__(self, **kwargs):
        self.configuration = None  # type: CloudClusterPrinterConfiguration
        self.enabled = None  # type: str
        self.firmware_version = None  # type: str
        self.friendly_name = None  # type: str
        self.ip_address = None  # type: str
        self.machine_variant = None  # type: str
        self.status = None  # type: str
        self.unique_name = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)


## Class representing a cloud cluster print job constraint
class CloudClusterPrintJobConstraint(BaseModel):
    def __init__(self, **kwargs):
        self.require_printer_name: None  # type: str
        super().__init__(**kwargs)

##  Class representing a print job
class CloudClusterPrintJob(BaseModel):
    def __init__(self, **kwargs):
        self.assigned_to = None  # type: str
        self.configuration = None  # type: str
        self.constraints = None  # type: str
        self.created_at = None  # type: str
        self.force = None  # type: str
        self.last_seen = None  # type: str
        self.machine_variant = None  # type: str
        self.name = None  # type: str
        self.network_error_count = None  # type: str
        self.owner = None  # type: str
        self.printer_uuid = None  # type: str
        self.started = None  # type: str
        self.status = None  # type: str
        self.time_elapsed = None  # type: str
        self.time_total = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)


class JobUploadRequest(BaseModel):
    def __init__(self, **kwargs):
        self.file_size = None  # type: int
        self.job_name = None  # type: str
        super().__init__(**kwargs)


class JobUploadResponse(BaseModel):
    def __init__(self, **kwargs):
        self.download_url = None  # type: str
        self.job_id = None  # type: str
        self.job_name = None  # type: str
        self.slicing_details = None  # type: str
        self.status = None  # type: str
        self.upload_url = None  # type: str
        super().__init__(**kwargs)
