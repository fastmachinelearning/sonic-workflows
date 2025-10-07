#!/bin/bash

export JOBNAME=""
export OUTDIR=""
export OPTIND=1
while [[ $OPTIND -le $# ]]; do
	OPTOLD=$OPTIND
	# getopts in silent mode, don't exit on errors
	getopts ":j:o:" opt || status=$?
	case "$opt" in
		j) export JOBNAME=$OPTARG
		;;
		o) export OUTDIR=$OPTARG
		;;
		# keep going if getopts had an error, but make sure not to skip anything
		\? | :) OPTIND=$((OPTOLD+1))
		;;
	esac
done

echo "parameter set:"
echo "JOBNAME:    $JOBNAME"
echo "OUTDIR:     $OUTDIR"

cd $CMSSW_BASE/src/sonic-workflows

ARGS=$(cat $_CONDOR_SCRATCH_DIR/args_${JOBNAME}.txt)
echo "cmsRun run.py ${ARGS} 2>&1"
cmsRun run.py ${ARGS} 2>&1

CMSEXIT=$?

if [[ $CMSEXIT -ne 0 ]]; then
  cat *.log
  echo "exit code $CMSEXIT, skipping xrdcp"
  exit $CMSEXIT
fi

# copy output to eos
echo "xrdcp output for condor"
for FILE in *.root; do
	echo "xrdcp -f ${FILE} ${OUTDIR}/${FILE}"
	stageOut -x "-f" -i ${FILE} -o ${OUTDIR}/${FILE} -r -c '*.root' 2>&1
	XRDEXIT=$?
	if [[ $XRDEXIT -ne 0 ]]; then
		echo "exit code $XRDEXIT, failure in xrdcp"
		exit $XRDEXIT
	fi
done
