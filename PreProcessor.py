__license__ = "LGPLv3"

import pandas as pd
from dijkstar import Graph, find_path

import argparse
import os
import sys
import glob

# CONSTANTS AND SETTINGS
import numpy

myParser = argparse.ArgumentParser(description='Creates *.ini files and config tables for the AFDX Simulation. Please specify the input excel file. '
                                                'Otherwise current directory will be searched for and first one found will be used.')

# Add the arguments
myParser.add_argument('-iPath',
                      metavar="<input path>",
                      type=str,
                      help='location of the input *.xlsx file',
                      required=False)
myParser.add_argument('-oPath',
                      metavar="<Output path>",
                      type=str,
                      help='path that *.ini file and config table(s) are needed to be located.',
                      required=False)
# Execute the parse_args() method
args = myParser.parse_args()
i = args.iPath
o = args.oPath

if i is None:
    fileList = glob.glob("*.xlsx")
    if 0 != len(fileList):
        inputDirectory = fileList[0]
        print(f">>  No *.xlsx file(-i) specified. Using \"{inputDirectory}\" located in current directory")
    else:
        print("<<No *.xlsx files in current directory, by!")
        sys.exit()
else:
    if not os.path.isfile(i):
        print(f'<<No such file as \"{i}\", by!')
        sys.exit()
    else:
        inputDirectory = i
        print(f">> input file: {inputDirectory}")
if o is None:
    print(">>  No output directory specified. Using current directory.")
    simulationDirectory = ""
else:
    if not os.path.isdir(o):
        print(f'<<No such directory as \"{o}\", by!')
        sys.exit()
    else:
        simulationDirectory = o

    if '/' != simulationDirectory[len(simulationDirectory)-1]:
        simulationDirectory += "/"
    print(f">> output directory: {simulationDirectory} \n")


############################# PART1 #############################
########################## READ EXCEL ###########################
#################################################################
# Get: numberOfES, numberOfSW, entryList, exitsList values

# CONSTANTS AND SETTINGS
copyrightNotice = "#" + "\n" + "# Copyright (C) 2022 Ipek Gokce" + "\n" + "#" + "\n" +\
                  "# SPDX-License-Identifier: LGPL-3.0-or-later" + "\n" + "#" + "\n" +\
                  "# This file is created by ANCAT." + "\n" + "#" + "\n"
iniFileName = "AutoNetwork.ini"
sheet1Name = "Topology"
sheet1_column1Name = "End1"
sheet1_column2Name = "End2"
sheet1_column3Name = "Cable length"
sheet2Name = "Settings"
sheet2_column1Name = "Setting"
sheet2_column2Name = "Value"
sheet3Name = "Message Set"
sheet3_column1Name = "Source ES"

endSystemIndicator = "ES"
switchIndicator = "SW"
networkName = "afdx.AutoNetwork"

# SOME DECLARATIONS
# iniString1Header = ""
# iniString2GenNetworkParams = ""
iniString3Conndef = ""
iniString4EthernetSpeed = ""
iniString5ESGeneral_numberOfs = ""
iniString6ESGeneral_TechDelays = ""
iniString7ESGeneral_skewMax = ""
iniString8ESGeneralVLQueueLength = ""
iniString9ESGeneral_defaults = ""


class ConnectionNode:
    def __init__(self, s):
        for c in s:
            if c.isdigit():
                self.id = int(s[s.index(c):])
                self.is_es = True if endSystemIndicator in s else False
                self.cableLength = "0m"
                break

    def __str__(self):
        return ("ES" if self.is_es else "SW")+f"{self.id}"

    def __repr__(self):
        return ("ES" if self.is_es else "SW")+f"{self.id}"

    def __eq__(self, other):
        return (self.id == other.id) and (self.is_es == other.is_es)

    def __hash__(self):
        return hash(("ES" if self.is_es else "SW") + f"{self.id}")


