import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from DriveFilter import DriveFilter
import pytest


def test_defaultFilterAllowAll():
    filter = DriveFilter()
    assert filter.filterByValue({}) == {}
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3"}) == {"1": "Test1", "2": "Test2", "3": "Test3"}

def test_whiteListRegexSimpleContains():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "WhitelistRegex",
            "pattern": "Test",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Invalid", "5": "Test"}) == {"1": "Test1", "2": "Test2", "3": "Test3", "5": "Test"}

def test_whiteListRegexPattern():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "WhitelistRegex",
            "pattern": r"Test\d+",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Invalid", "5": "Test"}) == {"1": "Test1", "2": "Test2", "3": "Test3"}

def test_blackListRegexSimpleContains():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "BlacklistRegex",
            "pattern": "Test",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Valid", "5": "Test"}) == {"4": "Valid"}

def test_blackListRegexPattern():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "BlacklistRegex",
            "pattern": r"Test\d+",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Valid", "5": "Test"}) == {"4": "Valid", "5": "Test"}

def test_multipleWhiteListRegexContains():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "WhitelistRegex",
            "pattern": "Test",
        },
        {
            "type": "WhitelistRegex",
            "pattern": "Valid",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Valid", "5": "Test"}) == {"1": "Test1", "2": "Test2", "3": "Test3", "4": "Valid", "5": "Test"}

def test_whitelistBlacklistRegexContains():
    filter = DriveFilter()
    filter.reload([
        {
            "type": "WhitelistRegex",
            "pattern": "Test",
        },
        {
            "type": "BlacklistRegex",
            "pattern": "Test2",
        },
    ])
    assert filter.filterByValue({"1": "Test1", "2": "Test2", "3": "Test3", "4": "Test"}) == {"1": "Test1", "3": "Test3", "4": "Test"}
