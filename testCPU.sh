#!/bin/bash -ex

TESTNAME=""
NTHREADS=0
NJOBS=0
SONIC=0
DEVICE=cpu
MANUAL=0
ARGS=""
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

	if [ "$MANUAL" -eq 1 ]; then
		cmsTriton -n triton_server_instance stop
	fi
}
trap "kill_busy" EXIT

while getopts "t:n:j:a:sgm" opt; do
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
		g) DEVICE=gpu
		;;
		m) MANUAL=1
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

# set up test area
mkdir $TESTNAME && cd $TESTNAME && ln -s ../*.py . && ln -s ../*.root .

# manually provide a server
if [ "$MANUAL" -eq 1 ]; then
	GPUSERVER=""
	if [ "$DEVICE" == "gpu" ]; then
		GPUSERVER="-g"
	fi
	TRITON_START=$(cmsTriton $GPUSERVER -P -1 -n triton_server_instance -M $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models start)
	echo "$TRITON_START"
	TRITON_PORT=$(echo "$TRITON_START" | grep -F "CMS_TRITON_GRPC_PORT: " | sed 's/CMS_TRITON_GRPC_PORT: //')
	ARGS="address=0.0.0.0 port=$TRITON_PORT fallback=0 $ARGS"
fi

declare -A JOBS
for ((nj=0;nj<$NJOBS;nj++)); do
	# run job
	JOBNAME=job${nj}_th${NTHREADS}
	cmsRun run.py config=step4_PAT_Run3 tmi=1 device=$DEVICE sonic=$SONIC threads=$NTHREADS input=$INFILE output="file:out_${JOBNAME}.root" duplicate=$DUP $ARGS >& log_${JOBNAME}.log &
	JOBS[$nj]=$!
done

# wait for all cmsRun processes
for JOB in ${JOBS[@]}; do
	wait $JOB || true >& /dev/null
done

# remove manual server
if [ "$MANUAL" -eq 1 ]; then
	cmsTriton $GPUSERVER -n triton_server_instance -M $CMSSW_BASE/src/HeterogeneousCore/SonicTriton/data/models stop
fi
