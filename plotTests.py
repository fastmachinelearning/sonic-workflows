from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from collections import OrderedDict
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import mplhep as hep

# style
hep.set_style(hep.style.CMS)
plt.style.use('default.mplstyle')
colors = ["#9c9ca1", "#e42536", "#5790fc", "#964a8b", "#f89c20", "#7a21dd"]
markers = ["o","v","^","s","D","P"]
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=colors)+mpl.cycler(marker=markers)

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-t", "--test", dest="test", type=str, help="txt file w/ results from anaTests.sh", required=True)
parser.add_argument("-n", "--numer", dest="numer", type=str, default=[], help="numer(s) for ratio", nargs='*')
parser.add_argument("-d", "--denom", dest="denom", type=str, default=[], help="denom(s) for ratio", nargs='*')
parser.add_argument("-s", "--suffix", dest="suffix", type=str, default="", help="suffix for plots")
parser.add_argument("-p","--pformats", dest="pformats", type=str, default=["png"], nargs='*', help="print plots in specified format(s)")
args = parser.parse_args()

data = OrderedDict()
def make_default(has_err=False):
    default = {"threads": np.array([]), "throughput": np.array([])}
    if has_err: default["err"] = np.array([])
    return default
with open(args.test,'r') as infile:
    for line in infile:
        line = line.rstrip()
        linesplit = line.split('\t')
        if len(linesplit)<3: continue
        type_, threads, throughput = linesplit
        throughsplit = throughput.split(' ')
        if len(throughsplit)>1: throughput, throughput_err = throughsplit
        else: throughput_err = None
        has_err = throughput_err is not None
        if type_ not in data:
            data[type_] = make_default(has_err)
        data[type_]["threads"] = np.append(data[type_]["threads"], int(threads))
        data[type_]["throughput"] = np.append(data[type_]["throughput"], float(throughput))
        if "err" in data[type_]: data[type_]["err"] = np.append(data[type_]["err"], float(throughput_err))

unknown = []
for req in args.numer+args.denom:
    if req not in data: unknown.append(req)
if len(unknown)>0:
    raise ValueError("Unknown test type(s) requested: "+", ".join(unknown))

# from https://github.com/kpedro88/SimGVCore/blob/PlotStyle2/Application/test/plotTest.py
# currently doesn't check if all tests have same values of threads
ratios = OrderedDict()
ratio_title = ""
ratio_key = 1
def make_ratio(numer,denom,ratios,data):
    key = (numer,denom)
    ratios[key] = make_default("err" in data[denom])
    ratios[key]["threads"] = np.copy(data[denom]["threads"])
    ratios[key]["throughput"] = np.divide(data[numer]["throughput"],data[denom]["throughput"])
    ratios[key]["err"] = ratios[key]["throughput"]*np.sqrt((data[numer]["err"]/data[numer]["throughput"])**2 + (data[denom]["err"]/data[denom]["throughput"])**2)
if len(args.numer)==1 and len(args.denom)==1:
    make_ratio(args.numer[0],args.denom[0],ratios,data)
    ratio_title = args.numer[0]+" / "+args.denom[0]
elif len(args.numer)==1 and len(args.denom)>1:
    for denom in args.denom:
        make_ratio(args.numer[0],denom,ratios,data)
    ratio_title = args.numer[0]+" / *"
elif len(args.numer)>1 and len(args.denom)==1:
    for numer in args.numer:
        make_ratio(numer,args.denom[0],ratios,data)
    ratio_title = "* / "+args.denom[0]
    ratio_key = 0
elif len(args.numer)>0 and len(args.numer)==len(args.denom):
    for numer,denom in zip(args.numer,args.denom):
        make_ratio(numer,denom,ratios,data)
    ratio_title = "ratio"

def save_plot(fig, name, pformats):
    for pformat in pformats:
        fargs = {}
        if pformat=="png": fargs = {"dpi":100, "bbox_inches":"tight"}
        elif pformat=="pdf": fargs = {"bbox_inches":"tight"}
        fig.savefig(name+"."+pformat,**fargs)

xtitle = "Threads/job"
ytitle = "Throughput [evt/s]"
details = "\n".join(["Nevents = 2000*threads/job","Intel(R) Xeon(R) W-2295 CPU @ 3.00GHz"])
colors_used = OrderedDict()
markers_used = OrderedDict()
# one plot for data, one plot for ratios
for plot in [data,ratios]:
    fig, ax = plt.subplots()

    isratio = False
    for val in plot:
        if isinstance(val,tuple):
            label = val[0] + " / " + val[1]
            isratio = True
        else:
            label = val
        container = ax.errorbar(plot[val]["threads"], plot[val]["throughput"], yerr = plot[val]["err"] if len(plot[val]["err"])>0 else None, label=label, linestyle="")
        line = ax.get_lines()[-1]
        if isratio:
            line.set_color(colors_used[val[ratio_key]])
            line.set_marker(markers_used[val[ratio_key]])
            # set error bar color
            _, _, (vertical_lines,) = container.lines
            vertical_lines.set_color(colors_used[val[ratio_key]])
        else:
            colors_used[val] = line.get_color()
            markers_used[val] = line.get_marker()

    # add perfect scaling line
    if not isratio:
        try:
            slope = next(y for x,y in zip(data["Direct"]["threads"],data["Direct"]["throughput"]) if x==1)
            xvals = np.array(list(ax.get_xlim()))
            ax.plot(xvals, slope*xvals, color='k', linestyle='--', label="Perfect", marker='')
        except:
            pass

    # axis info
    try:
        min_divisor = next(x for x in data["Direct"]["threads"] if x>1)
    except:
        min_divisor = 1
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(min_divisor))
    ax.set_xlabel(xtitle)
    ax.set_ylabel(ratio_title+" ("+ytitle+")" if isratio else ytitle)
    fig.tight_layout()
    legend = ax.legend(loc="best")
    hep.cms.text("Simulation")
    ax = hep.cms.lumitext(ax=ax, text=details, fontsize=mpl.rcParams["font.size"]*0.5)

    pname = "threads_vs_throughput"+("__ratio" if isratio else "")
    if len(args.suffix)>0: pname = pname+"__"+args.suffix
    save_plot(fig, pname, args.pformats)

