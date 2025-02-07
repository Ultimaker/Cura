import requests
import argparse
from pathlib import Path

def get_package_wheel_hashes(package, version):
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    data = requests.get(url).json()

    print(f"    {package}:")
    print(f"      version: \"{version}\"")
    print(f"      hashes:")

    for url in data["urls"]:
        print(f"        - sha256:{url['digests']['sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display the hashes of the wheel files to be inserted in pip_requirements")
    parser.add_argument("package", type=Path, help="Name of the target package")
    parser.add_argument("version", type=Path, help="Version of the target package")
    args = parser.parse_args()
    get_package_wheel_hashes(args.package, args.version)
