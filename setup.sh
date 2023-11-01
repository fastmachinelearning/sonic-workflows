#!/bin/bash

ACCESS=ssh
CORES=8
BATCH=""
CMSSWVER=CMSSW_13_3_0_pre4
CMSSWVERS=(
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

export SCRAM_ARCH=${SLC_VERSION}_amd64_gcc12
scram project $CMSSWVER
cd ${CMSSWVER}/src
eval `scramv1 runtime -sh`
git cms-init $ACCESS_CMSSW $BATCH
git cms-merge-topic fastmachinelearning:CMSSW_13_3_0_pre4_PTTC
git cms-merge-topic wpmccormack:CMSSW_13_3_0_pre4_new_PN_and_HiggsIN
git cms-merge-topic yongbinfeng:CMSSW_13_3_0_pre3_DeepTauIdSONIC
git cms-addpkg RecoBTag/Combined
mkdir RecoTauTag/TrainingFiles
git clone ${ACCESS_GITHUB}wpmccormack/RecoBTag-Combined.git -b onnx_patch_with_newPN_HiggsIN RecoBTag/Combined/data
git clone ${ACCESS_GITHUB}yongbinfeng/RecoTauTag-TrainingFiles.git -b DeepTau2018v2p5_SONIC RecoTauTag/TrainingFiles/data
git clone ${ACCESS_GITHUB}fastmachinelearning/sonic-workflows -b CMSSW_13_3_X
cd Configuration/ProcessModifiers/python/
rm allSonicTriton_cff.py
wget https://raw.githubusercontent.com/cms-tau-pog/cmssw/CMSSW_13_3_X_tau-pog_deepTauv2p5_SONIC/Configuration/ProcessModifiers/python/allSonicTriton_cff.py
cd ${CMSSW_BASE}/src
cd RecoTauTag/RecoTau/python/tools/
rm runTauIdMVA.py
wget https://raw.githubusercontent.com/cms-tau-pog/cmssw/CMSSW_13_3_X_tau-pog_deepTauv2p5_SONIC/RecoTauTag/RecoTau/python/tools/runTauIdMVA.py
cd ${CMSSW_BASE}/src
scram b -j ${CORES}
