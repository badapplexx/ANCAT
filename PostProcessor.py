import os
import matplotlib
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

matplotlib.use('Agg')

# constants
tg_95 = 1.96
tg_99 = 2.58

# globals
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
        if file.endswith(".vci"):  # if there is a file ending with vci in the directory
            filesFound_vci = True
            file_vci = open(os.path.join(path, file))
            lines_vci = file_vci.readlines()
            vector_lines = [x for x in lines_vci if "vector" in x]  # get all lines including "vector"
            vector_lines_splitted = list(map(str.split, vector_lines))
            dataCount = len(vector_lines_splitted)
            data_lines = lines_vci[-dataCount - 1:]
            data_lines_splitted = list(map(str.split, data_lines))

            records = [Record() for i in range(dataCount)]  # create records
            # fill those records that've just been created
            for i in range(dataCount):
                records[i].index = int(vector_lines_splitted[i][1])  # index number of record given by omnetpp
                records[i].block = vector_lines_splitted[i][2]  # in which block of simulation record is created
                records[i].count = int(data_lines_splitted[i][7])  # how many data points are there
                name_splitted = vector_lines_splitted[i][3].split("_")
                records[i].name = name_splitted[0]
                for c in name_splitted[1]:
                    if c.isdigit():
                        ind = name_splitted[1].index(c)
                        records[i].type = name_splitted[1][:ind]   # the type of the record, i.e. VL, SW ...
                        records[i].no = int(name_splitted[1][ind:])  # the no of the type, VL1, VL2, VL3 ...
                        break
            print(f"{file} is processed")

    # vec file operations, in this line, vci file should already be parsed
    for file in os.listdir(path):
        if file.endswith(".vec"):  # if there is a file ending with vec in the directory
            filesFound_vec = True
            file_vec = open(os.path.join(path, file))
            lines_vec = file_vec.readlines()
            lines_splitted = list(map(str.split, lines_vec))
            for x in lines_splitted:
                try:
                    records[int(x[0])].addDataPoint(x[2], x[3])  # add current line's data to the relative index
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


def printMultiRecord(r):  # prints all records in r (as specified in Record class)
    for i in range(len(r)):
        print(r[i], sep="\n")


