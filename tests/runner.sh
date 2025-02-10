#!/bin/bash
set -e

#change to suit your python versions/locations
PYTHONS=(${EARLYPYTHON:-~/bin/python312} ${LATEPYTHON:-~/bin/python313})

uname -a
mkdir -p tmp
cd tmp
rm -rf ./rl-accel-mirror
git clone https://github.com/MrBitBucket/rl-accel-mirror

TESTPY=testcs.py
cp ../runner.sh ../${TESTPY} rl-accel-mirror/tests
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
	echo "$(python -c'import sys;print(sys.version)')"
	echo "############################################################"
done

for i in .py*; do
	bpy=${i#.py}
   	rm -f _rl_accel.abi3.so
	case ${bpy} in
		(37|38|39)
			ln -s build/lib.linux-x86_64-3.${bpy#3}/_rl_accel.abi3.so .
			;;
		(*)
	   		ln -s build/lib.linux-x86_64-cpython-${bpy}/_rl_accel.abi3.so .
			;;
	esac
	for pyd in .py*; do
		pyv=${pyd#.py}
		(
		export PYTHONPATH="$(pwd)"
		. ${pyd}/bin/activate
		echo
		echo "#############################################################"
		echo "extension built with $bpy running tests/$TESTPY with python$pyv"
		echo "_rl_accel.abi3.so-->$(readlink _rl_accel.abi3.so)"
		echo "$(${pyd}/bin/python -c'import sys;print(sys.version)')"
		echo "#############################################################"
		${pyd}/bin/python tests/${TESTPY}
		)
	done
done
