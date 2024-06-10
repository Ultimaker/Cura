import requests
import argparse


def get_wheel_file_hashes(package_name, package_version, python_version):
    response = requests.get(f'https://pypi.org/pypi/{package_name}/json')
    data = response.json()

    hashes = []
    for file_info in data['releases'][package_version]:
        if python_version is None or file_info['python_version'] == python_version:
            hashes.append(file_info['digests']['sha256'])

    return hashes

    #wheel_files = [file_info['url'] for file_info in data['releases'].values() for file_info in file_info if file_info['filename'].endswith('.whl')]
    
    #hashes = {}
    #for wheel_url in wheel_files:
        #file_name = wheel_url.split('/')[-1]
        #download_file(wheel_url, file_name)
        #file_hash = compute_hash(file_name, hash_algorithm)
        #hashes[file_name] = file_hash
    
    #return hashes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Displays the hashes files to be inserted in a requirements.txt')
    parser.add_argument('package', type = str, help = 'Package name')
    parser.add_argument('version', type = str, help = 'Package version')
    parser.add_argument('--python-version', type = str, help = 'Python specific version, e.g. cp312 for Python 3.12', required=False)
    args = parser.parse_args()

    hashes = get_wheel_file_hashes(args.package, args.version, args.python_version)
    print(f"{args.package}=={args.version} \\")
    hashes = [f"    --hash=sha256:{hash}" for hash in hashes]
    print(" \\\n".join(hashes))
