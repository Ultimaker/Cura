# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .AddPrinterPagesModel import AddPrinterPagesModel


class AddPrinterPagesModelWithoutCancel(AddPrinterPagesModel):

    def initialize(self) -> None:
        self._generatePages()
        self.setItems(self._pages)
