from datetime import datetime, timedelta
from typing import TypeVar, Dict, Tuple, List

from UM import i18nCatalog

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


def formatTimeCompleted(seconds_remaining: int) -> str:
    completed = datetime.now() + timedelta(seconds=seconds_remaining)
    return "{hour:02d}:{minute:02d}".format(hour = completed.hour, minute = completed.minute)


def formatDateCompleted(seconds_remaining: int) -> str:
    now = datetime.now()
    completed = now + timedelta(seconds=seconds_remaining)
    days = (completed.date() - now.date()).days
    i18n = i18nCatalog("cura")

    # If finishing date is more than 7 days out, using "Mon Dec 3 at HH:MM" format
    if days >= 7:
        return completed.strftime("%a %b ") + "{day}".format(day = completed.day)
    # If finishing date is within the next week, use "Monday at HH:MM" format
    elif days >= 2:
        return completed.strftime("%a")
    # If finishing tomorrow, use "tomorrow at HH:MM" format
    elif days >= 1:
        return i18n.i18nc("@info:status", "tomorrow")
    # If finishing today, use "today at HH:MM" format
    else:
        return i18n.i18nc("@info:status", "today")
