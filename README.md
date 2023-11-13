# SONIC workflows

This repository serves to deploy and run SONIC workflows for performance tests.

## Setup
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
wget https://raw.githubusercontent.com/fastmachinelearning/sonic-workflows/CMSSW_13_3_X/setup.sh
chmod +x setup.sh
./setup.sh
source /cvmfs/cms.cern.ch/cmsset_default.sh
voms-proxy-init --rfc --voms cms -valid 192:00
cd CMSSW_13_3_X_2023-10-13-1100/src/sonic-workflows
cmsenv
```

Notes:
* Using an IB release until CMSSW_13_3_0_pre4 is out
  * includes update to DRN for determinism
* Input AODSIM files currently hosted at T2_IT_Pisa

## Purdue resources

Interactive CPU job:
```
sinteractive --account=cms --partition=hammer-g -N 1 -n1 -c4 --mem-per-cpu=2G
```

Interactive GPU job:
```
sinteractive --account=cms --partition=hammer-f --gres=gpu:1 -N 1 -n1 -c4 --mem-per-cpu=2G
```

## Running

To see the available options:
```bash
cmsRun run.py --help
```

To run a workflow with the default settings:
```bash
cmsRun run.py maxEvents=100
```

## Driver commands

2017 ultra-legacy re-miniAOD:
```bash
runTheMatrix.py -l 1325.517 --dryRun --command="--no_exec"
```

Modified commands:
```
dasgoclient --limit 0 --query 'file dataset=/TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17RECO-106X_mc2017_realistic_v6-v2/AODSIM site=T2_IT_Pisa' | sort -u > step1_dasquery.log
cat step1_dasquery.log | head -n 3 > step1_dasquery_truncated.log
cmsDriver.py step2  -s PAT --era Run2_2017 -n 100 --process PAT --conditions auto:phase1_2017_realistic --mc  --scenario pp --eventcontent MINIAODSIM --datatier MINIAODSIM --procModifiers run2_miniAOD_UL_preSummer20 --no_exec --filein filelist:step1_dasquery_truncated.log --fileout file:step2.root
```

UL re-miniAOD workflows for other years: 1325.516, 1325.5161, 1325.518

Run3/Phase2 SONIC-enabled workflows are available from `runTheMatrix.py -w upgrade -n` with suffix `.9001`

