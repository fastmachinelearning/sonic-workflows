#!/bin/bash

ACCESS=ssh
CORES=8
BATCH=""
CMSSWVER=CMSSW_16_0_0_pre4
CMSSWVERS=(
CMSSW_16_0_0_pre4 \
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
OS_PREFIX[9]=el9
POSSIBLE_VERSIONS=( 7 8 9 )
if [[ -f "/etc/redhat-release" ]]; then
	VERSION_TMP=$(grep -o "[0-9]\+\." /etc/redhat-release | head -n1 | cut -d'.' -f1)
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

export SCRAM_ARCH=${SLC_VERSION}_amd64_gcc12
scram project $CMSSWVER
cd ${CMSSWVER}/src
eval `scramv1 runtime -sh`
git cms-init $ACCESS_CMSSW $BATCH
git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-workflows -b CMSSW_16_0_X
git clone ${ACCESS_GITHUB}kpedro88/CondorProduction Condor/Production
cd ${CMSSW_BASE}/src
scram b -j ${CORES}
$CMSSW_BASE/src/Condor/Production/scripts/postInstall.sh -b $CMSSW_BASE/src/sonic-workflows/batch -c -p
