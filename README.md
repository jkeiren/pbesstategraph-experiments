pbesstategraph-experiments
==========================
Repository containing the examples and scripts for the experiments belonging to
the paper "Liveness Analysis for Parameterised Boolean Equation Systems".

Usage
-----

Experiments should be run iff the mcrl2 binaries are in the PATH. Then invoke

    python run.py [-v[v[v[...]]]] [-jN] [-dpn] [yamlfile]

to run the experiments. More v's means more verbose. For `N` a positive
integer, `N` jobs are started if `-jN` is given. If a filename is given on
the command line, results are put in that file. The file is not 
overwritten: if it already exists, then the experiments for which it
contains results are skipped.
If the option `-d` is provided than only some small cases are run to debug the scripts. With the optio `-p` only those cases reported in the paper are run. If the option `-n` is provided, no timing or memory limits are imposed.

For convenience, the script `run.sh` is provided that sets the path consistently with the output of `install_prerequisites.sh`, see below. Using that script, the experiments as reported in the paper can be reproduced using

    ./run.sh

Installation
------------

To execute the script make sure that PyYAML is installed. The mCRL2 tools can be installed using:

    ./install_prequisites.sh
    
This installs two versions of the mCRL2 toolset: revisions 12522 and 12637. All binaries from revision 12522 are renamed such that 'old' is appended to their name.

Description
-----------
Two classes of problems are considered in this script: modelchecking problems and equivalence checking problems. The experiment consists of two phases. First, a PBES has to be obtained, and then tranformations are applied to the PBES, and the size of the underlying BES is determined.

### Obtaining a PBES
For each of the instances a number of tools is executed, as described below.

#### Model checking
The code that performs the steps below can be found in `cases/modelchecking/__init__.py`

By default, we produce a `.lps` file from `<case>.mcrl2` using:

    mcrl22lps -nf <case>.mcrl2 <case>.lps

The specifications for which this default is used are:

* Lossy buffer
* ABP
* ABP(BW)
* Hesselink
* SWP
* BRP
* Elevator
* Leader
* Hanoi

For some specifications we first unfold some some data types using `lpsparunfold`, in this case we perform the following sequence of commands:

    mcrl22lps -nf <case>.mcrl2 | lpsparunfold -l -nN -sSORT | lpsconstelm -ct > <case>.lps

where `N` is the number of times parameters of `SORT` need to be unfolded. Exactly which sort is unfolded depends on the case we consider. Sometimes lpsparunfold is repeated for multiple sorts. The tpecifications for which `lpsparunfold` is applied (values of `SORT` and `N` are included) are:

* Onebit (`Frame`, `10`)
* CCP (`Region`, `10`)
* CABP (`Frame`, `10`)
* Par (`Frame`, `10`)
* Lift (Correct) (`Message`, `10`)
* Lift (Incorrect) (`Message`, `10`)
* IEEE1994 (`SIG_TUPLE`, `10`) (`SIGNAL`, `10`), (`LDC`, `10`), (`LDI`, `10`)
* Othello (`Board`, height) (`Row`, width)
* Clobber (`Board`, height) (`Row`, width)
* Snake (`Board`, height) (`Row`, width)
* Hex (`Board`, height) (`Row`, width)
* Domineering (`Board`, height) (`Row`, width)

Finally, for each `.lps` file, and for each property to be considered, we generate a `.pbes` file using the command:

    lps2pbes -f <property>.mcf <case>.lps <case>.<property>.pbes

#### Equivalence checking
The code that performs the steps below can be found in `cases/equivchecking/__init__.py`

In equivalence checking we check each instance for strong bisimilarity, branching bisimilarity, branching similarity and weak bisimilarity. For this we consider two classes of specification.

First we consider all combinations of the following communication protocols:

* Buffer
* ABP
* ABP(BW)
* CABP
* Par
* SWP
* Onebit

The `.lps` for these cases are obtained using:

    mcrl22lps -nf <spec>.mcrl2 | lpsparunfold -l -sFrame -n10 | lpsparunfold -l -sFrameOB -n10 | lpsconstelm > <spec>.lps

Second we consider the equivalence of a specification of Hesselink's register with its implementation.

The `.lps` for this case is obtained using:

    mcrl22lps -nf <spec>.mcrl2 <spec>.lps

Finally, for each pair of LPSs, and each equivalence, the PBES is obtained as follows:

    lpsbisim2pbes -b<equivalence> <spec1>.lps <spec2>.lps <spec1>_<spec2>_<equivalence>.pbes

### Transforming PBES and obtaining results
The common code performing the steps described below can be found in `cases/__init__.py`. This consists of three phases.

#### Preprocessing
First, every PBES is preprocessed using the following commands:

    pbesrewr -psimplify <name>.pbes | pbesrewr -pquantifier-one-point | pbesrewr -psimplify > <simplified>.pbes

#### Reduction

Depending on the reduction, the following commands are performed.

##### Original

    pbesconstelm <simplified>.pbes <reduced>.pbes

##### Parelm

    pbesparelm <simplified>.pbes | pbesconstelm > <reduced>.pbes

##### Stategraph (local algorithm)

    pbesstategraph <simplified>.pbes -l1 | pbesconstelm > <reduced>.pbes

##### Stategraph (global algorithm)

For the global algorithm of stategraph we resort to an older version of the mCRL2 toolset:

    pbesstategraphold <simplified>.pbes -s1 -l0 | pbesconstelm > <reduced>.pbes

#### Instantiation & solving

Finally, the PBES is instantiated and solved, and the statistics about the generated BES are collected. Due to the low performance of instantiation in the current version of mCRL2, we resort to the old version for instantiation (note that this is the least favourable option for our experiments, in terms of the performance improvement that has been obtained).

    pbes2besold -rjittyc <reduced>.pbes <reduced>.bes
    besinfo <reduced>.bes
    pbespgsolve -srecursive <reduced>.bes

Results
-------

The full results reported in the SPIN 2013 submission J.J.A. Keiren, J.W. Wesselink, T.A.C. Willemse.
"Improved Static Analysis of Parameterised Boolean Equation Systems using Control Flow Reconstruction" can
be found in `results/20130316/run.yaml`, those results were obtained using r11682 of the mCRL2 toolset. In this version only the global version of pbesstategraph was available.
