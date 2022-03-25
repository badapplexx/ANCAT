import pandas as pd

############################# PART1 #############################
########################## READ EXCEL ###########################
#################################################################
# Get: numberOfES, numberOfSW, entryList, exitsList values

# CONSTANTS AND SETTINGS
inputFileName = "Config.xlsx"
sheet1Name = "Topology"
sheet1_column1Name = "Entry"
sheet1_column2Name = "Exit"
sheet2Name = "Settings"
sheet2_column1Name = "Setting"
sheet2_column2Name = "Value"
sheet3Name = "End Systems"

iniFileName = "Network.ini"
endSystemIndicator = "ES"
switchIndicator = "SW"
networkName = "AFDXNetwork"

# SOME DECLARATIONS

iniString1Header = ""
iniString2GenNetworkParams = ""
iniString3Conndef = ""
iniString4EthernetSettings = ""
iniString5ESGeneral_numberOfs = ""
iniString6ESGeneral_TechDelays = ""
iniString7ESGeneral_skewMax = ""
iniString8ESGeneralVLQueueLength = ""
iniString9ESGeneral_defaults = ""


# get excel content
with pd.ExcelFile(inputFileName) as file:
    sheet1 = pd.read_excel(file, sheet1Name)
    sheet2 = pd.read_excel(file, sheet2Name)
    sheet3 = pd.read_excel(file, sheet3Name)

# get column one(for entry nodes) and column two(for exit nodes)
entryList = sheet1[sheet1_column1Name].values.tolist()
exitsList = sheet1[sheet1_column2Name].values.tolist()
#print(entryList)
#print(exitsList)

## SETTINGS
settingNamesList = sheet2[sheet2_column1Name].values.tolist()
settingValuesList = sheet2[sheet2_column2Name].values.tolist()

switchTechDelay = settingValuesList[settingNamesList.index("Switch Tech Delay")]
ESRxTechDelay = settingValuesList[settingNamesList.index("ES Rx Tech Delay")]
ESTxTechDelay = settingValuesList[settingNamesList.index("ES Tx Tech Delay")]
ethernetSpeed = settingValuesList[settingNamesList.index("Ethernet Speed")]
ethernetCableLength = settingValuesList[settingNamesList.index("Ethernet Cable Length")]
skewMax = settingValuesList[settingNamesList.index("Skew Max")]
vlQueueLength = settingValuesList[settingNamesList.index("VL Queue size")]

# Parameters to be filled with default values
switchSchServiceTime = "0"
def_isSkewMaxTestEnabled = "false"
def_networkID = "0x99"
def_interfaceID = "0"
def_seqNum = "0"
def_udpSrcPort = "0x1234"
def_udpDestPort = "0x5678"
def_frameHeaderLength = "47"

# Get message sets vs
endOfFile = sheet3[sheet3.isnull().all(axis=1) == True].index.tolist()[0] # get final line number
headerList = sheet3.columns.tolist()

############################# PART2 #############################
##################### CREATE and FILL *.ini #####################
### Header ###
iniString1Header = "[General]\n" "**.vector-recording = true\n" "**.scalar-recording = true"
#print(iniString1Header + "\n")

### Network Parameters ###
iniString2GenNetworkParams = "#Network Params\n"  f"network = {networkName}"
#print(iniString2GenNetworkParams + "\n")


# Connection definitions: ex. ES1<->SW1 ..
connDefEntryTypeString = "*.connDef[{}].isEntryAnEndsystem = {}"
connDefExitTypeString = "*.connDef[{}].isExitAnEndsystem = {}"
connDefEntryIndexString = "*.connDef[{}].entryIndex = {}"
connDefExitIndexString = "*.connDef[{}].exitIndex = {}"

# initialize Parameters
ESSet = set()
SWSet = set()
connDefEntryTypeStringList = []
connDefExitTypeStringList = []
connDefEntryIndexStringList = []
connDefExitIndexStringList = []

# add values(ESn, SWn) in the column to a set to count unique occurrences
# create appropriate lines for *.ini file
i = 0
for s in entryList:
    connDefEntryIndexStringList.append(connDefEntryIndexString.format(i, s[2:4]))
    if endSystemIndicator in s:
        ESSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "true"))
    elif switchIndicator in s:
        SWSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "false"))
    i += 1

i = 0
for s in exitsList:
    connDefExitIndexStringList.append(connDefExitIndexString.format(i, s[2:4]))
    if endSystemIndicator in s:
        ESSet.add(s)
        connDefExitTypeStringList.append(connDefExitTypeString.format(i, "true"))
    elif switchIndicator in s:
        SWSet.add(s)
        connDefExitTypeStringList.append(connDefExitTypeString.format(i, "false"))
    i += 1

numberOfES = len(ESSet)
numberOfSW = len(SWSet)

