#!/bin/bash

curdir=`pwd`

newrev=12622
oldrev=11707

for rev in ${newrev} ${oldrev}; do

  mkdir -p ${curdir}/tools/mcrl2-${rev}
  cd ${curdir}/tools/mcrl2-${rev}
  svn checkout https://svn.win.tue.nl/repos/MCRL2/trunk -r${rev} src
  if [[ "${rev}" = "${oldrev}" ]]; then
    cd src
    patch -p0 < ${curdir}/tools/build_r11707_osx_mavericks.patch
    cd ..
  fi
  mkdir build
  cd build
  cmake ../src -DCMAKE_BUILD_TYPE=Release -DMCRL2_ENABLE_EXPERIMENTAL=ON -DMCRL2_ENABLE_GUI_TOOLS=OFF -DCMAKE_INSTALL_PREFIX=${curdir}/tools/mcrl2-${rev}/install
  make -j install
  
done

cd ${curdir}/tools/mcrl2-${oldrev}/install/bin
for b in `ls`; do
  if [[ "${b}" != "mcrl2compilerewriter" ]]; then
    mv ${b} ${b}old
  fi
done

cd ${curdir}