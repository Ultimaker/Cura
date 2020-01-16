#!/usr/bin/env bash

# Abort at the first error.
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"

# Make sure that environment variables are set properly
source /opt/rh/devtoolset-7/enable
export PATH="${CURA_BUILD_ENV_PATH}/bin:${PATH}"
export PKG_CONFIG_PATH="${CURA_BUILD_ENV_PATH}/lib/pkgconfig:${PKG_CONFIG_PATH}"

cd "${PROJECT_DIR}"

#
# Clone Uranium and set PYTHONPATH first
#

# Check the branch to use:
#  1. Use the Uranium branch with the branch same if it exists.
#  2. Otherwise, use the default branch name "master"
echo "GITHUB_REF: ${GITHUB_REF}"
echo "GITHUB_HEAD_REF: ${GITHUB_HEAD_REF}"
echo "GITHUB_BASE_REF: ${GITHUB_BASE_REF}"

GIT_REF_NAME_LIST=( "${GITHUB_HEAD_REF}" "${GITHUB_BASE_REF}" "${GITHUB_REF}" "master" )

for git_ref_name in "${GIT_REF_NAME_LIST[@]}"
do
  if [ -z "${git_ref_name}" ]; then
    continue
  fi
  git_ref_name="$(basename "${git_ref_name}")"
  URANIUM_BRANCH="${git_ref_name}"
  output="$(git ls-remote --heads https://github.com/Ultimaker/Uranium.git "${URANIUM_BRANCH}")"
  if [ -n "${output}" ]; then
    echo "Found Uranium branch [${URANIUM_BRANCH}]."
    exit
  else
    echo "Could not find Uranium banch [${URANIUM_BRANCH}], try next."
  fi
done

echo "Using Uranium branch ${URANIUM_BRANCH} ..."
git clone --depth=1 -b "${URANIUM_BRANCH}" https://github.com/Ultimaker/Uranium.git "${PROJECT_DIR}"/Uranium
export PYTHONPATH="${PROJECT_DIR}/Uranium:.:${PYTHONPATH}"

mkdir build
cd build
cmake3 \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_PREFIX_PATH="${CURA_BUILD_ENV_PATH}" \
    -DURANIUM_DIR="${PROJECT_DIR}/Uranium" \
    -DBUILD_TESTS=ON \
    ..
make
ctest3 --output-on-failure -T Test
