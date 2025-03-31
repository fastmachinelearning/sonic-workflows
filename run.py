import FWCore.ParameterSet.Config as cms
import sys
from HeterogeneousCore.SonicTriton.customize import getParser, getOptions, applyOptions

# helper
def import_obj(src,obj):
    return getattr(__import__(src,fromlist=[obj]),obj)

parser = getParser()
parser.add_argument("--config", default="step2_PAT", type=str, help="cmsDriver-generated config to import")
parser.add_argument("--redir", default="", type=str, help="specify xrootd redirector (or site name) for input files")
parser.add_argument("--noSonic", default=False, action="store_true", help="disable SONIC in workflow")
parser.add_argument("--modifiers", default="", nargs='*', type=str, help="additional process modifiers")
parser.add_argument("--tmi", default=False, action="store_true", help="include time/memory summary")
options = getOptions(parser, verbose=True)

options.sonic = not options.noSonic

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

if len(options.redir)>0:
    if options.redir[0]=="T":
        options.redir = "root://cmsxrootd.fnal.gov//store/test/xrootd/"+options.redir
    process.source.fileNames = [(options.redir if val.startswith("/") else "")+val for val in process.source.fileNames]

# propagate changes to all SONIC producers
process = applyOptions(process, options, applyToModules=True)

if options.tmi:
    from Validation.Performance.TimeMemorySummary import customise
    process = customise(process)
