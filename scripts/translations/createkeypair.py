#!/usr/bin/env python3

import argparse
from typing import Optional
import sys

from UM.Trust import TrustBasics

# Default arguments, if arguments to the script are omitted, these values are used:
DEFAULT_PRIVATE_KEY_PATH = "./private_key.pem"
DEFAULT_PUBLIC_KEY_PATH = "./public_key.pem"
DEFAULT_PASSWORD = ""


def createAndStoreNewKeyPair(private_filename: str, public_filename: str, optional_password: Optional[str]) -> None:
    """Creates a new public and private key, and saves them to the provided filenames.

    See also 'Trust.py' in the main library and the related scripts; 'signfile.py', 'signfolder.py' in this folder.

    :param private_filename: Filename to save the private key to.
    :param public_filename: Filename to save the public key to.
    :param optional_password: Private keys can have a password (or not).
    """

    password = None if optional_password == "" else optional_password
    private_key, public_key = TrustBasics.generateNewKeyPair()
    TrustBasics.saveKeyPair(private_key, private_filename, public_filename, password)


def mainfunc():
    """Arguments:

    `-k <filename>` or `--private <filename>` will store the generated private key to <filename>
    `-p <filename>` or `--public <filename>` will store the generated public key to <filename>
    `-w <password>` or `--password <password>` will give the private key a password (none if omitted, which is default)
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--private", type = str, default = DEFAULT_PRIVATE_KEY_PATH)
    parser.add_argument("-p", "--public", type = str, default = DEFAULT_PUBLIC_KEY_PATH)
    parser.add_argument("-w", "--password", type = str, default = DEFAULT_PASSWORD)
    args = parser.parse_args()
    createAndStoreNewKeyPair(args.private, args.public, args.password)


if __name__ == "__main__":
    sys.exit(mainfunc())
