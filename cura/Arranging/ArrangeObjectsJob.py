# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List

from UM.Application import Application
from UM.Job import Job
from UM.Logger import Logger
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from cura.Arranging.GridArrange import GridArrange
from cura.Arranging.Nest2DArrange import Nest2DArrange

i18n_catalog = i18nCatalog("cura")


class ArrangeObjectsJob(Job):
    def __init__(self, nodes: List[SceneNode], fixed_nodes: List[SceneNode], min_offset = 8,
                *, grid_arrange: bool = False) -> None:
        super().__init__()
        self._nodes = nodes
        self._fixed_nodes = fixed_nodes
        self._min_offset = min_offset
        self._grid_arrange = grid_arrange

    def run(self):
        found_solution_for_all = False
        status_message = Message(i18n_catalog.i18nc("@info:status", "Finding new location for objects"),
                                 lifetime = 0,
                                 dismissable = False,
                                 progress = 0,
                                 title = i18n_catalog.i18nc("@info:title", "Finding Location"))
        status_message.show()

        if self._grid_arrange:
            arranger = GridArrange(self._nodes, Application.getInstance().getBuildVolume(), self._fixed_nodes)
        else:
            arranger = Nest2DArrange(self._nodes, Application.getInstance().getBuildVolume(), self._fixed_nodes,
                                     factor=1000)

        found_solution_for_all = False
        try:
            found_solution_for_all = arranger.arrange()
        except:  # If the thread crashes, the message should still close
            Logger.logException("e",
                                "Unable to arrange the objects on the buildplate. The arrange algorithm has crashed.")

        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(
                    i18n_catalog.i18nc("@info:status",
                                       "Unable to find a location within the build volume for all objects"),
                    title = i18n_catalog.i18nc("@info:title", "Can't Find Location"),
                    message_type = Message.MessageType.ERROR)
            no_full_solution_message.show()

        self.finished.emit(self)
