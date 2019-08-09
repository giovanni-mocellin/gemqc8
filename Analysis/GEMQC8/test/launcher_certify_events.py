import csv
import os
import sys
import io
import subprocess
import time
import datetime

if __name__ == '__main__':

    run_number = sys.argv[1]

    # Different paths definition
    srcPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0]+'QC8Test/src/'
    pyhtonModulesPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0]+'QC8Test/src/Analysis/GEMQC8/python/'
    runPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0] + 'QC8Test/src/Analysis/GEMQC8/test/'
    configTablesPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0] + 'QC8Test/src/Analysis/GEMQC8/data/StandConfigurationTables/'
    alignmentTablesPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0] + 'QC8Test/src/Analysis/GEMQC8/data/StandAligmentTables/'
    certEvtsTablesPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0] + 'QC8Test/src/Analysis/GEMQC8/data/CertifiedEvents/'
    resDirPath = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0]

    sys.path.insert(0,pyhtonModulesPath)

    import dumpDBtables
    import config_creator
    import geometry_files_creator

    # Retrieve start date and time of the run
    fpath =  "/eos/cms/store/group/dpg_gem/comm_gem/QC8_Commissioning/run{:06d}/".format(int(run_number))
    for x in os.listdir(fpath):
        if x.endswith("ls0001_index000000.raw"):
            file0name = x
            break
        elif x.endswith("chunk_000000.dat"):
            file0name = x
            break
        else:
            print "Check the data files... First file (at least) is missing!"
    startDateTime = file0name.split('_')[3] + "_" + file0name.split('_')[4]
    time.sleep(1)

    # Get stand configuration table from the DB
    if int(run_number) >= 224:
        dumpDBtables.getConfigurationTable(run_number,startDateTime)

    # Generate configuration file
    config_creator.configMaker(run_number)
    time.sleep(1)

    # Generate geometry files
    geometry_files_creator.geomMaker(run_number,"--noAlignment")
    time.sleep(1)

    # Compiling after the generation of the geometry files
    scramCommand = "scram build -j 4"
    scramming = subprocess.Popen(scramCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=srcPath)
    while scramming.poll() is None:
        line = scramming.stdout.readline()
        print(line)
    print scramming.stdout.read()
    scramming.communicate()
    time.sleep(1)

    # Running the CMSSW code
    runCommand = "cmsRun -n 8 runGEMCosmicStand_certify_events.py"
    running = subprocess.Popen(runCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=runPath)
    while running.poll() is None:
        line = running.stdout.readline()
        print(line)
    print running.stdout.read()
    running.communicate()
    time.sleep(1)

    #  # Creating folder outside the CMMSW release to put the output files and plots
    outDirName = "Results_QC8_certify_events_run_"+run_number
    #---# Remove old version if want to recreate
    if (os.path.exists(resDirPath+outDirName)):
        rmDirCommand = "rm -rf "+outDirName
        rmDir = subprocess.Popen(rmDirCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=resDirPath)
        rmDir.communicate()
    #---# Create the new empty folder
    resDirCommand = "mkdir "+outDirName
    resDir = subprocess.Popen(resDirCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=resDirPath)
    resDir.communicate()
    time.sleep(1)

    # Selecting the correct output file, changing the name and moving to the output folder
    out_name = 'out_run_'
    for i in range(6-len(run_number)):
        out_name = out_name + '0'
    out_name = out_name + run_number + '.root'

    mvToDirCommand = "mv certify_events_" + out_name + " " + resDirPath+outDirName + "/certify_events_" + out_name
    movingToDir = subprocess.Popen(mvToDirCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=runPath)
    movingToDir.communicate()
    time.sleep(1)

    # Efficiency computation & output
    effoutDir = os.path.abspath("launcher_certify_events.py").split('QC8Test')[0] + outDirName
    effCommand = "root -l -q " + runPath + "macro_certify_events.c(" + run_number + ",\"" + configTablesPath + "\")"
    efficiency = subprocess.Popen(effCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=effoutDir)
    while efficiency.poll() is None:
        line = efficiency.stdout.readline()
        print(line)
    print efficiency.stdout.read()
    efficiency.communicate()
    time.sleep(1)

    # Moving the output of the root analysis to the folder in GEMQC8/data/..
    out_name = 'CertifiedEvents_run' + run_number + '.csv'
    mvToDirCommand = "cp " + effoutDir + "/" + out_name + " " + certEvtsTablesPath + out_name
    movingToDir = subprocess.Popen(mvToDirCommand.split(),stdout=subprocess.PIPE,universal_newlines=True,cwd=runPath)
    movingToDir.communicate()
    time.sleep(1)