def saveFigures(records, outDir, fSize, summaryOnly):
    os.mkdir(f"{outDir}{figPath}")
    time_range_small = 0.02
    time_range_medium = 0.1

    # Histograms ##############################################################

    rec_type_vl = [x for x in records if "VL" == x.type]  # records with type VL
    rec_vls = list(set([x.no for x in rec_type_vl]))  # all record vl no.s
    rec_vls.sort()
    for vn in rec_vls:
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"Inter-arrival time histogram for VL{vn}", y=0.05)
        # search in records having no == vn
        for r in records:
            if vn == r.no and "VL" == r.type:
                if "ESBag" in r.name:
                    inter_packet_bagged = [r.time[x + 1] - r.time[x] for x in range(len(r.time) - 1)]
                if "TrafficSource" in r.name:
                    inter_packet_source = [r.time[x + 1] - r.time[x] for x in range(len(r.time) - 1)]

        # plot histogram of these inter packet times at source and after bagging
        plt.subplot(2, 1, 1)
        plt.grid(True)
        plt.title(f"At creation")
        plt.xlabel("Time (s)")
        plt.ylabel("Packet count")
        plt.hist(inter_packet_source, 100,
                 range=(min(inter_packet_source), statistics.mean(inter_packet_source) * 1.5),
                 color="black")
        plt.subplot(2, 1, 2)
        plt.grid(True)
        plt.title(f"After bagging")
        plt.xlabel("Time (s)")
        plt.ylabel("Packet count")
        plt.hist(inter_packet_bagged, 100,
                 range=(min(inter_packet_bagged), statistics.mean(inter_packet_bagged) * 1.5),
                 color="black")

        plt.savefig(f"{outDir}{figPath}{r.type}{vn}_InterArrival")
        plt.clf()
        plt.close("all")
        print(f"Printing histograms: {int(100*(rec_vls.index(vn)+1)/len(rec_vls))}%")
        gc.collect()

    # Individual figures ######################################################
    if not summaryOnly:
        # for all records
        for r in records:

            # create a 2D line plot
            plt.figure(figsize=(fSize, fSize))
            plt.suptitle(f"{r.name} for {r.type}{r.no}", y=0.05)

            # make 3 row plot for different zoom levels
            plt.subplot(3, 1, 1)
            plt.grid(True)
            plt.xlabel("Time (ms)")
            plt.ylabel("Time (s)" if not "QueueLength" in r.name else "Queue Length")
            xdat = [xd for xd in r.time if xd < time_range_small]  # select the data for max zoom level
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
            plt.ylabel("Time (s)" if not "QueueLength" in r.name else "Queue Length")
            xdat = [xd for xd in r.time if xd < time_range_medium]  # select the data for medium zoom level
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
            plt.ylabel("Time (s)" if not "QueueLength" in r.name else "Queue Length")
            plt.plot(r.time, r.data,  # plot the whole data
                     color="black",
                     linestyle="solid",
                     linewidth=1,
                     marker=".",
                     markersize=2)
            plt.savefig(f"{outDir}{figPath}{r.type}{r.no}_{r.name}")
            plt.clf()
            plt.close("all")
            print(f"Printing individual figures: {int(100*(records.index(r)+1)/len(records))}%")
            gc.collect()

    # Combined figures ########################################################
    rec_names = list(set([x.name for x in records]))

    # for all record names
    for r in rec_names:
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"{r}", y=0.05)
        plt.grid(True)

        # find a record with matching name to the current loop's name in all records
        for x in records:
            if r == x.name:

                # make 3 row plot for different zoom levels
                plt.subplot(3, 1, 1)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                plt.ylabel("Time (s)" if not "QueueLength" in r else "Queue Length")
                xdat = [xd for xd in x.time if xd < time_range_small]  # select the data for max zoom level
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
                plt.ylabel("Time (s)" if not "QueueLength" in r else "Queue Length")
                xdat = [xd for xd in x.time if xd < time_range_medium]  # select the data for medium zoom level
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
                plt.ylabel("Time (s)" if not "QueueLength" in r else "Queue Length")
                plt.plot(x.time, x.data,  # plot the whole data
                         linestyle="solid",
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
                         label=f"{x.type}{x.no}")

        # put a legend to the top of the figure
        plt.subplot(3, 1, 1)
        handles, labels = plt.gca().get_legend_handles_labels()
        plt.legend(handles, labels, bbox_to_anchor=(0, 1, 1, 1), loc="lower center", fancybox=True, ncol=8)
        plt.savefig(f"{outDir}{figPath}Combined_{r}")
        plt.clf()
        plt.close("all")
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

    def getFileName(self):
        return self.reportname

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
        self.drawString(self.currentX+270, self.currentY, ": ")
        self.setFont("Courier-Bold", 12)
        self.drawString(self.currentX+280, self.currentY, f"{d}")
        self.currentY -= 16

    def pageBreak(self):
        self.showPage()
        self.currentX = 40
        self.currentY = 800

    def savePDF(self):
        self.save()

    def insertRecord(self, r, s):
        self.add_line_v2(f"    Maximum", r.getMax())
        self.add_line_v2(f"    Minimum", r.getMin())
        self.add_line_v2(f"    Mean", r.getMean())
        if 0 != r.getMean() and r.count >= 2:
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
            self.add_line(f"    Simulation mean is in {r.getConfidence99():.1f}% band of true mean with 99% confidence")
        self.insertImage(s)
        gc.collect()

    def insertTextRecord(self, r, s):
        self.add_line(f"{s}:")
        self.add_line_v2(f"    Maximum", r.getMax())
        self.add_line_v2(f"    Mean", r.getMean())
        if 0 != r.getMean() and r.count >= 2:
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
        gc.collect()

    def insertImage(self, s):
        self.drawImage(s, x=0, y=-150, width=600, preserveAspectRatio=True)
        self.currentY -= 750
        gc.collect()


