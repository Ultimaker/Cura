# Copyright (c) 2021 Ultimaker B.V.

from typing import Optional

from .PaginationMetadata import PaginationMetadata


class ResponseMeta:
    """Class representing the metadata included in a Digital Library response (if any)"""

    def __init__(self,
                 page: Optional[PaginationMetadata] = None,
                 **kwargs) -> None:
        """
        Creates a new digital factory project response object
        :param page: Metadata related to pagination
        :param kwargs:
        """

        self.page = page
        self.__dict__.update(kwargs)

    def __str__(self) -> str:
        return "Response Meta | {}".format(self.page)
