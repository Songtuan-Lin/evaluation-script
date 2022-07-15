import os
import argparse
import subprocess
import pdb

from tqdm import tqdm


parser = argparse.ArgumentParser(description='Arguments for Grounding')
parser.add_argument("instanceDirs", nargs="+", type=str, help="Input directories")
parser.add_argument("domainRoot", type=str, help="Domain root directory")
parser.add_argument("parser", type=str, help="Parser executable")
parser.add_argument("grounder", type=str, help="Grounder executable")
parser.add_argument("-o", "--output", dest="outputDir", type=str, default=None, help="Output directory")
parser.add_argument("-n", "--num", dest="numFile", type=int, default=None, help="Maximal number of files to create")
args = parser.parse_args()

filenames = []
for d in args.instanceDirs:
    for instance in os.listdir(d):
        filenames.append(os.path.join(d, instance))

numFile = float("inf") if args.numFile is None else args.numFile
domainDir = os.path.join(os.path.expanduser("~"), "datasets", "htn-to-domains") if args.outputDir is None else args.outputDir

if not os.path.exists(domainDir):
    os.mkdir(domainDir)


visitedNumFile = 0
for filename in tqdm(filenames):
    visitedNumFile = visitedNumFile + 1
    with open(filename) as f:
        domainFile = f.readline().strip()
        problemFile = f.readline().strip()
        plan = f.readline()
    domainFileName = domainFile.split("/")[-1].split(".")[0]
    pfileName = problemFile.split("/")[-1].split(".")[0]
    if "domain" in pfileName:
        pfileName = domainFileName
        temp = domainFile
        domainFile = problemFile
        problemFile = temp
    domainName = problemFile.split("/")[-2]
    parentDir = os.path.join(domainDir, domainName)
    if not os.path.exists(parentDir):
        os.mkdir(parentDir)
    pfileDir = os.path.join(parentDir, pfileName)
    newDomainDir = os.path.join(pfileDir, "domain")
    newProblemDir = os.path.join(pfileDir, "problem")
    parsedDir = os.path.join(pfileDir, "parsed")
    groundedDir = os.path.join(pfileDir, "grounded")
    if not os.path.exists(pfileDir):
        os.mkdir(pfileDir)
        os.mkdir(parsedDir)
        os.mkdir(groundedDir)
    absParseOutputPath = os.path.join(parsedDir, pfileName + "." + "htn")
    absDomainPath = os.path.join(args.domainRoot, domainFile)
    absProblemPath = os.path.join(args.domainRoot, problemFile)

    numExistedPlans = len(os.listdir(groundedDir))
    planFileIndex = "plan_{n}".format(n = numExistedPlans + 1)
    groundedDirPerPlan = os.path.join(groundedDir, planFileIndex)
    os.mkdir(groundedDirPerPlan)
    absPlanFilePath = os.path.join(groundedDirPerPlan, "plan.txt")
    absPlanReFilePath = os.path.join(groundedDirPerPlan, "plan_reformat.txt")
    with open(absPlanFilePath, "w") as f:
        f.write(plan)
    absGroundOutputPath = os.path.join(groundedDirPerPlan, pfileName + "." + "sas")

    # write the plan to the file for the grounder
    actions = plan.split(";")
    with open(absPlanReFilePath, "w") as f:
        for action in actions:
            if action[-1] == "\n":
                action = action[:-1]
            f.write("(" + action + ")" + "\n")
    # planFileForGrounder = os.path.abspath("plan")
    planFileForGrounder = absPlanReFilePath

    if not os.path.exists(absParseOutputPath):
        parserPath = args.parser
        if not os.path.exists(newDomainDir):
            os.mkdir(newDomainDir)
            subprocess.run(["cp", absDomainPath, newDomainDir])
        if not os.path.exists(newProblemDir):
            os.mkdir(newProblemDir)
            subprocess.run(["cp", absProblemPath, newProblemDir])
        execParser = "./{}".format(os.path.relpath(parserPath))
        subprocess.run([execParser, absDomainPath, absProblemPath, absParseOutputPath], capture_output=True)
    
    grounderPath = args.grounder
    execGrounder = "./{}".format(os.path.relpath(grounderPath))
    subprocess.run([execGrounder, "-t", "-D", absParseOutputPath, absGroundOutputPath, "-P", planFileForGrounder], capture_output=True)
    if visitedNumFile >= numFile:
        break