def saveReport(records, outDir, filename, summaryOnly):
    report = Report(outDir, filename)
    rec_type_sw = [x for x in records if "SW" == x.type]  # records with type SW
    rec_type_vl = [x for x in records if "VL" == x.type]  # records with type VL

    rec_names = list(set([x.name for x in records]))  # all record names
    rec_vls = list(set([x.no for x in rec_type_vl]))  # all record vl no.s
    rec_sws = list(set([x.no for x in rec_type_sw]))  # all record sw no.s

    rec_names.sort()
    rec_vls.sort()
    rec_sws.sort()

    # general statistics section ##############################################
    print(f"Creating pdf report - Overall Statistics")
    report.add_heading_lvl1("1. Overall Statistics")

    # insert summary text

    # Dropped frames
    droppedSum = Record()
    total_packets = 0
    for r in records:  # count all Dropped frames
        if "Dropped" in r.name:
            droppedSum.data += r.data
            droppedSum.count += int(r.count)
    for rcc in records:
        if "ESBag" in rcc.name:  # use ESBag records to count all frames in the simulation
            total_packets += rcc.count
    report.add_line_v2(f"Overall Total Frame Count", total_packets)
    report.add_line_v2(f"Overall Dropped Frame Count", droppedSum.count)
    report.add_line_v2(f"Overall Dropped Frame Percentage", droppedSum.count/total_packets)

    # insert summary text
    for nm in rec_names:  # for all names in records
        nsum = Record()
        for r in records:
            if nm == r.name:  # find records with that name
                nsum.data += r.data  # and create a sum of that data
                nsum.count += int(r.count)
        if "Dropped" not in nm and "TrafficSource" not in nm:
            report.insertTextRecord(nsum, f"Overall {nm}")

    # insert summary figures
    for nm in rec_names:  # for all names in records
        nsum = Record()
        for r in records:
            if nm == r.name:  # find records with that name
                nsum.data += r.data  # and create a sum of that data
                nsum.count += int(r.count)
        if "Dropped" not in nm and "TrafficSource" not in nm:
            report.pageBreak()
            report.add_line(f"     Overall {nm}")
            report.insertRecord(nsum, f"{outDir}{figPath}Combined_{nm}.png")  # and put that figure into report
            print(f"    Combined_{nm}.png is inserted")

    # per Switch statistics section(s) ########################################
    print(f"Creating pdf report - PerSwitch Statistics")
    if not summaryOnly:
        report.pageBreak()
        nonp = True
        report.add_heading_lvl1("2. Per-Switch Statistics")
        for ns in rec_sws:  # for all switch no.s
            i = rec_sws.index(ns)
            nonp = False if nonp else report.pageBreak()
            report.add_heading_lvl2(f"2.{i + 1}. SW{ns} Statistics")
            for nm in rec_names:  # for all names in records
                for r in rec_type_sw:  # in all switch records
                    if ns == r.no and nm == r.name:  # if that name of record and switch no found
                        report.add_line(f"    {r.name}")
                        report.insertRecord(r, f"{outDir}{figPath}{r.type}{r.no}_{r.name}.png")
            print(f"    SW{ns} is inserted")

    # per VL statistics section(s) ############################################
    print(f"Creating pdf report - PerVL Statistics")
    if not summaryOnly:
        report.pageBreak()
        nonp = True
        report.add_heading_lvl1("3. Per-VL Statistics")

        for nv in rec_vls:  # for all vl no.s
            i = rec_vls.index(nv)
            nonp = False if nonp else report.pageBreak()
            nonp2 = True
            report.add_heading_lvl2(f"3.{i + 1}. VL{nv} Statistics")

            # print total packet count and dropped ones
            total_packets = 0
            dropped_packets = 0
            for r in rec_type_vl:
                if nv == r.no and "ESBag" in r.name:  # count frames for that VL over ESBagLatency records
                    total_packets = r.count
            for r in rec_type_vl:
                if nv == r.no and "Dropped" in r.name:
                    dropped_packets = r.count
            report.add_line_v2(f"Total Frame Count", total_packets)
            report.add_line_v2(f"Dropped Frame Count", dropped_packets)
            report.add_line_v2(f"Dropped Frame Percentage", dropped_packets / total_packets if 0 != total_packets else 0)
            nonp2 = False if nonp2 else report.pageBreak()

            # print histograms
            report.insertImage(f"{outDir}{figPath}VL{nv}_InterArrival.png")

            for nm in rec_names:  # for all names
                if "Dropped" not in nm and "TrafficSource" not in nm:
                    for r in rec_type_vl:  # in all VL records
                        if nv == r.no and nm == r.name:  # if record no and name matches
                            nonp2 = False if nonp2 else report.pageBreak()
                            report.add_line(f"    {r.name}")
                            report.insertRecord(r, f"{outDir}{figPath}{r.type}{r.no}_{r.name}.png")
            print(f"    VL{nv} is inserted")

    print(f"Saving report")
    # save
    report.savePDF()
    print(f"Report is ready at {outDir}{report.getFileName()}")


def printTextRecord(r, s):
    print(f"    {s}:")
    print(f"        Maximum            : {r.getMax():.6f}")
    print(f"        Mean               : {r.getMean():.6f}")
    if 0 != r.getMean() and r.count >= 2:
        print(f"        Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
    gc.collect()


def printStatistics(records, summaryOnly):
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
    if not summaryOnly:
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
    if not summaryOnly:
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
    myParser.add_argument('-summaryOnly',
                          help='If this flag is given, perVL and per Switch statistics will not be generated',
                          action="store_true")

    args = myParser.parse_args()
    iPath = args.iPath
    oPath = args.oPath
    keepFig = args.keepFig
    figAndText = args.figAndText
    textOnly = args.textOnly
    oFile = args.oFile
    summaryOnly = args.summaryOnly

    if iPath is None:
        iPath = ".\\"
        print(f"Using current directory for simulation data.")
    else:
        if not iPath.endswith("\\"):
            iPath += "\\"
        print(f"Using '{iPath}' for simulation data.")
    if oPath is None:
        oPath = ".\\"
        print("Using current directory for outputs.")
    else:
        if oPath == "same":
            oPath = iPath
            print("Using input directory for outputs.")
        else:
            if not oPath.endswith("\\"):
                oPath += "\\"
            print(f"Using '{oPath}' for outputs.")
    if oFile is not None:
        figPath = f"{oFile}_{figPath}"

    records = getData(iPath)
    # printMultiRecord(records)

    if not textOnly or keepFig:
        saveFigures(records, oPath, 10, summaryOnly)

    if textOnly or figAndText:
        printStatistics(records, summaryOnly)
    else:
        saveReport(records, oPath, oFile, summaryOnly)

    if not keepFig and not figAndText and not textOnly:
        clean(oPath)
