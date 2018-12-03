# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List

from ..Models import BaseModel


##  Class representing a cloud connected cluster.
class CloudCluster(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_id = None  # type: str
        self.host_guid = None  # type: str
        self.host_name = None  # type: str
        self.host_version = None  # type: str
        self.status = None  # type: str
        self.is_online = None  # type: bool
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
        self.print_core_id = None  # type: str
        super().__init__(**kwargs)

        if isinstance(self.material, dict):
            self.material = CloudClusterPrinterConfigurationMaterial(**self.material)


##  Class representing a cluster printer
class CloudClusterPrinter(BaseModel):
    def __init__(self, **kwargs):
        self.configuration = []  # type: List[CloudClusterPrinterConfiguration]
        self.enabled = None  # type: str
        self.firmware_version = None  # type: str
        self.friendly_name = None  # type: str
        self.ip_address = None  # type: str
        self.machine_variant = None  # type: str
        self.status = None  # type: str
        self.unique_name = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)

        self.configuration = [CloudClusterPrinterConfiguration(**c)
                              if isinstance(c, dict) else c for c in self.configuration]


## Class representing a cloud cluster print job constraint
class CloudClusterPrintJobConstraint(BaseModel):
    def __init__(self, **kwargs):
        self.require_printer_name = None  # type: str
        super().__init__(**kwargs)


##  Class representing a print job
class CloudClusterPrintJob(BaseModel):
    def __init__(self, **kwargs):
        self.assigned_to = None  # type: str
        self.configuration = []  # type: List[CloudClusterPrinterConfiguration]
        self.constraints = []  # type: List[CloudClusterPrintJobConstraint]
        self.created_at = None  # type: str
        self.force = None  # type: str
        self.last_seen = None  # type: str
        self.machine_variant = None  # type: str
        self.name = None  # type: str
        self.network_error_count = None  # type: int
        self.owner = None  # type: str
        self.printer_uuid = None  # type: str
        self.started = None  # type: str
        self.status = None  # type: str
        self.time_elapsed = None  # type: str
        self.time_total = None  # type: str
        self.uuid = None  # type: str
        super().__init__(**kwargs)
        self.printers = [CloudClusterPrinterConfiguration(**c) if isinstance(c, dict) else c
                         for c in self.configuration]
        self.printers = [CloudClusterPrintJobConstraint(**p) if isinstance(p, dict) else p
                         for p in self.constraints]


class CloudClusterStatus(BaseModel):
    def __init__(self, **kwargs):
        self.printers = []  # type: List[CloudClusterPrinter]
        self.print_jobs = []  # type: List[CloudClusterPrintJob]
        super().__init__(**kwargs)

        self.printers = [CloudClusterPrinter(**p) if isinstance(p, dict) else p for p in self.printers]
        self.print_jobs = [CloudClusterPrintJob(**j) if isinstance(j, dict) else j for j in self.print_jobs]


class JobUploadRequest(BaseModel):
    def __init__(self, **kwargs):
        self.file_size = None  # type: int
        self.job_name = None  # type: str
        self.content_type = None  # type: str
        super().__init__(**kwargs)


class JobUploadResponse(BaseModel):
    def __init__(self, **kwargs):
        self.download_url = None  # type: str
        self.job_id = None  # type: str
        self.job_name = None  # type: str
        self.slicing_details = None  # type: str
        self.status = None  # type: str
        self.upload_url = None  # type: str
        self.content_type = None  # type: str
        super().__init__(**kwargs)


class PrintResponse(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_job_id = None  # type: str
        self.job_id = None  # type: str
        self.status = None  # type: str
        super().__init__(**kwargs)
