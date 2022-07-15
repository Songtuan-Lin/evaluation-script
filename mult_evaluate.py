import os
import argparse
import subprocess
import multiprocessing

from tqdm import tqdm
from functools import partial
import pdb

parser = argparse.ArgumentParser(description='Arguments for Plan Verification Evaluators')
parser.add_argument("benchmarks_dir", type=str, help="Specify the input benchmark directory")
parser.add_argument("executable", type=str, help="Specify the verifier executable to run")
parser.add_argument("verifier", type=str, help="Specify the verifier")
parser.add_argument("-o", "--outputDir", dest="output_dir", type=str, help="Specify the output directory")
parser.add_argument("-n", "--num_workers", default=None, type=int, help="Number of threads to run the evaluator")
parser.add_argument("--invalid", dest="invalid", action="store_true", help="Specify whether the benchmark set is for invalid plans")

args = parser.parse_args()

def run(lock, instance_dir):
    is_succeed_run = True
    exec_cmd = "./{}".format(os.path.relpath(args.executable))
    htn_file, plan_file = None, None
    for f in os.listdir(instance_dir):
        if ".sas" in f:
            htn_file = os.path.join(instance_dir, f)
        elif ".txt" in f:
            plan_file = os.path.join(instance_dir, f)
    if htn_file is None or plan_file is None:
        print("Fail to fetch the HTN problem file or the plan file in {}\n".format(instance_dir))
        raise AssertionError("Fail to fetch the HTN problem file or the plan file")
    domain_name = instance_dir.split("/")[-4]
    problem_name = instance_dir.split("/")[-3]
    plan_ind = instance_dir.split("/")[-1].split("_")[-1]
    # evaluation info directory
    output_dir = os.path.join(instance_dir, "eval-info")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # output info file
    eval_info_file = os.path.join(output_dir, "eval-info.txt")
    # run the plan verifier
    cmd = "ulimit -v 8388608; " "time timeout 600 " + exec_cmd + " -h " + htn_file + " -p " + plan_file + " -v " + args.verifier
    proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = proc.communicate()
    if proc.returncode != 0:
        # some error happens
        err_info_file = os.path.join(output_dir, "err-info.txt")
        is_succeed_run = False
        # print("non-zero returncore" + instance_dir)
        with open(err_info_file, "w") as ef:
            ef.write(outs)
            ef.write(errs)
        lock.acquire()
        try:
            with open("err-log.txt", "a") as el:
                el.write("Domain: {}\tProblem: {}\tPlan: {}\tIncorrect Ins: {}\n".format(domain_name, problem_name, plan_ind, False))
        finally:
            lock.release()
    else:
        lines = [line for line in outs.split("\n") if line]
        if lines[-1] != "The given plan is a solution":
            is_succeed_run = False
            err_info_file = os.path.join(output_dir, "err-log.txt")
            with open(err_info_file, "w") as ef:
                ef.write(outs)
                ef.write(errs)
            lock.acquire()
            try:
                with open("err-log.txt", "a") as el:
                    el.write("Domain: {}\tProblem: {}\tPlan: {}\tIncorrect Ins: {}\n".format(domain_name, problem_name, plan_ind, True))
            finally:
                lock.release()
        else:
            times = [e for e in errs.split("\n") if e]
            wallTime = times[0].split('\t')[-1]
            minutes, seconds = wallTime.split("m")[0], wallTime.split("m")[-1][:-1]
            total_seconds = float(minutes) * 60 + float(seconds)
            with open(eval_info_file, "w") as of:
                of.write(outs)
            lock.acquire()
            try:
                with open("time-log.txt", "a") as tl:
                    tl.write("Domain: {}\tProblem: {}\tPlan: {}\tTime: {}\n".format(domain_name, problem_name, plan_ind, total_seconds))
            finally:
                lock.release()
    return is_succeed_run

def collect_instances():
    instance_dirs = []
    for domain in os.listdir(args.benchmarks_dir):
        domain_dir = os.path.join(args.benchmarks_dir, domain)
        for problem in os.listdir(domain_dir):
            problem_dir = os.path.join(domain_dir, problem)
            grounded_files_dir = os.path.join(problem_dir, "grounded")
            for instance in os.listdir(grounded_files_dir):
                instance_dir = os.path.join(grounded_files_dir, instance)
                instance_dirs.append(instance_dir)
    return instance_dirs

def start():
    # num_succeed_instances = 0
    num_cpus = multiprocessing.cpu_count()
    print("- Number of avaliable CPUs: {}\n".format(num_cpus))
    instance_dirs = collect_instances()
    print("- Total number of instances: {}\n".format(len(instance_dirs)))
    lock = multiprocessing.Manager().Lock()
    # instance_dirs = [(lock, instance_dir) for instance_dir in instance_dirs]
    if args.num_workers is not None:
        num_workers = args.num_workers
    else:
        num_workers = num_cpus
    with multiprocessing.Pool(num_workers) as p:
        r = list(tqdm(p.imap(partial(run, lock), instance_dirs), total=len(instance_dirs)))
        # imap_it = p.imap_unordered(run, instance_dirs)
        # for re in imap_it:
        #     if re:
        #         num_succeed_instances += 1
    # print("Succeed instances: {}\t Failed instances: {}\n".format(num_succeed_instances, len(instance_dirs) - num_succeed_instances))

def reformat_plans(instance_dirs):
    for instance_dir in instance_dirs:
        plan_file = os.path.join(instance_dir, "plan.txt")
        with open(plan_file, "r") as f:
            plan = f.readline()
        actions = plan.split(";")
        plan_reformat_file = os.path.join(instance_dir, "plan_reformat.txt")
        with open(plan_reformat_file, "w") as f:
            for action in actions:
                if action[-1] == "\n":
                    action = action[:-1]
                f.write("(" + action + ")" + "\n")

if __name__ == "__main__":
    start()