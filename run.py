import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# helper
def import_obj(src,obj):
    return getattr(__import__(src,fromlist=[obj]),obj)

# choices
allowed_compression = ["none","deflate","gzip"]
allowed_devices = ["auto","cpu","gpu"]

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("--config", default="step2_PAT", type=str, help="cmsDriver-generated config to import")
parser.add_argument("--maxEvents", default=-1, type=int, help="Number of events to process (-1 for all)")
parser.add_argument("--noSonic", default=False, action="store_true", help="disable SONIC in workflow")
parser.add_argument("--serverName", default="default", type=str, help="name for server (used internally)")
parser.add_argument("--address", default="", type=str, help="server address")
parser.add_argument("--port", default=8001, type=int, help="server port")
parser.add_argument("--params", default="", type=str, help="json file containing server address/port")
parser.add_argument("--threads", default=1, type=int, help="number of threads")
parser.add_argument("--streams", default=0, type=int, help="number of streams")
parser.add_argument("--verbose", default=False, action="store_true", help="enable all verbose output")
parser.add_argument("--verboseClient", default=False, action="store_true", help="enable verbose output for clients")
parser.add_argument("--verboseServer", default=False, action="store_true", help="enable verbose output for server")
parser.add_argument("--verboseService", default=False, action="store_true", help="enable verbose output for TritonService")
parser.add_argument("--noShm", default=False, action="store_true", help="disable shared memory")
parser.add_argument("--compression", default="", type=str, choices=allowed_compression, help="enable I/O compression")
parser.add_argument("--ssl", default=False, action="store_true", help="enable SSL authentication for server communication")
parser.add_argument("--device", default="auto", type=str, choices=allowed_devices, help="specify device for fallback server")
parser.add_argument("--docker", default=False, action="store_true", help="use Docker for fallback server")
parser.add_argument("--imageName", default="", type=str, help="container image name for fallback server")
parser.add_argument("--tempDir", default="", type=str, help="temp directory for fallback server")
parser.add_argument("--modifiers", default="", nargs='*', type=str, help="additional process modifiers")
parser.add_argument("--tmi", default=False, action="store_true", help="include time/memory summary")
options = parser.parse_args()

options.sonic = not options.noSonic
options.shm = not options.noShm

if len(options.params)>0:
    with open(options.params,'r') as pfile:
        pdict = json.load(pfile)
    options.address = pdict["address"]
    options.port = int(pdict["port"])
    print("server = "+options.address+":"+str(options.port))

# activate modifiers
modifier_names = []
if options.sonic:
    modifier_names = ["allSonicTriton"]
modifier_names = modifier_names+[x for x in options.modifiers]
modifiers = []
for modifier in modifier_names:
    modifiers.append(import_obj("Configuration.ProcessModifiers.{}_cff".format(modifier),modifier))
    # need to do this before process is created/imported
    modifiers[-1]._setChosen()

process = import_obj(options.config,"process")
if len(modifiers)>0:
    process._Process__modifiers = process._Process__modifiers + tuple(modifiers)

if options.threads>0:
    process.options.numberOfThreads = options.threads
    process.options.numberOfStreams = options.streams

process.maxEvents.input = cms.untracked.int32(options.maxEvents)

if options.sonic:
    process.TritonService.verbose = options.verbose or options.verboseService
    process.TritonService.fallback.verbose = options.verbose or options.verboseServer
    process.TritonService.fallback.useDocker = options.docker
    process.TritonService.fallback.imageName = options.imageName
    process.TritonService.fallback.tempDir = options.tempDir
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
            producer.Client.verbose = options.verbose or options.verboseClient
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
