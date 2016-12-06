#!/bin/bash

threads=24

curdir=`pwd`

rev=14379

if [[ $OSTYPE == darwin* ]]; then
  echo "Running script on a MAC"
  export PATH=${curdir}/tools/mcrl2-${rev}/install/mCRL2.app/Contents/bin:$PATH
else
  echo "Running script on $OSTYPE"
  export PATH=${curdir}/tools/mcrl2-${rev}/install/bin:$PATH
fi
which mcrl22lps

python run.py -p -j${threads} -vvv run_14379.yaml >& run_14379.log
