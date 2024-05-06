from WMCore.Configuration import Configuration
config = Configuration()

config.section_("General")
config.General.requestName = 'SONIC_MiniAOD_CRAB_test108_right_1x3100-10j'
config.General.workArea = 'crabsubmit'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'run.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.numCores = 1
config.JobType.maxMemoryMB = 3100
config.JobType.maxJobRuntimeMin = 230
### move here the Load-balancer parameters from run.py
config.JobType.pyCfgParams=['--address', 'triton-run2.cms.geddes.rcac.purdue.edu', '--port', '8001']


config.section_("Data")
config.Data.inputDataset = '/TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17RECO-106X_mc2017_realistic_v6-v2/AODSIM'
config.Data.inputDBS = 'global'
config.Data.ignoreLocality = 'False'
config.Data.allowNonValidInputDataset = 'False'
config.Data.splitting = 'FileBased'
#config.Data.splitting = 'EventBased'
config.Data.unitsPerJob = 1
NJOBS = 10  # This is not a configuration parameter, but an auxiliary variable that we use in the next line.
config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.publication = False
config.Data.outputDatasetTag = 'TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8_SONIC_2024_test0'

config.section_("Site")
config.Site.blacklist = ['T2_US_Caltech','T2_US_UCSD','T2_US_Florida','T2_US_MIT','T2_US_Nebraska','T2_US_Vanderbilt','T2_US_Wisconsin']
config.Site.whitelist = ['T2_US_Purdue']
config.Site.storageSite = 'T2_US_Purdue'
# this is needed in order to prevent jobs overflowing to blacklisted sites
config.section_("Debug")
config.Debug.extraJDL = ['+CMS_ALLOW_OVERFLOW=False']

