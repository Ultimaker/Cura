from abc import ABC, abstractmethod

# Define the abstract base class for the GUI interface
class AbstractUI(ABC):
    @abstractmethod
    def update(self):
        """
        Abstract method: Updates the GUI elements.
        """
        pass