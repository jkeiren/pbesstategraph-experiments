pbesstategraph-experiments
==========================
Repository containing the examples and scripts for the experiments belonging to
the paper "Improved Static Analysis of Parameterised Boolean Equation Systems
using Control Flow Reconstruction"

Usage
-----

Experiments should be run iff the mcrl2 binaries are in the PATH. Then invoke

> python run.py [-v[v[v[...]]]] [-jN] [yamlfile]

to run the experiments. More v's means more verbose. For N a positive
integer, N jobs are started if -jN is given. If a filename is given on
the command line, results are put in that file. The file is not 
overwritten: if it already exists, then the experiments for which it
contains results are skipped.

Results
-------

The full results reported in the SPIN 2013 submission J.J.A. Keiren, J.W. Wesselink, T.A.C. Willemse.
"Improved Static Analysis of Parameterised Boolean Equation Systems using Control Flow Reconstruction" can
be found in `results/20130316/run.yaml`, those results were obtained using r11682 of the mCRL2 toolset.
