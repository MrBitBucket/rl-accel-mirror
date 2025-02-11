#!/bin/bash
set -e

#change to suit your python versions/locations
BUILDPYTHON="${BUILDPYTHON:-313}"
PYTHONS="${PYTHONS:-39 310 311 312 313 314}"

uname -a
mkdir -p tmp
cd tmp
DOWNLOAD="${DOWNLOAD:-1}"
if [ "$DOWNLOAD" = "1" ]; then
	rm -rf ./rl-accel-mirror
	git clone https://github.com/MrBitBucket/rl-accel-mirror
else
	[ ! -d "rl-accel-mirror" ] && echo "!!!!! cannot find existing rl-accel-mirror" && exit 1
fi

TESTPY="${TESTPY:-testcs.py}"
cp ../runner.sh ../${TESTPY} rl-accel-mirror/tests
cd rl-accel-mirror
rm -rf ./build

NL=$'\n'
DOTPYS=""
for i in ${PYTHONS}; do
	py=~/bin/python"$i"
	[ ! -x "$py" ] && echo "!!!!! '$py' is not executable" && exit 1
	pyv="$(${py} -c'import sys;print("".join(map(str,sys.version_info[:2])))')"
	pyd=".py$pyv"
	DOTPYS="$DOTPYS $pyd"
	vm=""
	if [ ! -d .py${pyv} ]; then
		$py -mvenv .py${pyv}
		vm="created ${pyd} $(${pyd}/bin/python -c'import sys;print(sys.version)')"
	fi
	if [ "$pyv" = "$BUILDPYTHON" ]; then
		(
		. ${pyd}/bin/activate
		${pyd}/bin/pip install wheel setuptools &>/dev/null
		${pyd}/bin/python setup.py build_ext
   		rm -f _rl_accel.abi3.so
		case ${pyv} in
			(37|38|39)
				ln -s build/lib.linux-x86_64-3.${pyv#3}/_rl_accel.abi3.so .
				;;
			(*)
	   			ln -s build/lib.linux-x86_64-cpython-${pyv}/_rl_accel.abi3.so .
				;;
		esac
		)
		bpy="made _rl_accel extension with python${pyv}"
		[ -n vm ] && vm="$vm${NL}$bpy" || vm="$bpy"
		bpy="$pyv"
	fi
	if [ -n "$vm" ];then
		echo
		echo "############################################################"
		echo "${vm}"
		echo "############################################################"
	fi
done

for pyd in $DOTPYS; do
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
	${pyd}/bin/python -u tests/${TESTPY}
	)
done
