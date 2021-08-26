#!/bin/bash

ACCESS=ssh
CORES=8
BATCH=""
CMSSWVER=CMSSW_12_0_0_pre5
CMSSWVERS=(
CMSSW_12_0_0_pre4 \
CMSSW_12_0_0_pre5 \
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

export SCRAM_ARCH=slc7_amd64_gcc900
scram project $CMSSWVER
cd ${CMSSWVER}/src
eval `scramv1 runtime -sh`
git cms-init $ACCESS_CMSSW $BATCH
git cms-checkout-topic $ACCESS_CMSSW fastmachinelearning:${CMSSWVER}_SONIC
git cms-addpkg HeterogeneousCore/SonicTriton
git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-models HeterogeneousCore/SonicTriton/data
git cms-addpkg RecoBTag/Combined
git clone ${ACCESS_GITHUB}fastmachinelearning/RecoBTag-Combined -b add_noragged RecoBTag/Combined/data
git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-workflows
scram b -j ${CORES}
