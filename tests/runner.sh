#!/bin/bash
set -e

#change to suit your python versions/locations
PYTHONS=(~/bin/python39 ~/bin/python314)

uname -a
mkdir -p tmp
cd tmp
rm -rf ./rl-accel-mirror
git clone https://github.com/MrBitBucket/rl-accel-mirror

cd rl-accel-mirror

for py in ${PYTHONS[@]}; do
	pyv="$(${py} -c'import sys;print("".join(map(str,sys.version_info[:2])))')"
	pyd=".py$pyv"
	$py -mvenv .py${pyv}
	(
	. ${pyd}/bin/activate
	${pyd}/bin/pip install wheel setuptools
	${pyd}/bin/python setup.py build_ext
	)
	echo
	echo "############################################################"
	echo "created ${pyd} and made _rl_accel extension with python${pyv}"
	echo "############################################################"
done

for bpy in 39 314; do
   rm -f _rl_accel.abi3.so
   if [ ${bpy} == 39 ]; then
	   ln -s build/lib.linux-x86_64-3.9/_rl_accel.abi3.so .
	else
	   ln -s build/lib.linux-x86_64-cpython-314/_rl_accel.abi3.so .
	fi
	for pyv in 39 314; do
		pyd=".py$pyv"
		(
		export PYTHONPATH="$(pwd)"
		. ${pyd}/bin/activate
		echo
		echo "#############################################################"
		echo "extension built with $bpy running tests/testrc.py with python$pyv"
		echo "_rl_accel.abi3.so-->$(readlink _rl_accel.abi3.so)"
		echo "$(${pyd}/bin/python -c'import sys;print(sys.version)')"
		echo "#############################################################"
		${pyd}/bin/python tests/testrc.py
		)
	done
done