class MessageSet:
    def __init__(self, source_name, destination_name):
        self.source = ConnectionNode(source_name)
        destNameList = destination_name.split(",")
        self.destinationList = [ConnectionNode(x) for x in destNameList]
        self.trafficSourceID = -1
        self.vlid = ""
        self.partitionID = ""
        self.startTime = ""
        self.stopTime = ""
        self.BAG = ""
        self.period = ""
        #self.deltaPeriod = ""
        self.payloadLength = ""
        #self.deltaPayloadLength = ""
        self.rho = ""
        self.sigma = ""
        self.sourceDatarate = ""
        self.sourceCableLength = ""

    def __str__(self):
        return f"\nsource:{self.source}, vlid:{self.vlid}, payload:{self.payloadLength}"

    def __repr__(self):
        return f"\nsource:{self.source}, vlid:{self.vlid}, payload:{self.payloadLength}"


# get excel content
with pd.ExcelFile(inputDirectory) as file:
    sheet1 = pd.read_excel(file, sheet1Name, dtype=str)
    sheet2 = pd.read_excel(file, sheet2Name, dtype=str)
    sheet3 = pd.read_excel(file, sheet3Name, dtype=str)

# TOPOLOGY
entryList = sheet1[sheet1_column1Name].values.tolist()
exitsList = sheet1[sheet1_column2Name].values.tolist()
cableLengthList = sheet1[sheet1_column3Name].values.tolist()

## SETTINGS
settingNamesList = sheet2[sheet2_column1Name].values.tolist()
settingValuesList = sheet2[sheet2_column2Name].values.tolist()

# get actual values
switchTechDelay = settingValuesList[settingNamesList.index("Switch Tech Delay")]
ESRxTechDelay = settingValuesList[settingNamesList.index("ES Rx Tech Delay")]
ESTxTechDelay = settingValuesList[settingNamesList.index("ES Tx Tech Delay")]
ethernetSpeed = settingValuesList[settingNamesList.index("Ethernet Speed")]
#ethernetCableLength = settingValuesList[settingNamesList.index("Ethernet Cable Length")]
skewMax = settingValuesList[settingNamesList.index("Skew Max")]
vlQueueLength = settingValuesList[settingNamesList.index("VL Queue size")]

# Parameters to be filled with default values
switchSchServiceTime = "0s"
def_isSkewMaxTestEnabled = "false"
def_networkID = "0x99"
def_equipmentID = "0x66"
def_interfaceID = "0"
def_seqNum = "0"
def_udpSrcPort = "0x1234"
def_udpDestPort = "0x5678"
def_frameHeaderLength = "47"

# MESSAGE SETS

endOfFile = sheet3[sheet3.isnull().all(axis=1) == True].index.tolist()[0]  # get final line number
headerList = sheet3.columns.tolist()

sourceNameColumn = (sheet3[sheet3_column1Name].values.tolist())[0:endOfFile]
# UniqEndSystemNameList = pd.unique((sheet3[sheet3_column1Name].values.tolist())[0:endOfFile])
UniqEndSystemNameList1 = (pd.unique((sheet1[sheet1_column1Name].values.tolist())[0:endOfFile])).tolist()
UniqEndSystemNameList2 = (pd.unique((sheet1[sheet1_column2Name].values.tolist())[0:endOfFile])).tolist()
UniqEndSystemNameList = set(UniqEndSystemNameList1+ UniqEndSystemNameList2)

############################# PART2 #############################
##################### CREATE and FILL *.ini #####################
### Header ###
iniString1Header = copyrightNotice + \
                   "[General]\n" +\
                   "print-undisposed = false\n" + \
                   "**.vector-recording = true\n" + \
                   "**.scalar-recording = true\n" + \
                   "**.queueLength.statistic-recording = false\n" + \
                   "**.lifeTime.statistic-recording = false\n"

