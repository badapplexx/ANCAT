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
sheet3_column1Name = "End System"

iniFileName = "AutoNetwork.ini"
#iniFileName = "C:\\Workspaces\\Github\\AFDX\\simulations\\AutoNetwork.ini"
endSystemIndicator = "ES"
switchIndicator = "SW"
networkName = "Deneme"

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


class Node:
    def __init__(self, node_id, is_es, connected_node_id, is_connected_node_es):
        self.nodeID = node_id
        self.isES = is_es
        self.connectedNodeID = connected_node_id
        self.isConnectedNodeES = is_connected_node_es


class EndSystem(Node):
    def __init__(self, id):
        self.sourceID = ""
        self.sourceDatarate = ""
        self.sourceCableLength = ""
        self.vlid = ""
        self.startTime = ""
        self.stopTime = ""
        self.BAG = ""
        self.period = ""
        self.deltaPeriod = ""
        self.payloadLength = ""
        self.deltaPayloadLength = ""
        self.rho = ""
        self.sigma = ""
        Node.__init__(self)


# get excel content
with pd.ExcelFile(inputFileName) as file:
    sheet1 = pd.read_excel(file, sheet1Name)
    sheet2 = pd.read_excel(file, sheet2Name)
    sheet3 = pd.read_excel(file, sheet3Name)

# TOPOLOGY
entryList = sheet1[sheet1_column1Name].values.tolist()
exitsList = sheet1[sheet1_column2Name].values.tolist()

## SETTINGS
settingNamesList = sheet2[sheet2_column1Name].values.tolist()
settingValuesList = sheet2[sheet2_column2Name].values.tolist()

# get actual values
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
def_equipmentID = "0x66"
def_interfaceID = "0"
def_seqNum = "0"
def_udpSrcPort = "0x1234"
def_udpDestPort = "0x5678"
def_frameHeaderLength = "47"

# MESSAGE SETS
endOfFile = sheet3[sheet3.isnull().all(axis=1) == True].index.tolist()[0]  # get final line number
headerList = sheet3.columns.tolist()

endSystemNamesList = (sheet3[sheet3_column1Name].values.tolist())[0:endOfFile]
UniqEndSystemNameList = pd.unique((sheet3[sheet3_column1Name].values.tolist())[0:endOfFile])

# a = len(pd.unique((sheet3[sheet3_column1Name].values.tolist())[0:endOfFile]))  # for messageCount values, count unique ES names

############################# PART2 #############################
##################### CREATE and FILL *.ini #####################
### Header ###
iniString1Header = "[General]\n" "**.vector-recording = true\n" "**.scalar-recording = true"

### Network Parameters ###
iniString2GenNetworkParams = "#Network Params\n"  f"network = {networkName}"

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
# ==========================================
# add values(ESn, SWn) in the column to a set to count unique occurrences
nodes = []
numberOfSW = 0
numberOfES = 0

for k in range(len(entryList)):
    entryNode = entryList[k]
    exitNode = exitsList[k]
    if endSystemIndicator in entryNode:  # entryNode is an ES
        ESSet.add(entryNode)
        if endSystemIndicator in exitNode: # exitNode is an ES
            nodes.append(Node(entryNode[2:4], True, exitNode[2:4], True))
            ESSet.add(exitNode)
        elif switchIndicator in exitNode:   # exitNode a SW
            nodes.append(Node(entryNode[2:4], True, exitNode[2:4], False))
            SWSet.add(exitNode)
    elif switchIndicator in entryNode:  # entryNode is an SW
        SWSet.add(entryNode)
        if endSystemIndicator in exitNode: # exitNode is an ES
            nodes.append(Node(entryNode[2:4], False, exitNode[2:4], True))
            ESSet.add(exitNode)
        elif switchIndicator in exitNode:   # exitNode a SW
            nodes.append(Node(entryNode[2:4], False, exitNode[2:4], False))
            SWSet.add(exitNode)
numberOfSW = len(SWSet)
numberOfES = len(ESSet)

entryIDs = ""
exitIDs = ""
isEntryES = ""
isExitES = ""
i = 0
for n in nodes:
    entryIDs += f"*.connDef[{i}].entryIndex = {n.nodeID}\n"
    exitIDs += f"*.connDef[{i}].exitIndex = {n.connectedNodeID}\n"
    isEntryES += "*.connDef[{}].isEntryAnEndsystem = {}\n".format(i, "true" if n.isES == True else "false")
    isExitES += "*.connDef[{}].isExitAnEndsystem = {}\n".format(i, "true" if n.isConnectedNodeES == True else "false")
    i += 1

