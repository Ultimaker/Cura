from abc import ABC

"""
TODO
"""
class CommandIterator(ABC):
    def __init__(self):
        self.pointer = 0
    
    def get_pointer(self) -> int:
        return self.pointer

    def get_text(self, pointer: int) -> str:
        return ...


"""
TODO
"""
class SweepCommandIterator(ABC):
    def __init__(self):
        self.pointer = 0
    
    def get_pointer(self) -> int:
        return self.pointer

    def get_text(self, pointer: int) -> str:
        self.pointer += 1
        return "G0 X10" if self.get_pointer() % 2 == 0 else "G0 X-10"