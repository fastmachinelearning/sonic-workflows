#!/bin/bash

ACCESS=ssh
CORES=8
BATCH=""
CMSSWVER=CMSSW_13_3_X_2023-10-13-1100
CMSSWVERS=(
CMSSW_13_3_X_2023-10-13-1100 \
CMSSW_13_3_0_pre4 \
)

usage(){
	EXIT=$1

	echo "setup.sh [options]"
	echo ""
	echo "-B                  configure some settings for checkout within batch setups (default = ${BATCH})"
	echo "-C                  choose CMSSW version (default = ${CMSSWVER}, choices=${CMSSWVERS[@]})"
	echo "-a [protocol]       use protocol to clone (default = ${ACCESS}, alternative = https)"
	echo "-j [cores]          run CMSSW compilation on # cores (default = ${CORES})"
	echo "-h                  display this message and exit"

	exit $EXIT
}

# process options
while getopts "BC:a:j:h" opt; do
	case "$opt" in
	B) BATCH=--upstream-only
	;;
	C) CMSSWVER=$OPTARG
	;;
	a) ACCESS=$OPTARG
	;;
	j) CORES=$OPTARG
	;;
	h) usage 0
	;;
	esac
done

# check options
if [ "$ACCESS" = "ssh" ]; then
	ACCESS_GITHUB=git@github.com:
	ACCESS_GITLAB=ssh://git@gitlab.cern.ch:7999/
	ACCESS_CMSSW=--ssh
elif [ "$ACCESS" = "https" ]; then
	ACCESS_GITHUB=https://github.com/
	ACCESS_GITLAB=https://gitlab.cern.ch/
	ACCESS_CMSSW=--https
else
	usage 1
fi

# check CMSSW version
if [[ ! " ${CMSSWVERS[@]} " =~ " $CMSSWVER " ]]; then
	echo "Unsupported CMSSW version: $CMSSWVER"
	usage 1
fi

# OS check: try redhat-release first to handle Singularity case
# kept in view of handling post-SL7 OS
declare -A OS_PREFIX
OS_PREFIX[7]=slc7
OS_PREFIX[8]=el8
POSSIBLE_VERSIONS=( 7 8 )
if [[ -f "/etc/redhat-release" ]]; then
	VERSION_TMP=`awk -F'[ .]' '{print $4}' "/etc/redhat-release"`
	if [[ "${POSSIBLE_VERSIONS[@]} " =~ "${VERSION_TMP}" ]]; then
		SLC_VERSION="${OS_PREFIX[${VERSION_TMP}]}"
	else
		echo "WARNING::Unknown SLC version. Defaulting to SLC7."
		SLC_VERSION="slc7"
	fi
else
	for POSVER in ${POSSIBLE_VERSIONS[@]}; do
		if [[ `uname -r` == *"el${POSVER}"* ]]; then
			SLC_VERSION="${OS_PREFIX[$POSVER]}"
			break
		fi
	done
	if [ -z "$SLC_VERSION" ]; then
		echo "WARNING::Unknown SLC version. Defaulting to SLC7."
		SLC_VERSION="slc7"
	fi
fi

declare -A GCC_VERSION
GCC_VERSION[slc7]=gcc11
GCC_VERSION[el8]=gcc12
export SCRAM_ARCH=${SLC_VERSION}_amd64_${GCC_VERSION[$SLC_VERSION]}
scram project $CMSSWVER
cd ${CMSSWVER}/src
eval `scramv1 runtime -sh`
git cms-init $ACCESS_CMSSW $BATCH
#git cms-addpkg HeterogeneousCore/SonicTriton
#git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-models HeterogeneousCore/SonicTriton/data
git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-workflows -b CMSSW_13_3_X
scram b -j ${CORES}
