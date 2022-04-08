import os
import matplotlib.pyplot as plt
from reportlab.pdfgen.canvas import Canvas
from datetime import datetime
import statistics
import math
import gc
import sys
import argparse
import shutil
# from time import process_time

tg_95 = 1.96
tg_99 = 2.58

report_now = datetime.now()
report_now_tag = f"{report_now.strftime('%Y%m%d%H%M')}"
figPath = f"ANCAT_figures_{report_now_tag}\\"


class Record:
    def __init__(self):
        self.index = -1
        self.block = ""
        self.name = ""
        self.type = ""
        self.no = -1
        self.count = 0
        self.time = []
        self.data = []

    def __str__(self):
        return f"{self.index}: name={self.name} {self.type}{self.no}, count={len(self.data)}, block={self.block}"

    def addDataPoint(self, t, d):
        self.time.append(float(t))
        self.data.append(float(d))

    def getData(self):
        return self.data

    def getMax(self):
        return max(self.data)

    def getMin(self):
        return min(self.data)

    def getMean(self):
        return statistics.mean(self.data)

    def getStdDev(self):
        return statistics.stdev(self.data)

    def getVariance(self):
        return statistics.variance(self.data)

    def getConfidence95(self):
        return 100*(self.getStdDev()*tg_95) / (self.getMean()*math.sqrt(self.count))

    def getConfidence99(self):
        return 100*(self.getStdDev()*tg_99) / (self.getMean()*math.sqrt(self.count))


def getData(path):
    print(f"Reading directory contents {path}")
    # vci file operations
    filesFound_vci = False
    filesFound_vec = False
    for file in os.listdir(path):
        if file.endswith(".vci"):
            filesFound_vci = True
            file_vci = open(os.path.join(path, file))
            lines_vci = file_vci.readlines()
            vector_lines = [x for x in lines_vci if "vector" in x]
            vector_lines_splitted = list(map(str.split, vector_lines))
            dataCount = len(vector_lines_splitted)
            data_lines = lines_vci[-dataCount - 1:]
            data_lines_splitted = list(map(str.split, data_lines))
            records = [Record() for i in range(dataCount)]

            for i in range(dataCount):
                records[i].index = int(vector_lines_splitted[i][1])
                records[i].block = vector_lines_splitted[i][2]
                records[i].count = int(data_lines_splitted[i][7])
                name_splitted = vector_lines_splitted[i][3].split("_")
                records[i].name = name_splitted[0]
                for c in name_splitted[1]:
                    if c.isdigit():
                        ind = name_splitted[1].index(c)
                        records[i].type = name_splitted[1][:ind]
                        records[i].no = int(name_splitted[1][ind:])
                        break
            print(f"{file} is processed")

    # vec file operations
    for file in os.listdir(path):
        if file.endswith(".vec"):
            filesFound_vec = True
            file_vec = open(os.path.join(path, file))
            lines_vec = file_vec.readlines()
            lines_splitted = list(map(str.split, lines_vec))
            for x in lines_splitted:
                try:
                    records[int(x[0])].addDataPoint(x[2], x[3])
                except IndexError:
                    pass  # x contains no element
                except ValueError:
                    pass  # x[0] is not convertible to int
                except Exception as e:
                    print(e)
            print(f"{file} is processed")

    if not filesFound_vci:
        print(f"*.vci file cannot be found in {path}")
    if not filesFound_vec:
        print(f"*.vec file cannot be found in {path}")
    if not filesFound_vci or not filesFound_vec:
        print(f"Files in the directory:")
        for file in os.listdir(path):
            print(file)
        sys.exit(-1)

    return records


def printMultiRecord(r):
    for i in range(len(r)):
        print(r[i], sep="\n")


