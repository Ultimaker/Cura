# Copyright (c) 2022 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

import re
from typing import Dict, List


class DriveFilter:
    def __init__(self):
        """Creates the filter.
        """

        self.filterSteps: List[Dict[str, str]] = []

    def reload(self, filterSteps: List[Dict[str, str]]) -> None:
        """Reloads the filter.

        :param filterSteps: Steps in the filter to apply.
        """

        self.filterSteps = filterSteps

    def passesFilter(self, string: str) -> bool:
        """Returns if a string can pass the filter.
        A string is considered passing the filter if:
        1. It passes at least 1 whitelist condition.
        2. It passes every blacklist condition.

        :param string: String to test.
        :return: Whether the string passes the filter.
        """

        # Iterate through the steps and determine if it passes the whitelist and blacklist.
        stepsPassed = {
            "whitelistregex": 0,
            "blacklistregex": 0,
        }
        stepsAttempted = {
            "whitelistregex": 0,
            "blacklistregex": 0,
        }
        for filterStep in self.filterSteps:
            # Add the base counters.
            stepType = filterStep["type"].lower()
            if stepType not in stepsAttempted:
                stepsAttempted[stepType] = 0
                stepsPassed[stepType] = 0
            stepsAttempted[stepType] += 1

            # Add the passed step.
            stepPassed = False
            if stepType == "whitelistregex":
                regexPattern = re.compile(filterStep["pattern"])
                if regexPattern.search(string) is not None:
                    stepPassed = True
            elif stepType == "blacklistregex":
                regexPattern = re.compile(filterStep["pattern"])
                if regexPattern.search(string) is not None:
                    stepPassed = True
            if stepPassed:
                stepsPassed[stepType] += 1

        # Return if the whitelist and blacklist pass.
        return (stepsAttempted["whitelistregex"] == 0 or stepsPassed["whitelistregex"] > 0) and stepsPassed["blacklistregex"] == 0

    def filterByValue(self, dictionary: Dict[str, str]) -> Dict[str, str]:
        """Filters a dictionary of strings based ont the values.

        :param dictionary: Input keys pairs to filter.
        :return: The key pairs where the value passes the filter.
        """

        # Get the values that pass the filter.
        filteredDictionary = {}
        for key in dictionary.keys():
            if self.passesFilter(dictionary[key]):
                filteredDictionary[key] = dictionary[key]

        # Return the filtered strings.
        return filteredDictionary
