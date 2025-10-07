from Condor.Production.jobSubmitter import *

class jobSubmitterSonic(jobSubmitter):
    def __init__(self):
        super(jobSubmitterSonic,self).__init__()

    def addExtraOptions(self,parser):
        super(jobSubmitterSonic,self).addExtraOptions(parser)
        parser.add_option("--name", dest="name", default="test", help="job name (default = %default)")
        parser.add_option("--outdir", dest="outdir", default="", help="output file directory (PFN) (default = %default)")
        parser.add_option("-A", "--args", dest="args", default="", help="additional common args to use for all jobs (default = %default)")

    def checkExtraOptions(self,options,parser):
        super(jobSubmitterSonic,self).checkExtraOptions(options,parser)

        # input is not necessarily required
        if len(options.outdir)==0:
            parser.error("Required option: --outdir [directory]")

    def generateSubmission(self):
        job = protoJob()
        job.name = self.name
        self.generatePerJob(job)

        for iJob in range(1):
            job.njobs += 1
            job.nums.append(iJob)

        if self.prepare:
            with open("input/args_"+job.name+".txt",'w') as argfile:
                argfile.write(self.args)

        job.queue = "-queue "+str(job.njobs)
        self.protoJobs.append(job)

    def generateExtra(self,job):
        super(jobSubmitterSonic,self).generateExtra(job)
        job.patterns.update([
            ("JOBNAME",job.name+"_part$(Process)_$(Cluster)"),
            ("EXTRAINPUTS","input/args_"+job.name+".txt"),
            ("EXTRAARGS","-j "+job.name+" -o "+self.outdir),
        ])
