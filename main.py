import pandas as pd

# PART1: Get from excel -> numberOfES, numberOfSW, entryList, exitsList

# constants
inputFileName = "Config.xlsx"
sheet1Name = "Topology"
sheet1_column1Name = "Entry"
sheet1_column2Name = "Exit"

# get excel content for sheet: "Topology"
with pd.ExcelFile(inputFileName) as file:
    topology = pd.read_excel(file, sheet1Name)

# get column one(node ones) and column two(node twos)
entryList = topology[sheet1_column1Name].values.tolist()
exitsList = topology[sheet1_column2Name].values.tolist()

print(entryList)
print(exitsList)
#################################################################33

connDefEntryTypeString = "*.connDef[{}].isEntryAnEndsystem = {}"
connDefExitTypeString = "*.connDef[{}].isExitAnEndsystem = {}"
connDefEntryIndexString = "*.connDef[{}].entryIndex = {}"
connDefExitIndexString = "*.connDef[{}].exitIndex = {}"

# numberOfES = sum(1 for s in entryList if 'ES' in s) + sum(1 for s in exitsList if 'ES' in s)
# add ES names to a set to count unique occurrences
ESSet = set()
SWSet = set()

i = 0
connDefEntryTypeStringList = []
connDefExitTypeStringList = []
connDefEntryIndexStringList = []
connDefExitIndexStringList = []

for s in entryList:
    connDefEntryIndexStringList.append(connDefEntryIndexString.format(i, s[2:3]))
    if 'ES' in s:
        ESSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "true"))
    elif 'SW' in s:
        SWSet.add(s)
        connDefEntryTypeStringList.append(connDefEntryTypeString.format(i, "false"))
    i += 1

i = 0
for s in exitsList:
    connDefExitIndexStringList.append(connDefExitIndexString.format(i, s[2:3]))
    if 'ES' in s:
        ESSet.add(s)
        connDefExitTypeStringList.append(connDefExitTypeString.format(i, "true"))
    elif 'SW' in s:
        SWSet.add(s)
        connDefExitTypeStringList.append(connDefExitTypeString.format(i, "false"))
    i += 1

numberOfES = len(ESSet)
numberOfSW = len(SWSet)

# print to ini file
inifile = open("network1.ini", "w")
inifile.write("\n")
for s in connDefEntryIndexStringList:
    inifile.write(s + "\n")
inifile.write("\n")
for s in connDefEntryTypeStringList:
    inifile.write(s + "\n")
inifile.write("\n")
for s in connDefExitIndexStringList:
    inifile.write(s + "\n")
inifile.write("\n")
for s in connDefExitTypeStringList:
    inifile.write(s + "\n")
inifile.write("\n")


