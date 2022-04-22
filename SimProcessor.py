import argparse
import subprocess

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
                          help='Location of the AFDX model (project)',
                          required=True)

    args = myParser.parse_args()
    omnetpp_path = args.omnetPath
    afdx_model_path = args.afdxPath

    omnetpp_path = "C:\\omnetpp-5.7"
    mingw_filename = omnetpp_path+"\\mingwenv.cmd"
    mingw_ancat_filename = omnetpp_path+"\\mingwenv_ancat.cmd"
    mingw_ancat_command_line = 'call "%HOME%\\tools\\win64\\msys2_shell.cmd" -mingw64'

    afdx_model_path = "C:\\omnetpp-5.7\\samples\\AFDX-Master-git"
    sim_exe_path = afdx_model_path + "\\src"
    sim_exe_name = "AFDX-Master-git.exe"
    sim_ini_path = afdx_model_path + "\\simulations"
    sim_ini_name = "AutoNetwork.ini"
    sim_exe_flags = "-m -u Cmdenv -c General -n ../src "

    script_path = sim_ini_path
    script_file_name = script_path + "\\ancat_run.sh"

    # write script file to feed to the mingw
    with open(script_file_name, 'w') as f:
        f.write('echo start ...\n')
        s = 'cd ' + sim_ini_path + '\n'
        s = s.replace("C:\\", "/c/").replace("\\", "/")
        f.write(s)
        s = f'PATH={omnetpp_path}\\bin:\\opt\\mingw64\\bin:"$PATH" '
        s += f'{sim_exe_path}\\{sim_exe_name} {sim_exe_flags} '
        s += f'{sim_ini_path}\\{sim_ini_name}\n'
        s = s.replace("C:\\", "/c/").replace("\\", "/")
        f.write(s)
        f.write('echo finish ...\n')

    # prepare mingw start script
    file = open(mingw_filename, "r")
    new_content = ""
    for line in file:
        if mingw_ancat_command_line in line:
            line = line.strip()
            new_content += line +" " + script_file_name + "\n"
        else:
            new_content += line
    file.close()
    file = open(mingw_ancat_filename, "w")
    file.write(new_content)
    file.close()

    # call simulation
    subprocess.call(mingw_ancat_filename)
