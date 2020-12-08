# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime, timezone
from typing import TypeVar, Dict, List, Any, Type, Union


# Type variable used in the parse methods below, which should be a subclass of BaseModel.
T = TypeVar("T", bound="BaseModel")


class BaseModel:

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.validate()

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        pass

    def __eq__(self, other):
        """Checks whether the two models are equal.

        :param other: The other model.
        :return: True if they are equal, False if they are different.
        """
        return type(self) == type(other) and self.toDict() == other.toDict()

    def __ne__(self, other) -> bool:
        """Checks whether the two models are different.

        :param other: The other model.
        :return: True if they are different, False if they are the same.
        """
        return type(self) != type(other) or self.toDict() != other.toDict()

    def toDict(self) -> Dict[str, Any]:
        """Converts the model into a serializable dictionary"""

        return self.__dict__

    @staticmethod
    def parseModel(model_class: Type[T], values: Union[T, Dict[str, Any]]) -> T:
        """Parses a single model.

        :param model_class: The model class.
        :param values: The value of the model, which is usually a dictionary, but may also be already parsed.
        :return: An instance of the model_class given.
        """
        if isinstance(values, dict):
            return model_class(**values)
        return values

    @classmethod
    def parseModels(cls, model_class: Type[T], values: List[Union[T, Dict[str, Any]]]) -> List[T]:
        """Parses a list of models.

        :param model_class: The model class.
        :param values: The value of the list. Each value is usually a dictionary, but may also be already parsed.
        :return: A list of instances of the model_class given.
        """
        return [cls.parseModel(model_class, value) for value in values]

    @staticmethod
    def parseDate(date: Union[str, datetime]) -> datetime:
        """Parses the given date string.

        :param date: The date to parse.
        :return: The parsed date.
        """
        if isinstance(date, datetime):
            return date
        return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
