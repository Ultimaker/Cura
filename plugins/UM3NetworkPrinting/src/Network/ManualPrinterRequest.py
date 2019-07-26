from typing import Optional, Callable


## Represents a request for adding a manual printer. It has the following fields:
#  - address: The string of the (IP) address of the manual printer
#  - callback: (Optional) Once the HTTP request to the printer to get printer information is done, whether successful
#              or not, this callback will be invoked to notify about the result. The callback must have a signature of
#                  func(success: bool, address: str) -> None
class ManualPrinterRequest:

    def __init__(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        self.address = address
        self.callback = callback
