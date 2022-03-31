#!/bin/bash -ex

TESTNAME=""
NTHREADS=0
NJOBS=0
SONIC=0
ARGS=""
PORTBASE=8000
INFILE="file:store_relval_CMSSW_12_0_0_pre4_RelValTTbar_14TeV_GEN-SIM-RECO_PU_120X_mcRun3_2021_realistic_v2-v1_00000_63718711-dca3-488a-b6dc-6989dfa81707.root"
NCPU=$(cat /proc/cpuinfo | grep processor | wc -l)
# check for hyperthreading
if grep -q " ht " /proc/cpuinfo; then
	NCPU=$((NCPU/2))
fi

# to kill busy processes
declare -A PIDS
kill_busy(){
	# disable errexit because cmsTriton stop may fail if server didn't start properly
	set +e

	for PID in ${PIDS[@]}; do
		kill $PID >& /dev/null
		wait $PID || true >& /dev/null
	done

	# manually stop CPU server
	for ((nj=0;nj<$NJOBS;nj++)); do
		if [ "$SONIC" -eq 1 ]; then
			cmsTriton -v -c -n triton_server_instance_${nj} stop
		fi
	done
}
trap "kill_busy" EXIT

while getopts "t:n:j:a:s" opt; do
	case "$opt" in
		t) TESTNAME=$OPTARG
		;;
		n) NTHREADS="$OPTARG"
		;;
		j) NJOBS="$OPTARG"
		;;
		a) ARGS="$OPTARG"
		;;
		s) SONIC=1
		;;
	esac
done

echo "NCPU: $NCPU"

if [ -z "$TESTNAME" ]; then
	echo "Must specify -t"
	exit 1
fi

if [ "$NTHREADS" -eq 0 ]; then
	echo "Must specify -n"
	exit 1
fi

if [ "$NJOBS" -eq 0 ]; then
	echo "Must specify -n"
	exit 1
fi

# do some integer math
NTOTAL=$((NTHREADS*NJOBS))
NLEFT=$((NCPU-NTOTAL))
if [ $NLEFT -lt 0 ]; then
	echo "Requested $NTOTAL cores but only $NCPU available"
	exit 1
fi

# input duplication math: throughput of 1 ev/s on 1 thread, input file has 1K events, run for 30 min = 1800 sec, assume perfect scaling w/ nthreads -> 2 files per thread
DUP=$((2*NTHREADS))

# use leftover CPUs
for ((extra=0;extra<$NLEFT;extra++)); do
	yes >& /dev/null &
	PIDS[$extra]=$!
done

mkdir $TESTNAME && cd $TESTNAME && ln -s ../*.py . && ln -s ../*.root .
declare -A JOBS
for ((nj=0;nj<$NJOBS;nj++)); do
	# manually start CPU server
	if [ "$SONIC" -eq 1 ]; then
		cmsTriton -P $((PORTBASE+3*nj)) -v -c -n triton_server_instance_${nj} -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/particlenet_AK8_MassRegression/config.pbtxt -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/deepmet/config.pbtxt -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/particlenet_AK8_MD-2prong/config.pbtxt -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/particlenet_AK4/config.pbtxt -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/deeptau_nosplit/config.pbtxt -m $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models/particlenet/config.pbtxt start
	fi
	# run job
	JOBNAME=job${nj}_th${NTHREADS}
	cmsRun run.py config=step4_PAT_Run3 tmi=1 device=cpu sonic=$SONIC threads=$NTHREADS input=$INFILE output="file:out_${JOBNAME}.root" duplicate=$DUP address=0.0.0.0 port=$((PORTBASE+3*nj+1)) fallback=0 $ARGS >& log_${JOBNAME}.log &
	JOBS[$nj]=$!
done

# wait for all cmsRun processes
for JOB in ${JOBS[@]}; do
	wait $JOB || true >& /dev/null
done
