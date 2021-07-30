import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing
import sys

# choices
allowed_compression = ["none","deflate","gzip"]
allowed_devices = ["auto","cpu","gpu"]

options = VarParsing()
options.register("config", "step2_PAT", VarParsing.multiplicity.singleton, VarParsing.varType.string, "cmsDriver-generated config to import")
options.register("maxEvents", -1, VarParsing.multiplicity.singleton, VarParsing.varType.int, "Number of events to process (-1 for all)")
options.register("sonic", True, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "enable SONIC in workflow")
options.register("serverName", "default", VarParsing.multiplicity.singleton, VarParsing.varType.string, "name for server (used internally)")
options.register("address", "", VarParsing.multiplicity.singleton, VarParsing.varType.string, "server address")
options.register("port", 8001, VarParsing.multiplicity.singleton, VarParsing.varType.int, "server port")
options.register("params", "", VarParsing.multiplicity.singleton, VarParsing.varType.string, "json file containing server address/port")
options.register("threads", 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, "number of threads")
options.register("streams", 0, VarParsing.multiplicity.singleton, VarParsing.varType.int, "number of streams")
options.register("verbose", False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "enable verbose output")
options.register("shm", True, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "enable shared memory")
options.register("compression", "", VarParsing.multiplicity.singleton, VarParsing.varType.string, "enable I/O compression (choices: {})".format(', '.join(allowed_compression)))
options.register("ssl", False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "enable SSL authentication for server communication")
options.register("device","auto", VarParsing.multiplicity.singleton, VarParsing.varType.string, "specify device for fallback server (choices: {})".format(', '.join(allowed_devices)))
options.register("docker", False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "use Docker for fallback server")
options.register("tmi", False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "include time/memory summary")
options.register("dump", False, VarParsing.multiplicity.singleton, VarParsing.varType.bool, "dump process python config")
options.parseArguments()

if len(options.params)>0:
    with open(options.params,'r') as pfile:
        pdict = json.load(pfile)
    options.address = pdict["address"]
    options.port = int(pdict["port"])
    print("server = "+options.address+":"+str(options.port))

# check compression
if len(options.compression)>0 and options.compression not in allowed_compression:
    raise ValueError("Unknown compression setting: {}".format(options.compression))

# check devices
options.device = options.device.lower()
if options.device not in allowed_devices:
    raise ValueError("Unknown device: {}".format(options.device))

from Configuration.ProcessModifiers.allSonicTriton_cff import allSonicTriton
# need to do this before process is created/imported
if options.sonic:
    allSonicTriton._setChosen()

process = getattr(__import__(options.config,fromlist=["process"]),"process")
if options.sonic:
    process._Process__modifiers = process._Process__modifiers + (allSonicTriton,)

if options.threads>0:
    process.options.numberOfThreads = options.threads
    process.options.numberOfStreams = options.streams

process.maxEvents.input = cms.untracked.int32(options.maxEvents)

if options.sonic:
    process.TritonService.verbose = options.verbose
    process.TritonService.fallback.verbose = options.verbose
    process.TritonService.fallback.useDocker = options.docker
    if options.device != "auto":
        process.TritonService.fallback.useGPU = options.device=="gpu"
    if len(options.address)>0:
        process.TritonService.servers.append(
            cms.PSet(
                name = cms.untracked.string(options.serverName),
                address = cms.untracked.string(options.address),
                port = cms.untracked.uint32(options.port),
                useSsl = cms.untracked.bool(options.ssl),
                rootCertificates = cms.untracked.string(""),
                privateKey = cms.untracked.string(""),
                certificateChain = cms.untracked.string(""),
            )
        )

# propagate changes to all SONIC producers
keepMsgs = ['TritonClient','TritonService']
for producer in process._Process__producers.values():
    if hasattr(producer,'Client'):
        if hasattr(producer.Client,'verbose'):
            producer.Client.verbose = options.verbose
            keepMsgs.extend([producer._TypedParameterizable__type,producer._TypedParameterizable__type+":TritonClient"])
        if hasattr(producer.Client,'compression'):
            producer.Client.compression = options.compression
        if hasattr(producer.Client,'useSharedMemory'):
            producer.Client.useSharedMemory = options.shm

if options.verbose:
    process.load('FWCore/MessageService/MessageLogger_cfi')
    process.MessageLogger.cerr.FwkReport.reportEvery = 500
    for msg in keepMsgs:
        setattr(process.MessageLogger.cerr,msg,
            cms.untracked.PSet(
                limit = cms.untracked.int32(10000000),
            )
        )

if options.tmi:
    from Validation.Performance.TimeMemorySummary import customise
    process = customise(process)

if options.dump:
    print(process.dumpPython())
    sys.exit(0)