def saveFigures(records, outDir, fSize):
    os.mkdir(f"{outDir}{figPath}")
    time_range_small = 0.02
    time_range_medium = 0.1

    # Individual figures ######################################################
    for r in records:
        # 2D line plot
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"{r.name} for {r.type}{r.no}" + " in " + r.block)

        plt.subplot(3, 1, 1)
        plt.grid(True)
        plt.xlabel("Time (ms)")
        xdat = [xd for xd in r.time if xd < time_range_small]
        ydat = r.data[:len(xdat)]
        plt.plot([1000 * x for x in xdat], ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=10)
        plt.subplot(3, 1, 2)
        plt.grid(True)
        plt.xlabel("Time (ms)")
        xdat = [xd for xd in r.time if xd < time_range_medium]
        ydat = r.data[:len(xdat)]
        plt.plot([1000 * x for x in xdat], ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=5)
        plt.subplot(3, 1, 3)
        plt.grid(True)
        plt.xlabel("Time (s)")
        plt.plot(r.time, r.data,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=2)
        plt.savefig(f"{outDir}{figPath}{r.type}{r.no}_{r.name}")
        plt.close()
        plt.clf()
        print(f"Printing individual figures: {int(100*(records.index(r)+1)/len(records))}%")
        gc.collect()

    # Combined figures ########################################################
    rec_names = list(set([x.name for x in records]))
    for r in rec_names:
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"{r}")
        plt.grid(True)

        for x in records:
            if r == x.name:
                plt.subplot(3, 1, 1)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                xdat = [xd for xd in x.time if xd < time_range_small]
                ydat = x.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=10,
                         label=f"{x.type}{x.no}")
                plt.subplot(3, 1, 2)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                xdat = [xd for xd in x.time if xd < time_range_medium]
                ydat = x.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=5,
                         label=f"{x.type}{x.no}")
                plt.subplot(3, 1, 3)
                plt.grid(True)
                plt.xlabel("Time (s)")
                plt.plot(x.time, x.data,
                         linestyle="solid",
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
                         label=f"{x.type}{x.no}")
        plt.subplot(3, 1, 1)
        plt.legend(loc="upper right")
        plt.savefig(f"{outDir}{figPath}Combined_{r}")
        plt.close()
        plt.clf()
        print(f"Printing combined figures: {int(100*(rec_names.index(r)+1)/len(rec_names))}%")
        gc.collect()


class Report(Canvas):
    def __init__(self, outDir, name):
        if name:
            self.reportname = f"{name}_ANCAT_{report_now_tag}"
        else:
            self.reportname = f"ANCAT_{report_now_tag}"
        Canvas.__init__(self, f"{outDir}{self.reportname}.pdf")

        self.currentX = 40
        self.currentY = 800

        self.setTitle("ANCAT Simulation Results")
        self.setAuthor("ANCAT")

        # add title
        self.setFont("Courier-Bold", 28)
        self.drawString(self.currentX+50, self.currentY, "ANCAT Simulation Results")
        self.currentY -= 34
        self.setFont("Courier-Bold", 20)
        self.drawString(self.currentX+150, self.currentY, report_now.strftime("%H:%M    %d.%m.%Y"))
        self.currentY -= 34

    def add_heading_lvl1(self, s):
        self.setFont("Courier-Bold", 18)
        self.drawString(self.currentX, self.currentY, s)
        self.currentY -= 22

    def add_heading_lvl2(self, s):
        self.setFont("Courier-Bold", 14)
        self.drawString(self.currentX+20, self.currentY, s)
        self.currentY -= 18

    def add_line(self, s):
        self.setFont("Courier", 12)
        self.drawString(self.currentX+40, self.currentY, s)
        self.currentY -= 16

    def add_line_v2(self, s, d):
        self.setFont("Courier", 12)
        self.drawString(self.currentX+40, self.currentY, s)
        self.setFont("Courier-Bold", 12)
        self.drawString(self.currentX+240, self.currentY, f"{d}")
        self.currentY -= 16

    def pageBreak(self):
        self.showPage()
        self.currentX = 40
        self.currentY = 800

    def savePDF(self):
        self.save()

    def insertRecord(self, r, s):
        self.add_line_v2(f"    Maximum            : ", r.getMax())
        self.add_line_v2(f"    Minimum            : ", r.getMin())
        self.add_line_v2(f"    Mean               : ", r.getMean())
        if 0 != r.getMean() and r.count >= 2:
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
            self.add_line(f"    Simulation mean is in {r.getConfidence99():.1f}% band of true mean with 99% confidence")
        self.insertImage(s)
        gc.collect()

    def insertTextRecord(self, r, s):
        self.add_line(f"{s}:")
        self.add_line_v2(f"    Maximum            : ", r.getMax())
        self.add_line_v2(f"    Mean               : ", r.getMean())
        if 0 != r.getMean() and r.count >= 2:
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
        gc.collect()

    def insertImage(self, s):
        self.drawImage(s, x=0, y=-150, width=600, preserveAspectRatio=True)
        self.currentY -= 750
        gc.collect()


