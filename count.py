import os
import os.path as path
from tabulate import tabulate

homeDir = path.expanduser("~")
evalDir = path.join(homeDir, "Codes", "evaluation")

evalOldDir = path.join(evalDir, "eval-outputs-old")
evalNewDir = path.join(evalDir, "eval-outputs-new")

startDirs = [evalNewDir, evalOldDir]

outputs = []
domains = set()

for evalStartDir in startDirs:
    stat = {}
    for domain in os.listdir(evalStartDir):
        domainFullPath = path.join(evalStartDir, domain)
        if path.isdir(domainFullPath):
            domains.add(domain)
            succeedInsDir = path.join(domainFullPath, "succeed")
            numSucceed = len([fileName for fileName in os.listdir(succeedInsDir)])

            failedInsDir = path.join(domainFullPath, "failed")
            numFailed = len([fileName for fileName in os.listdir(failedInsDir)])
            
            domainStat = {"succeed": numSucceed, "failed": numFailed}
            stat[domain] = domainStat

    outputs.append(stat)

domains = list(domains)

table = []
startColumn = ["New Implementation", "Reimplementation"]

firstRow = ["Total Instances"]
headers = [""]
for domain in domains:
    numSucceed = outputs[0][domain]["succeed"]
    numFailed = outputs[0][domain]["failed"]
    firstRow.append(numSucceed + numFailed)
    headers.append(domain)
table.append(firstRow)

for i in [0, 1]:
    info = [startColumn[i]]
    target = outputs[i]
    for i, domain in enumerate(domains):
        if domain not in target:
            numSucceed = 0
            rate = 0
        else:
            numSucceed = target[domain]["succeed"]
            rate = numSucceed / firstRow[i + 1] 
        info.append("{0} ({1:.2f}%)".format(numSucceed, rate * 100))
    table.append(info)

maxColWidths = []

print(tabulate(table, headers = headers, tablefmt="latex_booktabs"))
