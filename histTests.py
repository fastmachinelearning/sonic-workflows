from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from collections import OrderedDict
import numpy as np
from scipy import stats
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import mplhep as hep

# style
hep.set_style(hep.style.CMS)
plt.style.use('default.mplstyle')
colors = ["#9c9ca1", "#e42536", "#5790fc", "#964a8b", "#f89c20", "#7a21dd"]
styles = ['-','--',':','-.','-','--']
markers = ["o","v","^","s","D","P"]
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=colors)+mpl.cycler(marker=markers)+mpl.cycler(linestyle=styles)

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-t", "--test", dest="test", type=str, help="txt file w/ results from anaTests.sh", required=True)
parser.add_argument("-T", "--threads", dest="threads", type=int, help="threads/job value", required=True)
parser.add_argument("-s", "--suffix", dest="suffix", type=str, default="", help="suffix for plots")
parser.add_argument("-p","--pformats", dest="pformats", type=str, default=["png"], nargs='*', help="print plots in specified format(s)")
args = parser.parse_args()

data = OrderedDict()
xmin = 1e10
xmax = 0
npts = 0
with open(args.test,'r') as infile:
    for line in infile:
        line = line.rstrip()
        linesplit = line.split('\t')
        if len(linesplit)<3: continue
        type_, threads, throughput = linesplit
        if int(threads)!=args.threads: continue
        throughputs = np.array([float(x) for x in throughput.split(' ')])
        data[type_] = throughputs
        xmax = max(xmax,max(throughputs))
        xmin = min(xmin,min(throughputs))
        npts = len(throughputs)

def save_plot(fig, name, pformats):
    for pformat in pformats:
        fargs = {}
        if pformat=="png": fargs = {"dpi":100, "bbox_inches":"tight"}
        elif pformat=="pdf": fargs = {"bbox_inches":"tight"}
        fig.savefig(name+"."+pformat,**fargs)

xtitle = "Throughput/job [evt/s]"
details = "\n".join(["Nevents = 2000*threads/job; threads/job = {}".format(args.threads),"Intel(R) Xeon(R) W-2295 CPU @ 3.00GHz"])

# create histograms
nbins = npts/2
bins = np.linspace(xmin, xmax, nbins)
fig, ax = plt.subplots()
for key,val in data.items():
    counts, hbins = np.histogram(val, bins=bins)
    ax.hist(hbins[:-1], hbins, weights=counts, label=key, histtype='step')
ax.set_xlabel(xtitle)
ax.set_ylabel("Number of jobs")
fig.tight_layout()
legend = ax.legend(loc="best")
hep.cms.text("Simulation")
ax = hep.cms.lumitext(ax=ax, text=details, fontsize=mpl.rcParams["font.size"]*0.5)

pname = "hist_throughput_th{}".format(args.threads)
if len(args.suffix)>0: pname = pname+"__"+args.suffix
save_plot(fig, pname, args.pformats)
