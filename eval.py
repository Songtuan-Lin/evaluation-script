import os
import argparse
import subprocess
import multiprocessing

from tqdm import tqdm
from functools import partial

parser = argparse.ArgumentParser(description='Arguments for Plan Verification Evaluators')
parser.add_argument("benchmarks", type=str, help="Specify the input benchmark directory")
parser.add_argument("-n", "--num_workers", default=None, type=int, help="Number of threads to run the evaluator")
parser.add_argument("--inval", action="store_true", help="Specify whether the input benchmark set consists of invalid instances")
parser.add_argument("--cyk", action="store_true", help="Run the evaluation for the CYK-based approach")
parser.add_argument("--planning", action="store_true", help="Run the evaluation for the planning-based approach")

args = parser.parse_args()

def collect_instances():
    instance_dirs = []
    for domain in os.listdir(args.benchmarks):
        domain_dir = os.path.join(args.benchmarks, domain)
        for problem in os.listdir(domain_dir):
            problem_dir = os.path.join(domain_dir, problem)
            for instance in os.listdir(problem_dir):
                instance_dir = os.path.join(problem_dir, instance)
                instance_dirs.append(instance_dir)
    return instance_dirs

def run_pl(lock, instance_dir):
    is_succeed_run = True
    domain_name = instance_dir.split("/")[-3]
    problem_name = instance_dir.split("/")[-2]
    plan_ind = instance_dir.split("/")[-1].split("_")[-1]
    # evaluation info directory
    output_dir = os.path.join(instance_dir, "eval-info")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # output info file
    eval_info_file = os.path.join(output_dir, "eval-info-pl.txt")
    cmd_file = os.path.join(instance_dir, "planning.sh")
    # run the plan verifier
    cmd = "time timeout 600 bash " + cmd_file
    proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = proc.communicate()
    if proc.returncode == 124: 
        # timeout
        err_info_file = os.path.join(output_dir, "err-info-pl.txt")
        is_succeed_run = False
        # print("non-zero returncore" + instance_dir)
        with open(err_info_file, "w") as ef:
            ef.write(outs)
            ef.write(errs)
        lock.acquire()
        try:
            with open("err-log-pl.txt", "a") as el:
                el.write("Domain: {}\tProblem: {}\tPlan: {}\tIncorrect Ins: {}\n".format(domain_name, problem_name, plan_ind, False))
        finally:
            lock.release()
    else:
        times = [e for e in errs.split("\n") if e]
        wallTime = times[-3].split('\t')[-1]
        minutes, seconds = wallTime.split("m")[0], wallTime.split("m")[-1][:-1]
        total_seconds = float(minutes) * 60 + float(seconds)
        with open(eval_info_file, "w") as of:
            of.write(outs)
        lock.acquire()
        try:
            with open("time-log-pl.txt", "a") as tl:
                tl.write("Domain: {}\tProblem: {}\tPlan: {}\tTime: {}\n".format(domain_name, problem_name, plan_ind, total_seconds))
        finally:
            lock.release()
    return is_succeed_run

def run_cyk(lock, instance_dir):
    is_succeed_run = True
    domain_name = instance_dir.split("/")[-3]
    problem_name = instance_dir.split("/")[-2]
    plan_ind = instance_dir.split("/")[-1].split("_")[-1]
    # evaluation info directory
    output_dir = os.path.join(instance_dir, "eval-info")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # output info file
    eval_info_file = os.path.join(output_dir, "eval-info-cyk.txt")
    cmd_file = os.path.join(instance_dir, "cyk.sh")
    # run the plan verifier
    cmd = "time timeout 600 bash " + cmd_file
    proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = proc.communicate()
    if proc.returncode != 0:
        # some error happens
        err_info_file = os.path.join(output_dir, "err-info-cyk.txt")
        is_succeed_run = False
        # print("non-zero returncore" + instance_dir)
        with open(err_info_file, "w") as ef:
            ef.write(outs)
            ef.write(errs)
        lock.acquire()
        try:
            with open("err-log-cyk.txt", "a") as el:
                el.write("Domain: {}\tProblem: {}\tPlan: {}\tIncorrect Ins: {}\n".format(domain_name, problem_name, plan_ind, False))
        finally:
            lock.release()
    else:
        lines = [line for line in outs.split("\n") if line]
        is_sol_output_str = "The given plan is a solution"
        if (lines[-1] != is_sol_output_str and not args.inval) or (lines[-1] == is_sol_output_str and args.inval):
            is_succeed_run = False
            err_info_file = os.path.join(output_dir, "err-log-cyk.txt")
            with open(err_info_file, "w") as ef:
                ef.write(outs)
                ef.write(errs)
            lock.acquire()
            try:
                with open("err-log-cyk.txt", "a") as el:
                    el.write("Domain: {}\tProblem: {}\tPlan: {}\tIncorrect Ins: {}\n".format(domain_name, problem_name, plan_ind, True))
            finally:
                lock.release()
        else:
            times = [e for e in errs.split("\n") if e]
            wallTime = times[-3].split('\t')[-1]
            minutes, seconds = wallTime.split("m")[0], wallTime.split("m")[-1][:-1]
            total_seconds = float(minutes) * 60 + float(seconds)
            with open(eval_info_file, "w") as of:
                of.write(outs)
            lock.acquire()
            try:
                with open("time-log-cyk.txt", "a") as tl:
                    tl.write("Domain: {}\tProblem: {}\tPlan: {}\tTime: {}\n".format(domain_name, problem_name, plan_ind, total_seconds))
            finally:
                lock.release()
    return is_succeed_run

def start_pl(instance_dirs):
    num_cpus = multiprocessing.cpu_count()
    lock = multiprocessing.Manager().Lock()
    # instance_dirs = [(lock, instance_dir) for instance_dir in instance_dirs]
    if args.num_workers is not None:
        num_workers = args.num_workers
    else:
        num_workers = num_cpus
    with multiprocessing.Pool(num_workers) as p:
        r = list(tqdm(p.imap(partial(run_pl, lock), instance_dirs), total=len(instance_dirs)))

def start_cyk(instance_dirs):
    num_cpus = multiprocessing.cpu_count()
    lock = multiprocessing.Manager().Lock()
    # instance_dirs = [(lock, instance_dir) for instance_dir in instance_dirs]
    if args.num_workers is not None:
        num_workers = args.num_workers
    else:
        num_workers = num_cpus
    with multiprocessing.Pool(num_workers) as p:
        r = list(tqdm(p.imap(partial(run_cyk, lock), instance_dirs), total=len(instance_dirs)))

if __name__ == "__main__":
    instance_dirs = collect_instances()
    if args.cyk:
        start_cyk(instance_dirs)
    if args.planning:
        start_pl(instance_dirs)