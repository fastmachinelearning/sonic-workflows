# SONIC workflows

This repository serves to deploy and run SONIC workflows for performance tests.

## Setup
```bash
wget https://raw.githubusercontent.com/fastmachinelearning/sonic-workflows/master/setup.sh
chmod +x setup.sh
./setup.sh
cd CMSSW_12_0_0_pre5/src/sonic-workflows
cmsenv
```

## Running
```bash
cmsRun run.py
```

## Driver commands

2018 ultra-legacy re-miniAOD:
```bash
runTheMatrix.py -l 1325.518 --dryRun --command="--no_exec"
```

Modified commands:
```
dasgoclient --limit 0 --query 'file dataset=/RelValProdTTbar_13_pmx25ns/CMSSW_10_6_4-PUpmx25ns_106X_upgrade2018_realistic_v9-v1/AODSIM' | sort -u > step1_dasquery.log
cmsDriver.py step2  -s PAT --era Run2_2018 -n 100 --process PAT --conditions auto:phase1_2018_realistic --mc  --scenario pp --eventcontent MINIAODSIM --datatier MINIAODSIM --procModifiers run2_miniAOD_UL_preSummer20 --no_exec --filein filelist:step1_dasquery.log --fileout file:step2.root
```

UL re-miniAOD workflows for other years: 1325.516, 1325.5161, 1325.517

Run3/Phase2 SONIC-enabled workflows are available from `runTheMatrix.py -w upgrade -n` with suffix `.9001`
