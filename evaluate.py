import os
import os.path as path
import subprocess
from tqdm import tqdm


homeDir = path.expanduser("~")
benchmarkDir = path.join(homeDir, "projects", "pandaPI", "HTN-po-domains")
assert(path.exists(benchmarkDir))


totalInstances = 0
for domainDir in os.listdir(benchmarkDir):
    domainDirAbs = path.join(benchmarkDir, domainDir)
    for problemDir in os.listdir(domainDirAbs):
        problemDirAbs = path.join(domainDirAbs, problemDir)
        planDir = path.join(problemDirAbs, "plans")
        for planPath in os.listdir(planDir):
            totalInstances += 1
pbar = tqdm(total=totalInstances)

executable = path.join(homeDir, "projects", "pandaPI", "pandaPIengine", "build", "run_verifier")
assert(path.exists(executable))
execExcutable = "./{}".format(path.relpath(executable))

currentDir = os.getcwd()
outputDir = path.join(currentDir, "eval-outputs")
if not path.exists(outputDir):
    os.mkdir(outputDir)

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

            # cmd = ["time", "-p", execExcutable, "-h", groundedProblemFile, "-p", planFile]
            cmd = "time " + execExcutable + " -h " + groundedProblemFile + " -p " + planFile + " -v sat-verifier"

            evalInfoFileName = "eval-info-instance-{}.txt".format(numInstances)
            # evalInfoFile = path.join(evalProblemDir, evalInfoFileName)

            proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                outs, errs = proc.communicate(timeout=600)
            except subprocess.TimeoutExpired:
                proc.kill()
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
                    # print(minutes, seconds)
                else:
                    numIncorrectInstances += 1
                    evalInfoFile = path.join(evalIncorrectDir, evalInfoFileName)
            
            with open(evalInfoFile, "w") as f:
                f.write(errs)
                f.write(outs)

            numInstances += 1
            # if numInstances % 20 == 0:
            #     message = "Num of succeed instances: {}\t Num of failed instances: {}\t Num of incorrect instances: {}".format(numSucceedInstances, numFailedInstances, numIncorrectInstances)
            #     tqdm.write(message)
            desc = "Succeed: {}/Failed: {}/Incorrect: {}".format(numSucceedInstances, numFailedInstances, numIncorrectInstances)
            pbar.update()
            pbar.set_description(desc, refresh=True)
            # pbar.refresh()

pbar.close()              


            # isFailedInstance = False
            # try:
            #     # r = subprocess.run(cmd, check=True, capture_output=True, text=True)
            #     r = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # except subprocess.CalledProcessError as e:
            #     numFailedInstances += 1
            #     with open(evalInfoFile, 'w') as f:
            #         f.write(e.stdout + e.stderr)
            #     isFailedInstance = True
            
            # if not isFailedInstance:
            #     with open(evalInfoFile, 'w') as f:
            #         stdout, stderr = (r.stdout.read(), r.stderr.read())
            #         f.write(stderr)
            #         f.write(stdout)
            #     outputs = [s for s in stdout.split("\n") if s]
            #     if outputs[-1] == "The given plan is a solution":
            #         numSuccessInstances += 1
            #     else:
            #         numIncorrectInstances += 1

            # numInstances += 1

print(numSucceedInstances)
print(numIncorrectInstances)
print(numFailedInstances)