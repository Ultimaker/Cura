# Copyright (c) 2021 Ultimaker B.V.

from typing import Optional


class PaginationLinks:
    """Model containing pagination links."""

    def __init__(self,
                 first: Optional[str] = None,
                 last: Optional[str] = None,
                 next: Optional[str] = None,
                 prev: Optional[str] = None,
                 **kwargs) -> None:
        """
        Creates a new digital factory project response object
        :param first: The URL for the first page.
        :param last: The URL for the last page.
        :param next: The URL for the next page.
        :param prev: The URL for the prev page.
        :param kwargs:
        """

        self.first_page = first
        self.last_page = last
        self.next_page = next
        self.prev_page = prev

    def __str__(self) -> str:
        return "Pagination Links | First: {}, Last: {}, Next: {}, Prev: {}".format(self.first_page, self.last_page, self.next_page, self.prev_page)