### Network Parameters ###
iniString2GenNetworkParams = "#Network Params\n"  f"network = {networkName}"
# ==========================================
connGraph = Graph()
connList = []
ESSet = set()
SWSet = set()
for e in range(len(entryList)):
    entryNode = ConnectionNode(entryList[e])
    exitNode = ConnectionNode(exitsList[e])
    connGraph.add_edge(entryNode, exitNode, 1)
    connGraph.add_edge(exitNode, entryNode, 1)
    ESSet.add(entryNode) if entryNode.is_es else SWSet.add(entryNode)
    ESSet.add(exitNode) if exitNode.is_es else SWSet.add(exitNode)
    connList.append([entryNode, exitNode, cableLengthList[e]])

stringEntryIDs = ""
stringExitIDs = ""
stringIsEntryES = ""
stringIsExitES = ""
stringCableLength = ""
i = 0
for cit in connList:
    stringEntryIDs += f"*.connDef[{i}].entryIndex = {cit[0].id}\n"
    stringExitIDs += f"*.connDef[{i}].exitIndex = {cit[1].id}\n"
    stringIsEntryES += "*.connDef[{}].isEntryAnEndsystem = {}\n".format(i, "true" if cit[0].is_es else "false")
    stringIsExitES += "*.connDef[{}].isExitAnEndsystem = {}\n".format(i, "true" if cit[1].is_es else "false")
    stringCableLength += f"*.connDef[{i}].cableLength = {cit[2]}\n"
    i += 1

iniString3Conndef = stringEntryIDs + "\n" + stringExitIDs + "\n" + stringIsEntryES + "\n" + stringIsExitES + "\n" + stringCableLength
# ==========================================
iniString4EthernetSpeed = f"*.ethSpeed = {ethernetSpeed}\n"
iniString5ESGeneral_numberOfs = f"**.numberOfEndSystems = {len(ESSet)}\n" \
                                f"**.numberOfSwitches = {len(SWSet)}"
iniString6ESGeneral_TechDelays = f"**.scheduler.serviceTime = {switchSchServiceTime}\n" \
                                 f"**.switchFabric.delay.delay = {switchTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechTx.delay = {ESTxTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechRx.delay = {ESRxTechDelay}"
iniString7ESGeneral_skewMax = f"**.redundancyChecker.skewMax = {skewMax}"
iniString8ESGeneralVLQueueLength = f"**.regulatorLogic.maxVLIDQueueSize = {vlQueueLength}"
# ==========================================
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].networkId = {def_networkID}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].equipmentId = {def_equipmentID}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].interfaceId = {def_interfaceID}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].seqNum = {def_seqNum}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].udpSrcPort = {def_udpSrcPort}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].udpDestPort = {def_udpDestPort}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].frameHeaderLength = {def_frameHeaderLength}\n"
iniString9ESGeneral_defaults += f"**.skewMaxTester.skewMaxTestEnabled = {def_isSkewMaxTestEnabled}"
# ==========================================
# Per end system parameters
# message counts

UniqEndSystemNameList_ES = [x for x in UniqEndSystemNameList if "ES" in x]
UniqEndSystemNameList_ES.sort()

iniStringMessageCount = [" "] * len(UniqEndSystemNameList_ES)
for es in UniqEndSystemNameList_ES:
    ix = int(es[2:4])
    iniStringMessageCount[ix] = f"**.ESGroup[{ix}].messageCount = {sourceNameColumn.count(es)}\n"
# ==========================================
#
# other details


def fillEndSystemInfo(row, column_length):
    esInfo = MessageSet(row[0], row[1])
    esInfo.vlid = str(row[2])
    esInfo.partitionID = str(row[3])
    esInfo.startTime = str(row[4])
    esInfo.stopTime = str(row[5])
    esInfo.BAG = str(row[6])
    esInfo.period = str(row[7])
    #esInfo.deltaPeriod = str(row[8])
    esInfo.payloadLength = str((row[8]))
   #esInfo.deltaPayloadLength = int(row[10])
    esInfo.rho = str(row[9])
    esInfo.sigma = str(row[10])
    esInfo.sourceDatarate = str(row[11])
    esInfo.sourceCableLength = str(row[12])
    return esInfo

