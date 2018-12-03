# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List

from ..Models import BaseModel


##  Class representing a cloud connected cluster.
class CloudCluster(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_id: str = None
        self.host_guid: str = None
        self.host_name: str = None
        self.host_version: str = None
        self.status: str = None
        super().__init__(**kwargs)

    def validate(self):
        if not self.cluster_id:
            raise ValueError("cluster_id is required on CloudCluster")


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfigurationMaterial(BaseModel):
    def __init__(self, **kwargs):
        self.guid: str = None
        self.brand: str = None
        self.color: str = None
        self.material: str = None
        super().__init__(**kwargs)


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfiguration(BaseModel):
    def __init__(self, **kwargs):
        self.extruder_index: str = None
        self.material: CloudClusterPrinterConfigurationMaterial = None
        self.nozzle_diameter: str = None
        self.print_core_id: str = None
        super().__init__(**kwargs)

        if isinstance(self.material, dict):
            self.material = CloudClusterPrinterConfigurationMaterial(**self.material)


##  Class representing a cluster printer
class CloudClusterPrinter(BaseModel):
    def __init__(self, **kwargs):
        self.configuration: List[CloudClusterPrinterConfiguration] = []
        self.enabled: str = None
        self.firmware_version: str = None
        self.friendly_name: str = None
        self.ip_address: str = None
        self.machine_variant: str = None
        self.status: str = None
        self.unique_name: str = None
        self.uuid: str = None
        super().__init__(**kwargs)

        self.configuration = [CloudClusterPrinterConfiguration(**c)
                              if isinstance(c, dict) else c for c in self.configuration]


## Class representing a cloud cluster print job constraint
class CloudClusterPrintJobConstraint(BaseModel):
    def __init__(self, **kwargs):
        self.require_printer_name: str = None
        super().__init__(**kwargs)


##  Class representing a print job
class CloudClusterPrintJob(BaseModel):
    def __init__(self, **kwargs):
        self.assigned_to: str = None
        self.configuration: List[CloudClusterPrinterConfiguration] = []
        self.constraints: List[CloudClusterPrintJobConstraint] = []
        self.created_at: str = None
        self.force: str = None
        self.last_seen: str = None
        self.machine_variant: str = None
        self.name: str = None
        self.network_error_count: int = None
        self.owner: str = None
        self.printer_uuid: str = None
        self.started: str = None
        self.status: str = None
        self.time_elapsed: str = None
        self.time_total: str = None
        self.uuid: str = None
        super().__init__(**kwargs)
        self.printers = [CloudClusterPrinterConfiguration(**c) if isinstance(c, dict) else c
                         for c in self.configuration]
        self.printers = [CloudClusterPrintJobConstraint(**p) if isinstance(p, dict) else p
                         for p in self.constraints]


class CloudClusterStatus(BaseModel):
    def __init__(self, **kwargs):
        self.printers: List[CloudClusterPrinter] = []
        self.print_jobs: List[CloudClusterPrintJob] = []
        super().__init__(**kwargs)

        self.printers = [CloudClusterPrinter(**p) if isinstance(p, dict) else p for p in self.printers]
        self.print_jobs = [CloudClusterPrintJob(**j) if isinstance(j, dict) else j for j in self.print_jobs]


class JobUploadRequest(BaseModel):
    def __init__(self, **kwargs):
        self.file_size: int = None
        self.job_name: str = None
        super().__init__(**kwargs)


class JobUploadResponse(BaseModel):
    def __init__(self, **kwargs):
        self.download_url: str = None
        self.job_id: str = None
        self.job_name: str = None
        self.slicing_details: str = None
        self.status: str = None
        self.upload_url: str = None
        super().__init__(**kwargs)


class PrintResponse(BaseModel):
    def __init__(self, **kwargs):
        self.cluster_job_id: str = None
        self.job_id: str = None
        self.status: str = None
        super().__init__(**kwargs)
