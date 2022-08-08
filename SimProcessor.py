__license__ = "LGPLv3"

import argparse
import subprocess
import psutil
import time


if __name__ == "__main__":

    myParser = argparse.ArgumentParser(description="Runs AFDX simulation")

    # Add the arguments
    myParser.add_argument('-omnetPath',
                          metavar="<input path>",
                          type=str,
                          help='Location of the omnetpp installation',
                          required=True)
    myParser.add_argument('-afdxPath',
                          metavar="<Output path>",
                          type=str,
                          help='Location of the AFDX model (project) and queuinglib',
                          required=True)

    args = myParser.parse_args()
    omnetpp_path = args.omnetPath
    afdx_model_path = args.afdxPath

    mingw_filename = omnetpp_path+"\\mingwenv.cmd"

    sim_exe_path = afdx_model_path + "\\afdx\\src"
    qlib_path = afdx_model_path + "\\queueinglib"
    sim_exe_name = "afdx.exe"
    sim_ini_path = afdx_model_path + "\\afdx\\simulations"
    sim_ini_name = "AutoNetwork.ini"
    sim_exe_flags = "-m -u Cmdenv -c General -n "

    script_path = sim_ini_path
    script_file_name = script_path + "\\run_ancat"

    # write script file to feed to the mingw
    with open(script_file_name, 'w') as f:
        f.write('#!/bin/sh\n')
        f.write('\n')
        f.write('echo start ...\n')
        f.write('cd `dirname $0`\n')
        f.write('PATH=/c/omnetpp-6.0/bin:/opt/mingw64/bin:../../queueinglib:"$PATH" '
                '../src/afdx.exe -m -u Cmdenv -c General -n ../src/:../../queueinglib AutoNetwork.ini\n')
        f.write('echo finish ...\n')
        #s = 'cd ' + sim_ini_path + '\n'
        #s = s.replace("C:\\", "/c/").replace("\\", "/")
        #f.write(s)
        #s = f'PATH={omnetpp_path}\\bin:\\opt\\mingw64\\bin:{qlib_path}:"$PATH" '
        #s += f'{sim_exe_path}\\{sim_exe_name} {sim_exe_flags}{sim_exe_path}:{qlib_path} '
        #s += f'{sim_ini_path}\\{sim_ini_name}\n'
        #s = s.replace("C:\\", "/c/").replace("\\", "/")
        #f.write(s)

        # count minttys in process before running
    running_bash_old = 0
    for proc in psutil.process_iter():
        if "bash" in proc.name():
            running_bash_old += 1
    # call simulation
    subprocess.call(f"{mingw_filename} {script_file_name}")

    # count minttys in process after running and wait for termination of new mintty
    running = True
    print("Waiting for 'bash.exe' to finish ", end="", flush=True)
    while running:
        time.sleep(1)
        print(".", end="", flush=True)
        running_bash_new = 0
        for proc in psutil.process_iter():
            if "bash" in proc.name():
                running_bash_new += 1
        if running_bash_new <= running_bash_old:
            running = False

    print("")
    print("'bash' finished")