ESInfoList = []
for rowIndex in range(endOfFile):
    row = sheet3.loc[rowIndex].values.tolist()
    temp = fillEndSystemInfo(row, len(headerList))
    cnt = 0
    for e in ESInfoList:
        if e.source.id == temp.source.id:
            cnt += 1
    temp.trafficSourceID = cnt
    ESInfoList.append(temp)

iniStringMessageSet = [""] * endOfFile
for e in ESInfoList:
    rowIndex = ESInfoList.index(e)
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].afdxMarshall[{e.trafficSourceID}].rho = {e.rho}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].afdxMarshall[{e.trafficSourceID}].sigma = {e.sigma}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].afdxMarshall[{e.trafficSourceID}].BAG = {e.BAG}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].afdxMarshall[{e.trafficSourceID}].virtualLinkId = {e.vlid}\n"
    #iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].afdxMarshall[{e.trafficSourceID}].deltaPacketLengthMaxLimit = {e.deltaPayloadLength}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].partitionId = {e.partitionID}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].startTime = {e.startTime}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].stopTime = {e.stopTime}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].interArrivalTime = {e.period}\n"
    #iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].deltaInterArrivalTimeMaxLimit = {e.deltaPeriod}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].packetLength = {e.payloadLength}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].baudrate = {e.sourceDatarate}\n"
    iniStringMessageSet[rowIndex] += f"**.ESGroup[{e.source.id}].messageSource[{e.trafficSourceID}].cableLength = {e.sourceCableLength}\n"
    iniStringMessageSet[rowIndex] += "\n"
#print(iniStringMessageSet)

# ==========================================
# Open file and append strings
iniFile = open(simulationDirectory + iniFileName, 'w')
iniFile.write(iniString1Header + "\n\n")
iniFile.write(iniString2GenNetworkParams + "\n\n")
iniFile.write(iniString3Conndef + "\n\n")
iniFile.write(iniString4EthernetSpeed + "\n\n")
iniFile.write(iniString5ESGeneral_numberOfs + "\n")
iniFile.write(iniString7ESGeneral_skewMax + "\n")
iniFile.write(iniString8ESGeneralVLQueueLength + "\n")
iniFile.write(iniString6ESGeneral_TechDelays + "\n")
iniFile.write(iniString9ESGeneral_defaults + "\n\n")
for s in iniStringMessageCount:
    iniFile.write(s)
for s in iniStringMessageSet:
    iniFile.write(s)
# Close the file
iniFile.close()
############################# PART3 #############################
################# CREATE and FILL config tables #################
iniStringConfigTable = ""

for s in SWSet:
    registeredVLs = []
    fileName = f"{s}.txt"
    f = open(simulationDirectory + fileName, "w")
    f.write(f"*** VL ID - Ports Mapping for Switch {s.id} ***\n")
    for e in ESInfoList:
        ports = set()
        psource = find_path(connGraph, s, e.source)
        psource_node = psource.nodes[1]
        for c in connList:
            if ((c[0] == s) and (c[1] == psource_node)) or ((c[0] == psource_node) and (c[1] == s)):
                source_index = connList.index(c)
        for d in e.destinationList:
            p = find_path(connGraph, s, d)
            first_node = p.nodes[1]
            for c in connList:
                if ((c[0] == s) and (c[1] == first_node)) or ((c[0] == first_node) and (c[1] == s)):
                    dest_index = connList.index(c)
                    if source_index != dest_index:
                        ports.add(dest_index)
                    break
        if len(ports) != 0 and e.vlid not in registeredVLs:
            f.write(f"{e.vlid} : {ports}\n")
            registeredVLs.append(e.vlid)

    f.close()
    print(">>" + simulationDirectory + fileName + " is created")
    iniStringConfigTable += f"*.SwitchA[{s.id}].switchFabric.router.configTableName = \"{fileName}\"\n"
    iniStringConfigTable += f"*.SwitchB[{s.id}].switchFabric.router.configTableName = \"{fileName}\"\n"

iniFile = open(simulationDirectory + iniFileName, 'a')
iniFile.write("\n" + iniStringConfigTable)
iniFile.close()
print(">>" + simulationDirectory + iniFileName + " is created.\n")
