#!/bin/bash

threads=24

curdir=`pwd`

rev=13039

export PATH=${curdir}/tools/mcrl2-${rev}/install/bin:$PATH
which mcrl22lps

python run.py -p -j${threads} -vvv run.yaml >& run_paper.log
