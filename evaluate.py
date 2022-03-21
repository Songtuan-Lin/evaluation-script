import os
import os.path as path
import subprocess


homeDir = path.expanduser("~")
benchmarkDir = path.join(homeDir, "Projects", "pandaPI", "Demo")
assert(path.exists(benchmarkDir))

executable = path.join(homeDir, "Projects", "pandaPI", "pandaPIengine", "build", "run_verifier")
assert(path.exists(executable))
execExcutable = "./{}".format(path.relpath(executable))

currentDir = os.getcwd()

numSuccessInstances = 0
numFailedInstances = 0
numIncorrectInstances = 0

for domainDir in os.listdir(benchmarkDir):
    domainName = domainDir
    domainDirAbs = path.join(benchmarkDir, domainDir)

    evalDomainDir = path.join(currentDir, domainName)
    if not path.exists(evalDomainDir):
        os.mkdir(evalDomainDir)
    
    for problemDir in os.listdir(domainDirAbs):
        problemName = problemDir
        problemDirAbs = path.join(domainDirAbs, problemDir)

        groundedProblemFile = path.join(problemDirAbs, "grounded", problemName + "." + "sas")
        assert(path.exists(groundedProblemFile))

        evalProblemDir = path.join(evalDomainDir, problemName)
        if not path.exists(evalProblemDir):
            os.mkdir(evalProblemDir)

        planDir = path.join(problemDirAbs, "plans")
        numInstances = 0
        for planPath in os.listdir(planDir):
            planFile = path.join(planDir, planPath)
            assert(path.exists(planFile))

            # cmd = ["time", "-p", execExcutable, "-h", groundedProblemFile, "-p", planFile]
            cmd = "time " + execExcutable + " -h " + groundedProblemFile + " -p " + planFile
            evalInfoFileName = "eval-info-instance-{}.txt".format(numInstances)
            evalInfoFile = path.join(evalProblemDir, evalInfoFileName)

            isFailedInstance = False
            try:
                # r = subprocess.run(cmd, check=True, capture_output=True, text=True)
                r = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            except subprocess.CalledProcessError as e:
                numFailedInstances += 1
                with open(evalInfoFile, 'w') as f:
                    f.write(e.stdout + e.stderr)
                isFailedInstance = True
            
            if not isFailedInstance:
                with open(evalInfoFile, 'w') as f:
                    stdout, stderr = (r.stdout.read(), r.stderr.read())
                    f.write(stderr)
                    f.write(stdout)
                outputs = [s for s in stdout.split("\n") if s]
                if outputs[-1] == "The given plan is a solution":
                    numSuccessInstances += 1
                else:
                    numIncorrectInstances += 1

            numInstances += 1

print(numSuccessInstances)
print(numIncorrectInstances)
print(numFailedInstances)