# Copyright (c) 2021 Ultimaker B.V.

from typing import Optional, Dict, Any

from .PaginationLinks import PaginationLinks
from .PaginationMetadata import PaginationMetadata
from .ResponseMeta import ResponseMeta


class PaginationManager:

    def __init__(self, limit: int) -> None:
        self.limit = limit  # The limit of items per page
        self.meta = None  # type: Optional[ResponseMeta]  # The metadata of the paginated response
        self.links = None  # type: Optional[PaginationLinks]  # The pagination-related links

    def setResponseMeta(self, meta: Optional[Dict[str, Any]]) -> None:
        self.meta = None

        if meta:
            page = None
            if "page" in meta:
                page = PaginationMetadata(**meta["page"])
            self.meta = ResponseMeta(page)

    def setLinks(self, links: Optional[Dict[str, str]]) -> None:
        self.links = PaginationLinks(**links) if links else None

    def setLimit(self, new_limit: int) -> None:
        """
        Sets the limit of items per page.

        :param new_limit: The new limit of items per page
        """
        self.limit = new_limit
        self.reset()

    def reset(self) -> None:
        """
        Sets the metadata and links to None.
        """
        self.meta = None
        self.links = None
