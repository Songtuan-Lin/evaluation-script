import os
import argparse
import subprocess
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Arguments for the Evaluation')
parser.add_argument("--benchmarks", nargs="+", type=str, help="Directories of benchmarks")
parser.add_argument("--root", type=str, help="Root directories of domains")
parser.add_argument("--parser", type=str, help="Path to the parser")
parser.add_argument("--grounder", type=str, help="Path to the grounder")
parser.add_argument("--verifier", type=str, help="Path to the verifier")
parser.add_argument("--specification", type=str, help="Specification of the verifier")
parser.add_argument("--outputs", type=str, help="Output directory")
args = parser.parse_args()


def parse_instance(ins, od, rd, lock):
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
    lock.acquire()
    if not os.path.exists(ddir):
        os.mkdir(ddir)
    pdir = os.path.join(ddir, pfn) # problem directory within the domain directory
    dfdir = os.path.join(pdir, "domain")
    pfdir = os.path.join(pdirm "problem")
    grodir = os.path.join(pdir, "grounded")
    pardir = os.path.join(pdir, "parser")
    if not os.path.exists(pdir):
        os.mkdir(pdir)
        os.mkdir(dfdir)
        os.mkdir(pfdir)
        os.mkdir(grodir)
        os.mkdir(pardir)
    np = len(os.listdir(grodir)) # number of parsed plan instanfce
    insdir = os.path.join(grodir, "plan_{}".format(np + 1))
    lock.release()

    


class Evaluator:
    def __init__(self, benchmarks, root, parser, grounder, verifier, specification, output):
        self._root = root
        self._par = parser
        self._gro = grounder
        self._ver = verifier
        self._spec = specification
        self._out = "output" if output is None else output
        _collect_file_names(benchmarks)
    
    def _collect_file_names(self, benchmarks):
        self._ins = []
        for b in benchmarks:
            for ins in b:
                # each instance in the benchmark set
                _read_instance(ins)

    def _read_instance(self, ins):
        with open(ins, "r") as f:
            df = f.readline().strip() # domain file
            pf = f.readline().strip() # problem file
            pl = f.readline() # plan
        dfn = df.split("/")[-1].split(".")[0] # domain file name
        pfn = pf.split("/")[-1].split(".")[0] # problem file name
        if "domain" in pn:
            # domain file and problem file are in incorrect order
            pfn = dfn
            df, pf = pf, df
        df = os.path.join(self._root, df)
        pf = os.path.join(self._root, pf)
        dn = pf.split("/")[-2] # domain name
        d_dir = os.path.join(self._out, dn) # directory for the domain
        if not os.path.exists(d_dir):
            # create the domain directory if it does not exist yet
            os.mkdir(d_dir)
        p_dir = os.path.join(d_dir, pfn)
        df_dir = os.path.join(p_dir, "domain") # (sub)directory for the domain file
        pf_dir = os.path.join(p_dir, "problem") # directory for the problem file
        pedf_dir = os.path.join(p_dir, "parsered") # directory for the parsered file
        gedf_dir = os.path.join(p_dir, "grounded") # directory for the grounded files
        if not os.path.exists(p_dir):
            os.mkdir(p_dir)
            os.mkdir(df_dir)
            os.mkdir(pf_dir)
            os.mkdir(pedf_dir)
            os.mkdir(gedfs_dir)
        self._ins.append((plan, df, dn, df_dir, pf, pfn, pf_dir, pedf_dir, gedf_dir))

    def _eval_instance(self, lock, i):
        plan, df, dn, df_dir, pf, pfn, pf_dir. pedf_dir, gedf_dir = i
        lock.acquire()
        n = len(os.listdir(gedf_dir))
        pl_dir = os.path.join(gedf_dir, "plan_{}".format(n + 1)) # directory for the plan instance
        os.mkdir(pl_dir)
        lock.release()
        plf = os.path.join(pl_dir, "plan.txt") # created plan file
        plf_re = os.path.join(pl_dir, "plan_reformat.txt")
        # write to the plan file
        with open(plf, "w") as f:
            f.write(pl)
        # reformat the plan file
        with open(plf_re, "w") as f:
            actions = pl.split(";")
            for action in actions:
                if action[-1] == "\n":
                    action = action[:-1]
                f.write("(" + action + ")" + "\n")
        pa_exec = "./{}".format(os.path.relpath(self._par)) # command to execute parser
        gr_exec = "./{}".format(os.path.relpath(self._gro)) # command to execute grounder
        paf = os.path.join(pedf_dir, pfn + "." + "htn") # parsed file
        grf = os.path.join(gedf_dir, pfn + "." + "sas") # grounded file
        pa_cmd = pa_exec + " " + df + " " + pf + " " + paf
        gr_cmd = gr_exec + " " + "-t" + " " + "-D" + " " + paf + " " + grf + " " + "-P" + " " + plf_re
        

