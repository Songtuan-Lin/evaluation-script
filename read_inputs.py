import os
import subprocess
import pdb

from tqdm import tqdm

prefix = os.path.join(os.path.expanduser("~"), "Projects", "ipc-benchmarks")
pandaPIPrefix = os.path.join(os.path.expanduser("~"), "Projects", "pandaPI")
planFilePath = os.path.join(prefix, "ipc-2020-plans", "plans", "IPC-2020")
planFilePathProgression = os.path.join(prefix, "ipc-2020-plans", "plans", "progression-128")
planFilePathSAT = os.path.join(prefix, "ipc-2020-plans", "plans", "sat-121")
# prefix = os.path.join(os.path.expanduser("~"), "projects", "pandaPI")
# planFilePath = os.path.join(prefix, "ipc-2020-plans", "po-plans", "IPC-2020")
# progressionPlanPath = os.path.join(prefix, "ipc-2020-plans", "po-plans", "progression-132")
# planFilePath = os.path.join(prefix, "ipc-2020-plans", "inval-po")
# planFilePath = os.path.join(prefix, "ipc-2020-plans", "inval-to")
# parser = argparse.ArgumentParser(description='Process Command Line Arguments')
# parser.add_argument('--file', type=str)

filenames = []
for filename in os.listdir(planFilePath):
    filenames.append(os.path.join(planFilePath, filename))
for filename in os.listdir(planFilePathProgression):
    filenames.append(os.path.join(planFilePathProgression, filename))
for filename in os.listdir(planFilePathSAT):
    filenames.append(os.path.join(planFilePathSAT, filename))
# for filename in os.listdir(progressionPlanPath):
#     filenames.append(os.path.join(progressionPlanPath, filename))

numFile = float("inf")
domainDir = os.path.join(os.path.expanduser("~"), "Datasets", "htn-to-domains")
# domainDir = os.path.join(prefix, "htn-po-domains")
# domainDir = os.path.join(prefix, "htn-po-domains-invalid")
# domainDir = os.path.join(prefix, "htn-to-domains-invalid")
if not os.path.exists(domainDir):
    os.mkdir(domainDir)


visitedNumFile = 0
for filename in tqdm(filenames):
    visitedNumFile = visitedNumFile + 1
    # absFilePath = os.path.join(planFilePath, filename)
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
    # print("problem file name>>>>>>>>>>>>>>>> " + problemFile + "\n")
    domainName = problemFile.split("/")[-2]
    # print("domain file name>>>>>>>>>>>>>>>>> " + domainFile + "\n")
    parentDir = os.path.join(domainDir, domainName)
    if not os.path.exists(parentDir):
        os.mkdir(parentDir)
    pfileDir = os.path.join(parentDir, pfileName)
    newDomainDir = os.path.join(pfileDir, "domain")
    newProblemDir = os.path.join(pfileDir, "problem")
    parsedDir = os.path.join(pfileDir, "parsed")
    groundedDir = os.path.join(pfileDir, "grounded")
    # planDir = os.path.join(parentDir, pfileDir, "plans")
    if not os.path.exists(pfileDir):
        os.mkdir(pfileDir)
        os.mkdir(parsedDir)
        os.mkdir(groundedDir)
        # if not os.path.exists(planDir):
        #     os.mkdir(planDir)
    absParseOutputPath = os.path.join(parsedDir, pfileName + "." + "htn")
    # absGroundOutputPath = os.path.join(groundedDir, pfileName + "." + "sas")
    absDomainPath = os.path.join(prefix, domainFile)
    absProblemPath = os.path.join(prefix, problemFile)

    numExistedPlans = len(os.listdir(groundedDir))
    planFileIndex = "plan_{n}".format(n = numExistedPlans + 1)
    groundedDirPerPlan = os.path.join(groundedDir, planFileIndex)
    # planFileName = "plan_{n}.txt".format(n = numExistedPlans + 1)
    os.mkdir(groundedDirPerPlan)
    absPlanFilePath = os.path.join(groundedDirPerPlan, "plan.txt")
    with open(absPlanFilePath, "w") as f:
        f.write(plan)
    absGroundOutputPath = os.path.join(groundedDirPerPlan, pfileName + "." + "sas")

    # write the plan to the file for the grounder
    actions = plan.split(";")
    with open("plan", "w") as f:
        for action in actions:
            if action[-1] == "\n":
                action = action[:-1]
            f.write("(" + action + ")" + "\n")
    planFileForGrounder = os.path.abspath("plan")
    # pdb.set_trace()

    if not os.path.exists(absParseOutputPath):
        parserPath = os.path.join(pandaPIPrefix, "pandaPIparser/pandaPIparser")
        if not os.path.exists(newDomainDir):
            os.mkdir(newDomainDir)
            subprocess.run(["cp", absDomainPath, newDomainDir])
        if not os.path.exists(newProblemDir):
            os.mkdir(newProblemDir)
            subprocess.run(["cp", absProblemPath, newProblemDir])
        execParser = "./{}".format(os.path.relpath(parserPath))
        subprocess.run([execParser, absDomainPath, absProblemPath, absParseOutputPath], capture_output=True)
    
    grounderPath = os.path.join(pandaPIPrefix, "pandaPIgrounder/pandaPIgrounder")
    execGrounder = "./{}".format(os.path.relpath(grounderPath))
    # subprocess.run([execGrounder, "--plan", absPlanFilePath, "-t", "-D", absParseOutputPath, absGroundOutputPath])
    subprocess.run([execGrounder, "-t", "-D", absParseOutputPath, absGroundOutputPath, "-P", planFileForGrounder], capture_output=True)

    # if not os.path.exists(absGroundOutputPath):
    #     grounderPath = os.path.join(prefix, "pandaPIgrounder/pandaPIgrounder")
    #     parserPath = os.path.join(prefix, "pandaPIparser/pandaPIparser")

    #     if not os.path.exists(newDomainDir):
    #         os.mkdir(newDomainDir)
    #     if not os.path.exists(newProblemDir):
    #         os.mkdir(newProblemDir)
    #     subprocess.run(["cp", absDomainPath, newDomainDir])
    #     subprocess.run(["cp", absProblemPath, newProblemDir])

    #     execGrounder = "./{}".format(os.path.relpath(grounderPath))
    #     execParser = "./{}".format(os.path.relpath(parserPath))
    #     subprocess.run([execParser, absDomainPath, absProblemPath, absParseOutputPath], capture_output=True)

    #     subprocess.run([execGrounder, "-t", "-D", absParseOutputPath, absGroundOutputPath])
    #     # subprocess.run([execGrounder, "-E", "-D", absParseOutputPath, absGroundOutputPath], capture_output=True)

    # numExistedPlans = len(os.listdir(planDir))
    # planFileName = "plan_{n}.txt".format(n = numExistedPlans + 1)
    # absPlanFilePath = os.path.join(planDir, planFileName)
    # with open(absPlanFilePath, "w") as f:
    #     f.write(plan)
    if visitedNumFile >= numFile:
        break

# print("Number of instances read: ")
# print(visitedNumFile)
