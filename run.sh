#!/bin/bash

threads=16

curdir=`pwd`

newrev=12622
oldrev=11707

export PATH=${curdir}/tools/mcrl2-${newrev}/install/bin:${curdir}/tools/mcrl2-${oldrev}/install/bin:$PATH
which mcrl22lps
which mcrl22lpsold

python run.py -dn -j${threads} -vvv run.yaml >& run.log