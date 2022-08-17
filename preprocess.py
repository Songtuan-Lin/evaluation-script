import os
import argparse
import subprocess
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Arguments for the Evaluation')
parser.add_argument("--benchmarks", nargs="+", type=str, help="Directories of benchmarks")
parser.add_argument("--root", type=str, help="Root directories of domains")
parser.add_argument("--parser", type=str, help="Path to the parser")
parser.add_argument("--grounder", type=str, help="Path to the grounder")
parser.add_argument("--transformer", type=str, help="Path to the transformer")
parser.add_argument("--verifier", type=str, help="Path to the verifier")
parser.add_argument("--planner", type=str, help="Path to the planner")
parser.add_argument("--output", type=str, help="Output directory")
parser.add_argument("--inval", action="store_true", help="Are invalid instances")
args = parser.parse_args()


def parse_instance(ins, od, rd, dirs):
    with open(ins, "r") as f:
        df = f.readline().strip() # domain file
        pf = f.readline().strip() # problem file
        pl = f.readline() # plan
    dfn = df.split("/")[-1].split(".")[0] # domain file name
    pfn = pf.split("/")[-1].split(".")[0] # problem file name
    if "domain" in pfn:
        # domain file and problem file are in incorrect order
        pfn = dfn
        df, pf = pf, df
    df = os.path.join(rd, df)
    pf = os.path.join(rd, pf)
    dn = pf.split("/")[-2] # domain name
    ddir = os.path.join(od, dn) # output domain directory 
    if not os.path.exists(ddir):
        os.mkdir(ddir)
    pdir = os.path.join(ddir, pfn) # problem directory within the domain directory
    dfdir = os.path.join(pdir, "domain")
    pfdir = os.path.join(pdir, "problem")
    grodir = os.path.join(pdir, "grounded")
    pardir = os.path.join(pdir, "parser")
    if not os.path.exists(pdir):
        os.mkdir(pdir)
    np = len(os.listdir(pdir)) # number of parsed plan instances
    insdir = os.path.join(pdir, "plan_{}".format(np + 1))
    os.mkdir(insdir)
    cykpf = os.path.join(insdir, "plan-cyk.txt") # plan format for cyk verifier
    plpf = os.path.join(insdir, "plan-planning.txt") # plan format for planning-based verifier
    with open(cykpf, "w") as f:
        f.write(pl)
    actions = pl.split(";")
    with open(plpf, "w") as f:
        for action in actions:
            if action[-1] == "\n":
                action = action[:-1]
            f.write("(" + action + ")" + "\n")

    parf = os.path.join(insdir, "{}.htn".format(pfn)) # parsed problem file
    # command for parsing
    cmdp_cyk = args.parser + " " + df + " " + pf + " " + parf
    cmdp_pl = cmdp_cyk 

    grof_cyk = os.path.join(insdir, "{}-cyk.sas".format(pfn)) # grounded problem file for cyk
    grof_pl = os.path.join(insdir, "{}-planning.sas".format(pfn)) # founded problem file for planning-based
    # command for grounding
    if not args.inval:
        cmdg_cyk = args.grounder + " " + "-t -D" + " " + parf + " " + grof_cyk + " " + "-P" + " " + plpf
        cmdg_pl = args.grounder + " " + "-D" + " " + parf + " " + grof_pl + " " + "-P" + " " + plpf
    else:
        cmdg_cyk = args.grounder + " " + "-t -D" + " " + parf + " " + grof_cyk
        cmdg_pl = args.grounder + " " + "-D" + " " + parf + " " + grof_pl
    # command calling cyk-verifier
    cmdv_cyk = args.verifier + " " + "-h" + " " + grof_cyk + " " + "-p" + " " + cykpf + " " + "-v to-verifier"
    # command calling transformer 
    cmd_trans = args.transformer + " " + grof_pl + " " + plpf
    # transformed file
    trf = os.path.join("{}.verify".format(plpf))
    cmdv_pl = args.planner + " " + trf + " --suboptimal --gValue=none"

    cyk_sh = os.path.join(insdir, "cyk.sh")
    pl_sh = os.path.join(insdir, "planning.sh")
    with open(cyk_sh, "w") as f:
        f.write("ulimit -v 8388608\n")
        f.write(cmdp_cyk + "\n")
        f.write(cmdg_cyk + "\n")
        f.write(cmdv_cyk)
    with open(pl_sh, "w") as f:
        f.write("ulimit -v 8388608\n")
        f.write(cmdp_pl + "\n")
        f.write(cmdg_pl + "\n")
        f.write(cmd_trans + "\n")
        f.write(cmdv_pl)
    dirs.append(insdir)

def collect_instances(dirs):
    inss = []
    for d in dirs:
        for p in os.listdir(d):
            inss.append(os.path.join(d, p))
    return inss
    
if __name__ == "__main__":
    inss = collect_instances(args.benchmarks)
    dirs = []
    for ins in tqdm(inss):
        parse_instance(ins, args.output, args.root, dirs)