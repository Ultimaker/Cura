# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime, timedelta

from UM import i18nCatalog


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
