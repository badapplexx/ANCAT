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
iniFileName = "Network.ini"
endSystemIndicator = "ES"
switchIndicator = "SW"
networkName = "AFDXNetwork"

# SOME DECLARATIONS
# flags for optional(?) ini lines
createConTypeLines = True
iniString1Header = ""
iniString2GenNetworkParams = ""
iniString3EthernetSettings = ""
iniString4Conndef = ""
iniString5ESGeneral_numberOfs = ""
iniString6ESGeneral_skewMax = ""
iniString8ESGeneral_defaults = ""
iniString7ESGeneral_TechDelays = ""

iniStringESMarshal_defaults = ""

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


# get excel content for sheet: "Topology"
with pd.ExcelFile(inputFileName) as file:
    topology = pd.read_excel(file, sheet1Name)

# get column one(for entry nodes) and column two(for exit nodes)
entryList = topology[sheet1_column1Name].values.tolist()
exitsList = topology[sheet1_column2Name].values.tolist()
ethernetSpeed = "100Mbps"
ethernetCableLength = "10m"
skewMax = "10ms"
ESRxTechDelay = "32ms"
ESTxTechDelay = "32ms"

def_isSkewMaxTestEnabled = "false"

def_networkID = "0x99"
def_interfaceID = "0"
def_seqNum = "0"
def_udpSrcPort = "0x1234"
def_udpDestPort = "0x5678"
frameHeaderLength = "47"

print(entryList)
print(exitsList)

############################# PART2 #############################
##################### CREATE and FILL *.ini #####################
### Header ###
iniString1Header = "[General]\n" "**.vector-recording = true\n" "**.scalar-recording = true\n"
print(iniString1Header)

### Network Parameters ###
iniString2GenNetworkParams = "#Network Params\n"  f"network = {networkName}\n"
print(iniString2GenNetworkParams)
iniString3EthernetSettings = f"*.ethSpeed = {ethernetSpeed}\n*.cableLength = {ethernetCableLength}\n"
print(iniString3EthernetSettings)

### Connection definitions: ex. ES1<->SW1 .. ###
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
    iniString4Conndef += s
    iniString4Conndef += "\n"
iniString4Conndef += "\n"
for s in connDefEntryTypeStringList:
    iniString4Conndef += s
    iniString4Conndef += "\n"
iniString4Conndef += "\n"
for s in connDefExitIndexStringList:
    iniString4Conndef += s
    iniString4Conndef += "\n"
iniString4Conndef += "\n"
for s in connDefExitTypeStringList:
    iniString4Conndef += s
    iniString4Conndef += "\n"
iniString4Conndef += "\n"
#print(iniString4Conndef)

### ES Parameters ###

# General
iniString5ESGeneral_numberOfs = f"#ES Params\n**.numberOfEndSystems = {numberOfES}\n**.numberOfSwitches = {numberOfSW}"
iniString6ESGeneral_skewMax = f"**.redundancyChecker.skewMax = {skewMax}"
iniString7ESGeneral_TechDelays = f"**.ESGroup[*].latencyTechTx.delay = {ESTxTechDelay}\n**.ESGroup[*].latencyTechRx.delay = {ESRxTechDelay}"
iniString8ESGeneral_defaults = f"**.skewMaxTester.skewMaxTestEnabled = {def_isSkewMaxTestEnabled}\n"
print(iniString5ESGeneral_numberOfs)
print(iniString6ESGeneral_skewMax)
print(iniString7ESGeneral_TechDelays)
print(iniString8ESGeneral_defaults)


iniStringESMarshal_defaults = f"**.afdxMarshall[*].networkId = {def_networkID}\n"
iniStringESMarshal_defaults += f"**.afdxMarshall[*].interfaceId = {def_interfaceID}\n"
iniStringESMarshal_defaults += f"**.afdxMarshall[*].seqNum = {def_seqNum}\n"
iniStringESMarshal_defaults += f"**.afdxMarshall[*].udpSrcPort = {def_udpSrcPort}\n"
iniStringESMarshal_defaults += f"**.afdxMarshall[*].udpDestPort = {def_udpDestPort}\n"
iniStringESMarshal_defaults += f"**.afdxMarshall[*].frameHeaderLength = {frameHeaderLength}\n"
print(iniStringESMarshal_defaults)
# Per trafficSource parameters



