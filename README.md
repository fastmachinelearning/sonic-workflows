# SONIC workflows

This repository serves to deploy and run SONIC workflows for performance tests.

## Setup
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
wget https://raw.githubusercontent.com/fastmachinelearning/sonic-workflows/test_24.11/setup.sh
chmod +x setup.sh
./setup.sh
voms-proxy-init --rfc --voms cms -valid 192:00
cd CMSSW_15_1_0_pre4/src/sonic-workflows
cmsenv
```

Notes:
* Input AODSIM files currently hosted at Purdue

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
cmsRun run.py --maxEvents 100
```

## Driver commands

2023 miniAOD:
```bash
runTheMatrix.py -w upgrade -l 12434.21 --dryRun --command="--no_exec"
```

Modified commands:
```bash
./get_files_on_disk.py /TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM -o files__TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8__Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2__AODSIM.txt
cat files__TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8__Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2__AODSIM.txt | head -n 3 > files__TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8__Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2__AODSIM__truncated.txt
cmsDriver.py step4  -s PAT --conditions auto:phase1_2023_realistic --datatier MINIAODSIM -n 10 --eventcontent MINIAODSIM --geometry DB:Extended --era Run3_2023 --no_exec --filein filelist:files__TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8__Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2__AODSIM__truncated.txt --fileout file:step4.root
```
Run3/Phase2 SONIC-enabled workflows are available from `runTheMatrix.py -w upgrade -n` with suffix `.9001`

## Listing models

The following script provides a list of all models possibly used by a config:
```
./getModels.py --config step4_PAT
```
(Some of the listed models may not actually be used, depending on task and output configurations, but that can only be evaluated by fully executing the config.)
