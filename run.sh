#!/bin/bash

threads=8

curdir=`pwd`

rev=14614

export PATH=${curdir}/tools/mcrl2-${rev}/install/bin:$PATH
which mcrl22lps

#python run.py -d -j${threads} -vvv run_debug.yaml >& run_debug.log
#python run.py -p -j${threads} -vvv run_paper.yaml >& run_paper.log
python run.py -p -j${threads} -vvv run_paper_constelm-c.yaml >& run_paper_constelm-c.log
