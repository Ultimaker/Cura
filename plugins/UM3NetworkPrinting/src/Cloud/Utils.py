from typing import TypeVar, Dict, Tuple, List

T = TypeVar("T")
U = TypeVar("U")


## Splits the given dictionaries into three lists (in a tuple):
#       - `removed`: Items that were in the first argument but removed in the second one.
#       - `added`: Items that were not in the first argument but were included in the second one.
#       - `updated`: Items that were in both dictionaries. Both values are given in a tuple.
#  \param previous: The previous items
#  \param received: The received items
#  \return: The tuple (removed, added, updated) as explained above.
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
