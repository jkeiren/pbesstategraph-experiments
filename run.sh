#!/bin/bash

threads=24

curdir=`pwd`

newrev=12659
oldrev=12522

export PATH=${curdir}/tools/mcrl2-${newrev}/install/bin:${curdir}/tools/mcrl2-${oldrev}/install/bin:$PATH
which mcrl22lps
which mcrl22lpsold

python run.py -p -j${threads} -vvv run_markings.yaml >& run_markings.log
