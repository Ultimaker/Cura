# Copyright (c) 2021 Ultimaker B.V.

from typing import Optional


class PaginationMetadata:
    """Class representing the metadata related to pagination."""

    def __init__(self,
                 total_count: Optional[int] = None,
                 total_pages: Optional[int] = None,
                 **kwargs) -> None:
        """
        Creates a new digital factory project response object
        :param total_count: The total count of items.
        :param total_pages: The total number of pages when pagination is applied.
        :param kwargs:
        """

        self.total_count = total_count
        self.total_pages = total_pages
        self.__dict__.update(kwargs)

    def __str__(self) -> str:
        return "PaginationMetadata | Total Count: {}, Total Pages: {}".format(self.total_count, self.total_pages)
