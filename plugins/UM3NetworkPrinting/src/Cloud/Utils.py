from typing import TypeVar, Dict, Tuple, List

T = TypeVar("T")
U = TypeVar("U")


def findChanges(previous: Dict[str, T], received: Dict[str, U]) -> Tuple[List[T], List[U], List[Tuple[T, U]]]:
    previous_ids = set(previous)
    received_ids = set(received)

    removed_ids = previous_ids.difference(received_ids)
    new_ids = received_ids.difference(previous_ids)
    updated_ids = received_ids.intersection(previous_ids)

    removed = [previous[removed_id] for removed_id in removed_ids]
    added = [received[new_id] for new_id in new_ids]
    updated = [(previous[updated_id], received[updated_id]) for updated_id in updated_ids]

    return removed, added, updated