def saveReport(records, outDir, filename):
    report = Report(outDir, filename)
    rec_type_sw = [x for x in records if "SW" == x.type]
    rec_type_vl = [x for x in records if "VL" == x.type]

    rec_names = list(set([x.name for x in records]))
    rec_vls = list(set([x.no for x in rec_type_vl]))
    rec_sws = list(set([x.no for x in rec_type_sw]))

    rec_names.sort()
    rec_vls.sort()
    rec_sws.sort()

    # general statistics section ##############################################
    print(f"Creating pdf report - Overall Statistics")
    report.add_heading_lvl1("1. Overall Statistics")

    # insert summary text
    for nm in rec_names:
        nsum = Record()
        for r in records:
            if nm == r.name:
                nsum.data += r.data
                nsum.count += int(r.count)
        report.insertTextRecord(nsum, f"Overall {nm}")

    # insert summary figures
    for nm in rec_names:
        nsum = Record()
        for r in records:
            if nm == r.name:
                nsum.data += r.data
                nsum.count += int(r.count)
        report.pageBreak()
        report.add_line(f"     Overall {nm}")
        report.insertRecord(nsum, f"{outDir}{figPath}Combined_{nm}.png")
        print(f"    Combined_{nm}.png is inserted")

    # per Switch statistics section(s) ########################################
    print(f"Creating pdf report - PerSwitch Statistics")
    report.pageBreak()
    nonp = True
    report.add_heading_lvl1("2. Per-Switch Statistics")
    for ns in rec_sws:
        i = rec_sws.index(ns)
        nonp = False if nonp else report.pageBreak()
        report.add_heading_lvl2(f"2.{i + 1}. SW{ns} Statistics")
        for nm in rec_names:
            for r in rec_type_sw:
                if ns == r.no and nm == r.name:
                    report.add_line(f"    {r.name}")
                    report.insertRecord(r, f"{outDir}{figPath}{r.type}{r.no}_{r.name}.png")
        print(f"    SW{ns} is inserted")

    # per VL statistics section(s) ############################################
    print(f"Creating pdf report - PerVL Statistics")
    report.pageBreak()
    nonp = True
    report.add_heading_lvl1("3. Per-VL Statistics")

    for nv in rec_vls:
        i = rec_vls.index(nv)
        nonp = False if nonp else report.pageBreak()
        nonp2 = True
        report.add_heading_lvl2(f"3.{i + 1}. VL{nv} Statistics")
        for nm in rec_names:
            for r in rec_type_vl:
                if nv == r.no and nm == r.name:
                    nonp2 = False if nonp2 else report.pageBreak()
                    report.add_line(f"    {r.name}")
                    report.insertRecord(r, f"{outDir}{figPath}{r.type}{r.no}_{r.name}.png")
        print(f"    VL{nv} is inserted")

    print(f"Saving report")
    # save
    report.savePDF()
    print(f"Report is ready at {outDir}{filename}")


