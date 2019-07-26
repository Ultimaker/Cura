## Base model that maps kwargs to instance attributes.
class BaseModel:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.validate()

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        pass
