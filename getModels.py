#!/usr/bin/env python3

import FWCore.ParameterSet.Config as cms
import os,sys,glob,contextlib
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from FWCore.ParameterSet.pfnInPath import pfnInPath

# helper
def import_obj(src,obj):
    return getattr(__import__(src,fromlist=[obj]),obj)

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("--config", default="step2_PAT", type=str, help="cmsDriver-generated config to import")
parser.add_argument("--modifiers", default="", nargs='*', type=str, help="additional process modifiers")
parser.add_argument("--noSonic", default=False, action="store_true", help="disable SONIC in workflow")
parser.add_argument("--verbose", default=False, action="store_true", help="enable verbose output")
options = parser.parse_args()

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

context_stdout = contextlib.nullcontext if options.verbose else contextlib.redirect_stdout
context_stderr = contextlib.nullcontext if options.verbose else contextlib.redirect_stderr
with context_stdout(open(os.devnull,'w')), context_stderr(open(os.devnull,'w')):
	process = import_obj(options.config,"process")
if len(modifiers)>0:
    process._Process__modifiers = process._Process__modifiers + tuple(modifiers)

# get model info from SONIC producers
for pname,producer in process._Process__producers.items():
    if hasattr(producer,'Client'):
        path = producer.Client.modelConfigPath.value()
        fullpath = pfnInPath(path).replace("file:","").replace("config.pbtxt","")
        version = producer.Client.modelVersion.value()
        if len(version)==0:
            # this implements Triton's default version policy: provide only the latest version
            # ignoring non-integer versions and versions that start with 0
            versions = glob.glob(fullpath+'*/')
            versions = [os.path.basename(os.path.dirname(v)) for v in versions]
            version = str(max([int(v) for v in versions if v.isdigit() and not v[0]=='0']))
        dir = os.path.join(fullpath,version)
        print(dir)