def printTextRecord(r, s):
    print(f"    {s}:")
    print(f"        Maximum            : {r.getMax():.6f}")
    print(f"        Mean               : {r.getMean():.6f}")
    if 0 != r.getMean() and r.count >= 2:
        print(f"        Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
    gc.collect()


def printStatistics(records):
    rec_type_sw = [x for x in records if "SW" == x.type]
    rec_type_vl = [x for x in records if "VL" == x.type]

    rec_names = list(set([x.name for x in records]))
    rec_vls = list(set([x.no for x in rec_type_vl]))
    rec_sws = list(set([x.no for x in rec_type_sw]))

    rec_names.sort()
    rec_vls.sort()
    rec_sws.sort()

    # general statistics section ##############################################
    print(f"==========================================================================================")
    print(f"1. Overall Statistics")

    # insert summary text
    for nm in rec_names:
        nsum = Record()
        for r in records:
            if nm == r.name:
                nsum.data += r.data
                nsum.count += int(r.count)
        printTextRecord(nsum, f"Overall {nm}")

    # insert summary figures
    for nm in rec_names:
        nsum = Record()
        for r in records:
            if nm == r.name:
                nsum.data += r.data
                nsum.count += int(r.count)
        printTextRecord(nsum, f"Combined_{nm}")

    # per Switch statistics section(s) ########################################
    print("2. Per-Switch Statistics")
    for ns in rec_sws:
        i = rec_sws.index(ns)
        print(f"        2.{i + 1}. SW{ns} Statistics")
        for nm in rec_names:
            for r in rec_type_sw:
                if ns == r.no and nm == r.name:
                    printTextRecord(r, f"        {r.name}")

    # per VL statistics section(s) ############################################
    print("3. Per-VL Statistics")

    for nv in rec_vls:
        i = rec_vls.index(nv)
        print(f"    3.{i + 1}. VL{nv} Statistics")
        for nm in rec_names:
            for r in rec_type_vl:
                if nv == r.no and nm == r.name:
                    printTextRecord(r, f"        {r.name}")

    print(f"==========================================================================================")


def clean(path):
    shutil.rmtree(f"{path}{figPath}")


if __name__ == "__main__":

    myParser = argparse.ArgumentParser(
        description="Creates a pdf report from the simulation result files."
                    "Please specify the results file's location. Otherwise current directory will be searched.")

    # Add the arguments
    myParser.add_argument('-iPath',
                          metavar="<input path>",
                          type=str,
                          help='Location of the simulation result files; *.vci and *.vec',
                          required=False)
    myParser.add_argument('-oPath',
                          metavar="<Output path>",
                          type=str,
                          help='path that pdf file and figures (optional) to be located.',
                          required=False)
    myParser.add_argument('-oFile',
                          metavar="<Output path>",
                          type=str,
                          help='Name of the output pdf report, optional',
                          required=False)
    myParser.add_argument('-keepFig',
                          help='If this flag is given, mid-process figures will not be deleted.',
                          action="store_true")
    myParser.add_argument('-figAndText',
                          help='If this flag is given, pdf report will not be generated.',
                          action="store_true")
    myParser.add_argument('-textOnly',
                          help='If this flag is given, no output file will be generated, console text only',
                          action="store_true")

    args = myParser.parse_args()
    iPath = args.iPath
    oPath = args.oPath
    keepFig = args.keepFig
    figAndText = args.figAndText
    textOnly = args.textOnly
    oFile = args.oFile

    if iPath is None:
        iPath = ".\\"
        print(f"Using current directory for simulation results.")
    else:
        print(f"Using '{iPath}' for simulation results.")
        if not iPath.endswith("\\"):
            iPath += "\\"
    if oPath is None:
        oPath = ".\\"
        print("Using current directory for outputs.")
    else:
        print(f"Using '{oPath}' for outputs.")
        if not oPath.endswith("\\"):
            oPath += "\\"
    if oFile is not None:
        figPath = f"{oFile}_{figPath}"

    records = getData(iPath)
    # printMultiRecord(records)

    if not textOnly or keepFig:
        saveFigures(records, oPath, 10)

    if textOnly or figAndText:
        printStatistics(records)
    else:
        saveReport(records, oPath, oFile)

    if not keepFig and not figAndText:
        clean(oPath)