for s in connDefEntryIndexStringList:
    iniString3Conndef += s + "\n"
iniString3Conndef += "\n"
for s in connDefEntryTypeStringList:
    iniString3Conndef += s + "\n"
iniString3Conndef += "\n"
for s in connDefExitIndexStringList:
    iniString3Conndef += s + "\n"
iniString3Conndef += "\n"
for s in connDefExitTypeStringList:
    iniString3Conndef += s + "\n"

#print(iniString3Conndef + "\n")

iniString4EthernetSettings = f"*.ethSpeed = {ethernetSpeed}\n*.cableLength = {ethernetCableLength}"
iniString5ESGeneral_numberOfs = f"**.numberOfEndSystems = {numberOfES}\n" \
                                f"**.numberOfSwitches = {numberOfSW}"
iniString6ESGeneral_TechDelays = f"**.scheduler.serviceTime = {switchSchServiceTime}\n"\
                                 f"**.switchFabric.delay.delay = {switchTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechTx.delay = {ESTxTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechRx.delay = {ESRxTechDelay}"
iniString7ESGeneral_skewMax = f"**.redundancyChecker.skewMax = {skewMax}"
iniString8ESGeneralVLQueueLength = f"**.regulatorLogic.maxVLIDQueueSize = {vlQueueLength}"
#print(iniString4EthernetSettings)
#print(iniString5ESGeneral_numberOfs)
#print(iniString6ESGeneral_TechDelays)
#print(iniString7ESGeneral_skewMax)
#print(iniString8ESGeneralVLQueueLength + "\n")

iniString9ESGeneral_defaults = f"**.afdxMarshall[*].networkId = {def_networkID}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].interfaceId = {def_interfaceID}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].seqNum = {def_seqNum}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].udpSrcPort = {def_udpSrcPort}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].udpDestPort = {def_udpDestPort}\n"
iniString9ESGeneral_defaults += f"**.afdxMarshall[*].frameHeaderLength = {def_frameHeaderLength}\n"
iniString9ESGeneral_defaults += f"**.skewMaxTester.skewMaxTestEnabled = {def_isSkewMaxTestEnabled}"
#print(iniString9ESGeneral_defaults + "\n")


# Per end system parameters
iniStringMessageSet = [" "]*endOfFile
for rowIndex in range(endOfFile):
    esIndex = 0
    sourceIndex = 0
    row = sheet3.loc[rowIndex].values.tolist()
    for colIndex in range(len(headerList)):
        if colIndex == 0:  # col: End System
            esName = row[colIndex]
            esIndex = esName[2:4]
        if colIndex == 1:  # col: Source ID
            sourceIndex = row[colIndex]
        if colIndex == 2:  # col: Datarate of Source
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].baudrate = {row[colIndex]} "
        if colIndex == 3:  # col: Cable length
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].cableLength = {row[colIndex]} "
        if colIndex == 4:  # col: VLID
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].virtualLinkId = {row[colIndex]} "
        if colIndex == 5:  # col: startTime
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].startTime = {row[colIndex]} "
        if colIndex == 6:  # col: stopTime
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].stopTime = {row[colIndex]} "
        if colIndex == 7:  # col: BAG
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].BAG = {row[colIndex]} "
        if colIndex == 8:  # col: Period
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].interArrivalTime = {row[colIndex]} "
        if colIndex == 9:  # col: delta Period
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].deltaInterArrivalTimeMaxLimit = {row[colIndex]} "
        if colIndex == 10:  # col: Payload Length
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].packetLength = {row[colIndex]} "
        if colIndex == 11:  # col: Delta Payload Length
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].deltaPacketLengthMaxLimit = {row[colIndex]} "
        if colIndex == 12:  # col: rho
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].rho = {row[colIndex]} "
        if colIndex == 13:  # col: sigma
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].sigma = {row[colIndex]} "
        iniStringMessageSet[rowIndex] += "\n"
    #print(iniStringMessageSet[rowIndex])


# Open a file with access mode 'a'
iniFile = open(iniFileName, 'w')
# Append 'hello' at the end of file
iniFile.write(iniString1Header + "\n\n")
iniFile.write(iniString2GenNetworkParams + "\n\n")
iniFile.write(iniString3Conndef + "\n\n")
iniFile.write(iniString4EthernetSettings + "\n\n")
iniFile.write(iniString5ESGeneral_numberOfs + "\n")
iniFile.write(iniString7ESGeneral_skewMax + "\n")
iniFile.write(iniString8ESGeneralVLQueueLength + "\n")
iniFile.write(iniString6ESGeneral_TechDelays + "\n")
iniFile.write(iniString9ESGeneral_defaults + "\n")
for str in iniStringMessageSet:
    iniFile.write(str)
# Close the file
iniFile.close()



