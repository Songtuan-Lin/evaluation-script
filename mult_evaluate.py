import os
import argparse
import subprocess
import multiprocessing


parser = argparse.ArgumentParser(description='Arguments for Plan Verification Evaluators')
parser.add_argument("benchmarks", dest="benchmarks_dir", type=str, help="Specify the input benchmark directory")
parser.add_argument("verifier", dest="verifier", type=str, help="Specify the verifier to run")
parser.add_argument("-o", "--outputDir", dest="outputDir", type=str, help="Specify the output directory")
parser.add_argument("--invalid", dest="invalid", action="store_true", help="Specify whether the benchmark set is for invalid plans")

args = parser.parse_args()

def run(instance_dir):
    is_succeed_run = True
    exec_cmd = "./{}".format(os.path.relpath(verifier))
    htn_file, plan_file = None, None
    for f in os.listdir(instance_dir):
        if ".sas" in f:
            htn_file = os.path.join(instance_dir, f)
        elif ".txt" in f:
            plan_file = os.path.join(instance_dir, f)
        else:
            raise AssertionError("Unknown file in the directory of the problem instance")
    if htn_file is None or plan_file is None:
        raise AssertionError("Fail to fetch the HTN problem file or the plan file")
    # evaluation info directory
    output_dir = os.path.join(instance_dir, "eval-info")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # output info file
    eval_info_file = os.path.join(output_dir, "eval-info.txt")
    time_info_file = os.path.join(output_dir, "time-info.txt")
    # run the plan verifier
    cmd = "ulimit -v 8388608; " "time timeout 600 " + exec_cmd + " -h " + htn_file + " -p " + plan_file + " -v " + verifier
    proc = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outs, errs = proc.communicate()
    if proc.returncode != 0:
        # some error happens
        err_info_file = os.path.join(output_dir, "err-info.txt")
        is_succeed_run = False
        with open(err_info_file, "w") as ef:
            ef.write(outs)
            ef.write(errs)
    else:
        lines = [line for line in outs.split("\n") if line]
        if lines[-1] != "The given plan is a solution":
            is_succeed_run = False
            err_info_file = os.path.join(output_dir, "err-log.txt")
            with open(err_info_file, "w") as ef:
                ef.write(outs)
                ef.write(errs)
        else:
            times = [e for e in errs.split("\n") if e]
            wallTime = times[0].split('\t')[-1]
            minutes, seconds = wallTime.split("m")[0], wallTime.split("m")[-1][:-1]
            total_seconds = float(minutes) * 60 + float(seconds)
            with open(time_info_file, "w") as tf:
                tf.write("Time in seconds: {%.3f}".format(total_seconds))
            with open(eval_info_file, "w") as of:
                of.write(outs)
    return is_succeed_run

def collect_instances():
    instance_dirs = []
    for domain in os.listdir(benchmarks_dir):
        domain_dir = os.path.join(benchmarks_dir, domain)
        for problem in os.listdir(domain_dir):
            problem_dir = os.path.join(domain_dir, problem)
            grounded_files_dir = os.path.join(problem_dir, "grounded")
            for instance in os.listdir(grounded_files_dir):
                instance_dir = os.path.join(grounded_files_dir, instance)
                instance_dirs.append(instance_dir)
    return instance_dirs

def start():
    num_succeed_instances = 0
    num_cpus = multiprocessing.cpu_count()
    print("- Number of avaliable CPUs: {}\n".format(num_cpus))
    instance_dirs = collect_instances()
    with multiprocessing.Pool(num_cpus) as p:
        imap_it = p.imap_unordered(run, instance_dirs)
        try:
            for re in imap_it:
                num_succeed_instances = num_succeed_instances + 1 if re
        except AssertionError:
            print("Assertion failed")

if __name__ == "__main__":
    start()