#!/bin/bash

curdir=`pwd`

rev=14614

# First install boost
cd ${curdir}/tools
wget https://sourceforge.net/projects/boost/files/boost/1.63.0/boost_1_63_0.tar.gz/download boost_1_63_0.tar.gz
tar zxvf boost_1_63_0.tar.gz

# Next install mcrl2.
mkdir -p ${curdir}/tools/mcrl2-${rev}
cd ${curdir}/tools/mcrl2-${rev}
svn checkout https://svn.win.tue.nl/repos/MCRL2/trunk -r${rev} src
mkdir build
cd build
cmake ../src -DCMAKE_BUILD_TYPE=Release -DBOOST_ROOT=${curdir}/tools/boost_1_63_0 -DMCRL2_ENABLE_EXPERIMENTAL=ON -DMCRL2_ENABLE_GUI_TOOLS=OFF -DCMAKE_INSTALL_PREFIX=${curdir}/tools/mcrl2-${rev}/install
make -j8 install
  
cd ${curdir}