iniString3Conndef = entryIDs + "\n" + exitIDs + "\n" + isEntryES + "\n" + isExitES
# ==========================================
iniString4EthernetSettings = f"*.ethSpeed = {ethernetSpeed}\n*.cableLength = {ethernetCableLength}"
iniString5ESGeneral_numberOfs = f"**.numberOfEndSystems = {numberOfES}\n" \
                                f"**.numberOfSwitches = {numberOfSW}"
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
iniStringMessageCount = [" "] * len(UniqEndSystemNameList)
for es in UniqEndSystemNameList:
    ix = int(es[2:4])
    iniStringMessageCount[ix] = f"**.ESGroup[{ix}].messageCount = {endSystemNamesList.count(es)}\n"
# ==========================================
#
# other details

def fillEndSystemInfo(row, column_length):
    i = 0
    for colIndex in range(column_length):
        if colIndex == 0:  # col: End System
            esName = row[colIndex]
            esInfo = EndSystem(esName[2:4])
        if colIndex == 1:  # col: Source ID
            esInfo.sourceID = row[colIndex]
        if colIndex == 2:  # col: Datarate of Source
            esInfo.sourceDatarate  = row[colIndex]
        if colIndex == 3:  # col: Cable length
            esInfo.sourceCableLength  = row[colIndex]
        if colIndex == 4:  # col: VLID
            esInfo.vlid = row[colIndex]
        if colIndex == 5:  # col: startTime
            esInfo.startTime = row[colIndex]
        if colIndex == 6:  # col: stopTime
            esInfo.stopTime = row[colIndex]
        if colIndex == 7:  # col: BAG
            esInfo.BAG = row[colIndex]
        if colIndex == 8:  # col: Period
            esInfo.period = row[colIndex]
        if colIndex == 9:  # col: delta Period
            esInfo.deltaPeriod = row[colIndex]
        if colIndex == 10:  # col: Payload Length
            esInfo.payloadLength = row[colIndex]
        if colIndex == 11:  # col: Delta Payload Length
            esInfo.deltaPayloadLength = row[colIndex]
        if colIndex == 12:  # col: rho
            esInfo.rho = row[colIndex]
        if colIndex == 13:  # col: sigma
            esInfo.sigma = row[colIndex]
        i += i
    return esInfo


ESInfoList = []
for rowIndex in range(endOfFile):
    row = sheet3.loc[rowIndex].values.tolist()
    ESInfoList.append(fillEndSystemInfo(row, len(headerList)))

datarateStr = ""
cableLenStr = ""
for e in ESInfoList:
    datarateStr += f"**.ESGroup[{e.nodeID}].trafficSource[{e.sourceID}].baudrate = {e.sourceDatarate}\n"
    cableLenStr += f"**.ESGroup[{e.nodeID}].trafficSource[{e.sourceID}].cableLength = {e.sourceCableLength}\n"

print(datarateStr)
print(cableLenStr)

iniStringMessageSet = [""] * endOfFile
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
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].baudrate = {row[colIndex]} "
        if colIndex == 3:  # col: Cable length
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].cableLength = {row[colIndex]} "
        if colIndex == 4:  # col: VLID
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].virtualLinkId = {row[colIndex]}\n "
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].partitionId = {row[colIndex]} "
        if colIndex == 5:  # col: startTime
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].startTime = {row[colIndex]} "
        if colIndex == 6:  # col: stopTime
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].stopTime = {row[colIndex]} "
        if colIndex == 7:  # col: BAG
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].BAG = {row[colIndex]} "
        if colIndex == 8:  # col: Period
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].interArrivalTime = {row[colIndex]} "
        if colIndex == 9:  # col: delta Period
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].deltaInterArrivalTimeMaxLimit = {row[colIndex]} "
        if colIndex == 10:  # col: Payload Length
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].trafficSource[{sourceIndex}].packetLength = {row[colIndex]} "
        if colIndex == 11:  # col: Delta Payload Length
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].deltaPacketLengthMaxLimit = {row[colIndex]} "
        if colIndex == 12:  # col: rho
            iniStringMessageSet[rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].rho = {row[colIndex]} "
        if colIndex == 13:  # col: sigma
            iniStringMessageSet[
                rowIndex] += f"**.ESGroup[{esIndex}].afdxMarshall[{sourceIndex}].sigma = {row[colIndex]} "
        iniStringMessageSet[rowIndex] += "\n"
# ==========================================
# Open file and append strings
iniFile = open(iniFileName, 'w')
iniFile.write(iniString1Header + "\n\n")
iniFile.write(iniString2GenNetworkParams + "\n\n")
iniFile.write(iniString3Conndef + "\n\n")
iniFile.write(iniString4EthernetSettings + "\n\n")
iniFile.write(iniString5ESGeneral_numberOfs + "\n")
iniFile.write(iniString7ESGeneral_skewMax + "\n")
iniFile.write(iniString8ESGeneralVLQueueLength + "\n")
iniFile.write(iniString6ESGeneral_TechDelays + "\n")
iniFile.write(iniString9ESGeneral_defaults + "\n\n")
for str in iniStringMessageCount:
    iniFile.write(str)
for str in iniStringMessageSet:
    iniFile.write(str)
# Close the file
iniFile.close()

# =========================================