#!/usr/bin/env bash
cd build
ctest -j4 --output-on-failure -T Test
