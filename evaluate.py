import os
import os.path as path
import argparse
import subprocess
import matplotlib.pyplot as plt 
from tqdm import tqdm


parser = argparse.ArgumentParser(description='Process directories')
parser.add_argument("-o", "--outputDir", dest="outputDir", type=str, help="Specify the output directory")
parser.add_argument("-b", "--benchmarkDir", dest="benchmarkDir", type=str, help="Specify the input benchmark directory")
parser.add_argument("--invalid", dest="invalid", action="store_true", help="Specify whether the benchmark set is for invalid plans")
parser.add_argument("-v", "--verifier", dest="verifier", type=str, required=True, help="Specify the verifier to run")

args = parser.parse_args()

homeDir = path.expanduser("~")
currentDir = os.getcwd()
# create output directory
if not args.outputDir:
    outputDir = path.join(currentDir, "eval-outputs")
else:
    outputDir = args.outputDir
if not path.exists(outputDir):
    os.mkdir(outputDir)
# benchmark directory
if not args.benchmarkDir:
    benchmarkDir = path.join(homeDir, "Projects", "pandaPI", "HTN-po-domains")
    # benchmarkDir = path.join(homeDir, "Projects", "pandaPI", "Demo")
else:
    benchmarkDir = args.benchmarkDir
assert(path.exists(benchmarkDir))
# fetch the verifier
verifier = args.verifier


# count the total number of instances
totalInstances = 0
for domainDir in os.listdir(benchmarkDir):
    domainDirAbs = path.join(benchmarkDir, domainDir)
    for problemDir in os.listdir(domainDirAbs):
        problemDirAbs = path.join(domainDirAbs, problemDir)
        planDir = path.join(problemDirAbs, "plans")
        for planPath in os.listdir(planDir):
            totalInstances += 1
pbar = tqdm(total=totalInstances, dynamic_ncols = True)

executable = path.join(homeDir, "Projects", "pandaPI", "pandaPIengine", "build", "run_verifier")
assert(path.exists(executable))
execExcutable = "./{}".format(path.relpath(executable))

runtimeInfoFile = path.join(outputDir, "runtimeInfo.txt")

numSucceedInstances = 0
numFailedInstances = 0
numIncorrectInstances = 0

numInstances = 0

runTimes = []

for domainDir in os.listdir(benchmarkDir):
    domainName = domainDir
    domainDirAbs = path.join(benchmarkDir, domainDir)

    evalDomainDir = path.join(outputDir, domainName)
    if not path.exists(evalDomainDir):
        os.mkdir(evalDomainDir)
    
    for problemDir in os.listdir(domainDirAbs):
        problemName = problemDir
        problemDirAbs = path.join(domainDirAbs, problemDir)

        groundedProblemFile = path.join(problemDirAbs, "grounded", problemName + "." + "sas")
        assert(path.exists(groundedProblemFile))

        # evalProblemDir = path.join(evalDomainDir, problemName)
        evalSucceedDir = path.join(evalDomainDir, "succeed")
        evalFailedDir = path.join(evalDomainDir, "failed")
        evalIncorrectDir = path.join(evalDomainDir, "incorrect")
        if not path.exists(evalSucceedDir):
            os.mkdir(evalSucceedDir)
        if not path.exists(evalFailedDir):
            os.mkdir(evalFailedDir)
        if not path.exists(evalIncorrectDir):
            os.mkdir(evalIncorrectDir)

        planDir = path.join(problemDirAbs, "plans")

        for planPath in os.listdir(planDir):
            planFile = path.join(planDir, planPath)
            assert(path.exists(planFile))

            with open(planFile, "r") as pf:
                plan = pf.readlines()[0]
                planLength = len(plan.split(";"))

            # cmd = ["time", "-p", execExcutable, "-h", groundedProblemFile, "-p", planFile]
            cmd = "ulimit -v 8388608; " "time timeout 600 " + execExcutable + " -h " + groundedProblemFile + " -p " + planFile + " -v " + verifier

            evalInfoFileName = "eval-info-instance-{}.txt".format(numInstances)
            # evalInfoFile = path.join(evalProblemDir, evalInfoFileName)

            proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            outs, errs = proc.communicate()
                # numFailedInstances += 1

            if proc.returncode != 0:
                numFailedInstances += 1
                evalInfoFile = path.join(evalFailedDir, evalInfoFileName)
            else:
                outList = [s for s in outs.split("\n") if s]
                if outList[-1] == "The given plan is a solution":
                    numSucceedInstances += 1
                    evalInfoFile = path.join(evalSucceedDir, evalInfoFileName)
                    times = [e for e in errs.split("\n") if e]
                    wallTime = times[0].split('\t')[-1]
                    minutes, seconds = wallTime.split("m")[0], wallTime.split("m")[-1][:-1]
                    totalSeconds = float(minutes) * 60 + float(seconds)
                    runTimes.append(totalSeconds)
                    with open(runtimeInfoFile, "a") as rf:
                        info = "Domain: {}\tInstance: {}\truntime: {}\n".format(domainName, problemName, totalSeconds)
                        rf.write(info)
                    # print(minutes, seconds)
                else:
                    numIncorrectInstances += 1
                    evalInfoFile = path.join(evalIncorrectDir, evalInfoFileName)
            
            with open(evalInfoFile, "w") as f:
                domainInfo = "Domain name: {}\n".format(domainName)
                f.write(domainInfo)
                instanceInfo = "Problem instance: {}\n".format(problemName)
                f.write(instanceInfo)
                planInfo = "Plan length: {}\n".format(planLength)
                f.write(planInfo)
                f.write(errs)
                f.write(outs)

            numInstances += 1
            desc = "Succeed: {}/Failed: {}/Incorrect: {}".format(numSucceedInstances, numFailedInstances, numIncorrectInstances)
            pbar.update()
            pbar.set_description(desc, refresh=True)
            pbar.refresh()

pbar.close()              

onlyRuntimeFile = path.join(outputDir, "only-runtime.txt")
with open(onlyRuntimeFile, "w") as rf:
    for runTime in runTimes:
        rf.write(str(runTime) + "\n")

runTimes.sort()
figDir = path.join(outputDir)
figPath = path.join(figDir, "eval-outputs.png")

percentages = [(x / totalInstances) for x in range(len(runTimes))]
plt.plot(percentages, runTimes)
plt.xlabel("Percentage of solved instances")
plt.ylabel("Runtime in seconds")
# plt.axis([0, 1, 1, 10])
# plt.ylim([1, 10])
plt.yscale("log")
plt.savefig(figPath)