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
Sheet3_column1 = "End Systems"
Sheet3_column2 = "Source ID"
Sheet3_column3 = "Datarate of source"
Sheet3_column4 = "Cable Length"
Sheet3_column5 = "VLID"
Sheet3_column6 = "startTime"
Sheet3_column7 = "stopTime"
Sheet3_column8 = "BAG"
Sheet3_column9 = "Payload Length"
Sheet3_column10 = "Delta Payload Length"
Sheet3_column11 = "Period"
Sheet3_column12 = "Delta Period"
Sheet3_column13 = "rho"
Sheet3_column14 = "sigma"

iniFileName = "Network.ini"
endSystemIndicator = "ES"
switchIndicator = "SW"
networkName = "AFDXNetwork"

# SOME DECLARATIONS
# flags for optional(?) ini lines
createConTypeLines = True
iniString1Header = ""
iniString2GenNetworkParams = ""
iniString5EthernetSettings = ""
iniString4Conndef = ""
iniString6ESGeneral_numberOfs = ""
iniString8ESGeneral_skewMax = ""
iniString9ESGeneralVLQueueLength = ""
iniString10ESGeneral_defaults = ""
iniString7ESGeneral_TechDelays = ""

iniStringES_MessageCounts = ""
iniStringES_Datarates = ""
iniStringES_CableLengths = ""
iniStringES_VLIDs = ""
iniStringES_StartTimes = ""
iniStringES_StopTimes = ""
iniStringES_BAGs = ""
iniStringES_Payloads = ""
iniStringES_PayloadDeltas = ""
iniStringES_Rho = ""
iniStringES_Sigma = ""


# get excel content for sheet: "Topology" and "Settings"
with pd.ExcelFile(inputFileName) as file:
    sheet1 = pd.read_excel(file, sheet1Name)
    sheet2 = pd.read_excel(file, sheet2Name)
    sheet3 = pd.read_excel(file, sheet3Name)

# get column one(for entry nodes) and column two(for exit nodes)
entryList = sheet1[sheet1_column1Name].values.tolist()
exitsList = sheet1[sheet1_column2Name].values.tolist()
print(entryList)
print(exitsList)
# get settings
settingNamesList = sheet2[sheet2_column1Name].values.tolist()
settingValuesList = sheet2[sheet2_column2Name].values.tolist()

switchTechDelay = settingValuesList[settingNamesList.index("Switch Tech Delay")]  # "4us"
switchSchServiceTime = "0"
ESRxTechDelay = settingValuesList[settingNamesList.index("ES Rx Tech Delay")]  # "32ms"
ESTxTechDelay = settingValuesList[settingNamesList.index("ES Tx Tech Delay")]  # "32ms"
ethernetSpeed = settingValuesList[settingNamesList.index("Ethernet Speed")]  # "100Mbps"
ethernetCableLength = settingValuesList[settingNamesList.index("Ethernet Cable Length")]  # "10m"
skewMax = settingValuesList[settingNamesList.index("Skew Max")]  # "10ms"
vlQueueLength = settingValuesList[settingNamesList.index("VL Queue size")]  # "1000"
# Parameters to be filled with default values
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
iniStringMessageSet = [" "]*endOfFile

for rowIndex in range(endOfFile):
    esIndex = 0
    sourceIndex = 0
    row = sheet3.loc[rowIndex].values.tolist()
    for colIndex in range(len(headerList)):
        if colIndex == 0:  # col: End System
            esName = row[colIndex]
            esIndex = esName[2:3]
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
    print(iniStringMessageSet[rowIndex])
print("over")
############################# PART2 #############################
##################### CREATE and FILL *.ini #####################
### Header ###
iniString1Header = "[General]\n" "**.vector-recording = true\n" "**.scalar-recording = true"
print(iniString1Header + "\n")

### Network Parameters ###
iniString2GenNetworkParams = "#Network Params\n"  f"network = {networkName}"
print(iniString2GenNetworkParams + "\n")


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
    connDefEntryIndexStringList.append(connDefEntryIndexString.format(i, s[2:3]))
    if endSystemIndicator in s:
        ESSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "true"))
    elif switchIndicator in s:
        SWSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "false"))
    i += 1

i = 0
for s in exitsList:
    connDefExitIndexStringList.append(connDefExitIndexString.format(i, s[2:3]))
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
    iniString4Conndef += s + "\n"
iniString4Conndef += "\n"
for s in connDefEntryTypeStringList:
    iniString4Conndef += s + "\n"
iniString4Conndef += "\n"
for s in connDefExitIndexStringList:
    iniString4Conndef += s + "\n"
iniString4Conndef += "\n"
for s in connDefExitTypeStringList:
    iniString4Conndef += s + "\n"

print(iniString4Conndef + "\n")

iniString5EthernetSettings = f"*.ethSpeed = {ethernetSpeed}\n*.cableLength = {ethernetCableLength}"
iniString6ESGeneral_numberOfs = f"**.numberOfEndSystems = {numberOfES}\n" \
                                f"**.numberOfSwitches = {numberOfSW}"
iniString7ESGeneral_TechDelays = f"**.scheduler.serviceTime = {switchSchServiceTime}\n"\
                                 f"**.switchFabric.delay.delay = {switchTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechTx.delay = {ESTxTechDelay}\n" \
                                 f"**.ESGroup[*].latencyTechRx.delay = {ESRxTechDelay}"
iniString8ESGeneral_skewMax = f"**.redundancyChecker.skewMax = {skewMax}"
iniString9ESGeneralVLQueueLength = f"**.regulatorLogic.maxVLIDQueueSize = {vlQueueLength}"
print(iniString5EthernetSettings)
print(iniString6ESGeneral_numberOfs)
print(iniString7ESGeneral_TechDelays)
print(iniString8ESGeneral_skewMax)
print(iniString9ESGeneralVLQueueLength + "\n")

iniString10ESGeneral_defaults = f"**.afdxMarshall[*].networkId = {def_networkID}\n"
iniString10ESGeneral_defaults += f"**.afdxMarshall[*].interfaceId = {def_interfaceID}\n"
iniString10ESGeneral_defaults += f"**.afdxMarshall[*].seqNum = {def_seqNum}\n"
iniString10ESGeneral_defaults += f"**.afdxMarshall[*].udpSrcPort = {def_udpSrcPort}\n"
iniString10ESGeneral_defaults += f"**.afdxMarshall[*].udpDestPort = {def_udpDestPort}\n"
iniString10ESGeneral_defaults += f"**.afdxMarshall[*].frameHeaderLength = {def_frameHeaderLength}\n"
iniString10ESGeneral_defaults += f"**.skewMaxTester.skewMaxTestEnabled = {def_isSkewMaxTestEnabled}\n"
print(iniString10ESGeneral_defaults)
# Per trafficSource parameters



