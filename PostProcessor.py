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
figPath = f"ANCAT_figures_{report_now_tag}/"

records = []
overall_records = []
rec_names = []  # all record names
rec_vls = []  # all record vl no.s
rec_sws = []  # all record sw no.s
records_sw = []  # all records for sw
records_vl = []  # all record for vl


class Record:
    def __init__(self):
        self.index = -1
        self.block = ""
        self.name = ""
        self.type = ""
        self.no = -1
        self.time = []
        self.data = []

    def __str__(self):
        return f"{self.index:<3}: name={self.name:<30} {self.type:<3}{self.no:<6}, " \
               f"count={self.getCount():<5}, {self.getMeanText():<15}={self.getMean():<25}"

    def addDataPoint(self, t, d):
        self.time.append(float(t))
        self.data.append(float(d))

    def getData(self):
        return self.data

    def getCount(self):
        return len(self.data)

    def getMax(self):
        return max(self.data)

    def getMin(self):
        return min(self.data)

    def getMean(self):
        if "QueueLength" in self.name:
            total_weight = 0
            for i in range(1, self.getCount()):
                val_mean = (self.data[i] + self.data[i - 1]) / 2
                diff_in_time = self.time[i] - self.time[i - 1]
                total_weight += val_mean * diff_in_time
            mymean = total_weight / self.time[-1]
        else:
            mymean = statistics.mean(self.data)
        return mymean

    def getMeanText(self):
        if "QueueLength" in self.name:
            ret = "weighted mean"
        else:
            ret = "mean"
        return ret

    def getStdDev(self):
        return statistics.stdev(self.data)

    def getVariance(self):
        return statistics.variance(self.data)

    def getConfidence95(self):
        return 100*(self.getStdDev()*tg_95) / (self.getMean()*math.sqrt(self.getCount()))

    def getConfidence99(self):
        return 100*(self.getStdDev()*tg_99) / (self.getMean()*math.sqrt(self.getCount()))


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
        self.bookmarkPage(s)
        self.addOutlineEntry(s, s, level=0)
        self.setFont("Courier-Bold", 18)
        self.drawString(self.currentX, self.currentY, s)
        self.currentY -= 22

    def add_heading_lvl2(self, s):
        self.bookmarkPage(s)
        self.addOutlineEntry(s, s, level=1)
        self.setFont("Courier-Bold", 14)
        self.drawString(self.currentX+20, self.currentY, s)
        self.currentY -= 18

    def add_line(self, s):
        if self.currentY < 50:
            self.pageBreak()
        self.setFont("Courier", 12)
        self.drawString(self.currentX+40, self.currentY, s)
        self.currentY -= 16

    def add_line_v2(self, s, d):
        if self.currentY < 50:
            self.pageBreak()
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

    def insertRecordDetailText(self, r, s):
        self.add_line_v2(f"    Data count", r.getCount())
        self.add_line_v2(f"    Final time", r.time[-1])
        self.add_line_v2(f"    Maximum", r.getMax())
        self.add_line_v2(f"    Minimum", r.getMin())
        if 0 != r.getMean() and r.getCount() >= 2:
            self.add_line_v2(f"    {r.getMeanText().title()}", r.getMean())
            if "QueueLength" not in r.name:
                self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
                self.add_line(f"    Simulation mean is in {r.getConfidence99():.1f}% band of true mean with 99% confidence")
        self.insertImage(s)
        gc.collect()

    def insertRecordSummaryText(self, r, s):
        self.add_line(f"{s}:")
        self.add_line_v2(f"    Maximum", r.getMax())
        if 0 != r.getMean() and r.getCount() >= 2:
            self.add_line_v2(f"    {r.getMeanText().title()}", r.getMean())
            if "QueueLength" not in r.name:
                self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
        gc.collect()

    def insertImage(self, s):
        if self.currentY < 650:
            self.pageBreak()
        self.drawImage(s, x=0, y=-180, width=600, preserveAspectRatio=True)
        self.currentY -= 750
        gc.collect()


def getData():
    global records
    global overall_records
    global rec_names
    global rec_vls
    global rec_sws
    global records_sw
    global records_vl

    print(f"Reading directory contents {args.iPath}")
    # vci file operations
    filesFound_vci = False
    filesFound_vec = False
    for file in os.listdir(args.iPath):
        if file.endswith(".vci"):  # if there is a file ending with vci in the directory
            filesFound_vci = True
            file_vci = open(os.path.join(args.iPath, file))
            lines_vci = file_vci.readlines()
            vector_lines = [x for x in lines_vci if "vector " in x]  # get all lines including "vector"
            vector_lines_splitted = list(map(str.split, vector_lines))
            dataCount = len(vector_lines_splitted)
            data_lines = lines_vci[-dataCount - 1:]
            data_lines_splitted = list(map(str.split, data_lines))

            # fill those records that've just been created
            for i in range(dataCount):
                records.append(Record())
                records[i].index = int(vector_lines_splitted[i][1])  # index number of record given by omnetpp
                records[i].block = vector_lines_splitted[i][2]  # in which block of simulation record is created
                name_splitted = vector_lines_splitted[i][3].split("_")
                records[i].name = name_splitted[0]
                for c in name_splitted[1]:
                    if "VL" in name_splitted[1] or "SW" in name_splitted[1]:
                        records[i].type = name_splitted[1][:2]   # the type of the record, i.e. VL, SW ...
                        records[i].no = name_splitted[1][2:]  # the no of the type, i.e. 2c03 in VL2c03
                        break
                    else:
                        print("UNKNOWN RECORD TYPE, PLEASE FIX ANCAT TO INCLUDE THIS RECORD TYPE!")
            print(f"{file} is processed")

    # vec file operations, in this line, vci file should already be parsed
    for file in os.listdir(args.iPath):
        if file.endswith(".vec"):  # if there is a file ending with vec in the directory
            filesFound_vec = True
            file_vec = open(os.path.join(args.iPath, file))
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
        print(f"*.vci file cannot be found in {args.iPath}")
    if not filesFound_vec:
        print(f"*.vec file cannot be found in {args.iPath}")
    if not filesFound_vci or not filesFound_vec:
        print(f"Files in the directory:")
        for file in os.listdir(args.iPath):
            print(file)
        sys.exit(-1)

    records_sw = [rec for rec in records if "SW" == rec.type]  # records with type SW
    records_vl = [rec for rec in records if "VL" == rec.type]  # records with type VL
    rec_names = list(set([rec.name for rec in records]))  # all record names
    rec_vls = list(set([rec.no for rec in records_vl]))  # all record vl no.s
    rec_sws = list(set([rec.no for rec in records_sw]))  # all record sw no.s

    rec_names.sort()
    rec_vls.sort()
    rec_sws.sort()

    for rn in rec_names:
        overall_records.append(Record())
        overall_records[-1].index = rec_names.index(rn)
        overall_records[-1].name = f"Overall{rn}"
        overall_records[-1].type = "VL"
        for rec in records:
            if rn == rec.name and rec.type == "VL":
                overall_records[-1].data += rec.data
                overall_records[-1].time += rec.time

    for rn in rec_names:
        overall_records.append(Record())
        overall_records[-1].index = rec_names.index(rn)
        overall_records[-1].name = f"Overall{rn}"
        overall_records[-1].type = "SW"
        for rec in records:
            if rn == rec.name and rec.type == "SW":
                overall_records[-1].data += rec.data
                overall_records[-1].time += rec.time
    overall_records = [orec for orec in overall_records if orec.getCount() != 0]

    # Print records
    debugprint("rec_names: ")
    debugprint(rec_names)

    debugprint("rec_vls: ")
    debugprint(rec_vls)

    debugprint("rec_sws: ")
    debugprint(rec_sws)

    debugprint("records: ")
    for i in range(len(records)):
        debugprint(records[i], sep="\n")

    debugprint("overall records: ")
    for i in range(len(overall_records)):
        debugprint(overall_records[i], sep="\n")


def saveFigures():
    fSize = 10
    os.mkdir(f"{args.oPath}{figPath}")
    time_range_small = 0.02
    time_range_medium = 0.1

    # Histograms ##############################################################
    # Histogram for inter packet times at source and after bagging AND at destination
    counter = 0
    for rvl in rec_vls:
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"Inter-arrival time histogram for VL{rvl}", y=0.05)
        debugprint(f"Histogram print for VL{rvl}")
        # search in records having no == vn
        for rec in records:
            if rvl == rec.no and "VL" == rec.type:
                if "ESBag" in rec.name:
                    inter_packet_bagged = [rec.time[x + 1] - rec.time[x] for x in range(len(rec.time) - 1)]
                if "TrafficSource" in rec.name:
                    inter_packet_source = [rec.time[x + 1] - rec.time[x] for x in range(len(rec.time) - 1)]
                if "E2ELatency" in rec.name:
                    inter_packet_destination = [rec.time[x + 1] - rec.time[x] for x in range(len(rec.time) - 1)]
                    e2e = rec.data

        if len(inter_packet_destination) <= 1:
            continue

        plt.subplot(4, 1, 1)
        plt.grid(True)
        plt.title(f"At creation", y=1.0, pad=-14)
        plt.ylabel("Packet count")
        plt.hist(inter_packet_source, 200,
                 range=(min(inter_packet_source), statistics.mean(inter_packet_source) * 1.5),
                 color="black")
        plt.subplot(4, 1, 2)
        plt.grid(True)
        plt.title(f"After bagging", y=1.0, pad=-14)
        plt.ylabel("Packet count")
        plt.hist(inter_packet_bagged, 200,
                 range=(min(inter_packet_bagged), statistics.mean(inter_packet_bagged) * 1.5),
                 color="black")
        plt.subplot(4, 1, 3)
        plt.grid(True)
        plt.title(f"At destination", y=1.0, pad=-14)
        plt.ylabel("Packet count")
        plt.hist(inter_packet_destination, 200,
                 range=(min(inter_packet_destination), statistics.mean(inter_packet_destination) * 1.5),
                 color="black")
        plt.subplot(4, 1, 4)
        plt.grid(True)
        plt.title(f"E2E Latency", y=1.0, pad=-14)
        plt.xlabel("Time (s)")
        plt.ylabel("Packet count")
        plt.hist(e2e, 200,
                 range=(min(e2e), statistics.mean(e2e) * 1.5),
                 color="black")

        plt.savefig(f"{args.oPath}{figPath}VL{rvl}_InterArrival")
        plt.clf()
        plt.close("all")
        debugprint(f"  {args.oPath}{figPath}VL{rvl}_InterArrival")
        counter = counter + 1
        print(f"Printing histograms (1/3) -{counter}- ... ")
        gc.collect()

    # Histogram of E2ELatency Per destination end system per vl
    counter = 0
    for rec in records:
        if "VL" == rec.type:
            if "LatencyAt" in rec.name:
                plt.figure(figsize=(fSize, fSize))
                plt.suptitle(f"Histogram of {rec.name} for VL{rec.no}", y=0.05)
                debugprint(f"Histogram print for {rec.name} for VL{rec.no}")
                # search in records having no == vn

                if len(rec.data) <= 1:
                    continue

                plt.grid(True)
                plt.title(f"E2ELatency Per Destination ES", y=1.0, pad=-14)
                plt.xlabel("Time (s)")
                plt.ylabel("Packet count")
                plt.hist(rec.data, 200,
                         range=(min(rec.data), statistics.mean(rec.data) * 1.5),
                         color="black")

                plt.savefig(f"{args.oPath}{figPath}Histogram_{rec.name}VL{rec.no}")
                plt.clf()
                plt.close("all")
                debugprint(f"  {args.oPath}{figPath}Histogram_{rec.name}VL{rec.no}")
                counter = counter + 1
                print(f"Printing histograms (2/3) -{counter}- ... ")
                gc.collect()

    # Histogram of SWQueueingTime Per port per SW
    counter = 0
    for rec in records:
        if "SW" == rec.type:
            if "SWQueueingTime#Port" in rec.name:
                plt.figure(figsize=(fSize, fSize))
                plt.suptitle(f"Histogram of {rec.name} for SW{rec.no}", y=0.05)
                debugprint(f"Histogram print for {rec.name} for VL{rec.no}")
                # search in records having no == vn

                if len(rec.data) <= 1:
                    continue

                plt.grid(True)
                plt.title(f"Queuing Time Per Switch and Port", y=1.0, pad=-14)
                plt.xlabel("Time (s)")
                plt.ylabel("Time (s)")
                plt.hist(rec.data, #200,
                         # range=(min(rec.data), statistics.mean(rec.data) * 1.5),
                         color="black")

                plt.savefig(f"{args.oPath}{figPath}Histogram_{rec.name}SW{rec.no}")
                plt.clf()
                plt.close("all")
                debugprint(f"  {args.oPath}{figPath}Histogram_{rec.name}SW{rec.no}")
                counter = counter + 1
                print(f"Printing histograms (3/3) -{counter}- ... ")
                gc.collect()

    # Individual figures ######################################################
    if not args.summaryOnly:
        # for all records
        for rec in records:
            if "Dropped" not in rec.name and "TrafficSource" not in rec.name:
                # create a 2D line plot
                plt.figure(figsize=(fSize, fSize))
                plt.suptitle(f"{rec.name} for {rec.type}{rec.no}", y=0.05)

                # make 3 row plot for different zoom levels
                plt.subplot(3, 1, 1)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                plt.ylabel("Time (s)" if "QueueLength" not in rec.name else "Queue Length")
                xdat = [xd for xd in rec.time if xd < time_range_small]  # select the data for max zoom level
                ydat = rec.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         color="black",
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=10)
                plt.subplot(3, 1, 2)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                plt.ylabel("Time (s)" if "QueueLength" not in rec.name else "Queue Length")
                xdat = [xd for xd in rec.time if xd < time_range_medium]  # select the data for medium zoom level
                ydat = rec.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         color="black",
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=5)
                plt.subplot(3, 1, 3)
                plt.grid(True)
                plt.xlabel("Time (s)")
                plt.ylabel("Time (s)" if "QueueLength" not in rec.name else "Queue Length")
                plt.plot(rec.time, rec.data,  # plot the whole data
                         color="black",
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=2)
                plt.savefig(f"{args.oPath}{figPath}{rec.type}{rec.no}_{rec.name}")
                plt.clf()
                plt.close("all")
                debugprint(f"  {args.oPath}{figPath}{rec.type}{rec.no}_{rec.name}.png is added")
                print(f"Printing individual figures: {int(100*(records.index(rec)+1)/len(records))}%")
                gc.collect()

    # Overall figures ########################################################

    # for all record names
    for orec in overall_records:
        plt.figure(figsize=(fSize, fSize))
        plt.suptitle(f"{orec.name} for all {orec.type}", y=0.05)
        plt.grid(True)

        # find a record with matching name to the current loop's name in all records
        for rec in records:
            if ("Overall" + rec.name) == orec.name and orec.type == rec.type:
                debugprint(f"    processing {rec.name}{rec.type}{rec.no} for {orec.name}{orec.type}")

                # make 3 row plot for different zoom levels
                plt.subplot(3, 1, 1)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                plt.ylabel("Time (s)" if "QueueLength" not in orec.name else "Queue Length")
                xdat = [xd for xd in rec.time if xd < time_range_small]  # select the data for max zoom level
                ydat = rec.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=10,
                         label=f"{rec.type}{rec.no}")
                plt.subplot(3, 1, 2)
                plt.grid(True)
                plt.xlabel("Time (ms)")
                plt.ylabel("Time (s)" if "QueueLength" not in orec.name else "Queue Length")
                xdat = [xd for xd in rec.time if xd < time_range_medium]  # select the data for medium zoom level
                ydat = rec.data[:len(xdat)]
                plt.plot([1000 * x for x in xdat], ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=5,
                         label=f"{rec.type}{rec.no}")
                plt.subplot(3, 1, 3)
                plt.grid(True)
                plt.xlabel("Time (s)")
                plt.ylabel("Time (s)" if "QueueLength" not in orec.name else "Queue Length")
                plt.plot(rec.time, rec.data,  # plot the whole data
                         linestyle="solid",
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
                         label=f"{rec.type}{rec.no}")

        # put a legend to the top of the figure
        plt.subplot(3, 1, 1)
        handles, labels = plt.gca().get_legend_handles_labels()
        plt.legend(handles, labels, bbox_to_anchor=(0, 1, 1, 1), loc="lower center", fancybox=True, ncol=8)
        plt.savefig(f"{args.oPath}{figPath}{orec.type}_{orec.name}")
        plt.clf()
        plt.close("all")
        debugprint(f"  {args.oPath}{figPath}{orec.type}_{orec.name}")
        print(f"Printing overall figures: {int(100*(overall_records.index(orec)+1)/len(overall_records))}%")
        gc.collect()


def saveReport():
    report = Report(args.oPath, args.oFile)

    # general statistics section ##############################################
    print(f"Creating pdf report - Overall Statistics")
    report.add_heading_lvl1("1. Overall Statistics")

    # insert summary text

    # Dropped frames
    droppedSum = Record()
    total_packets = 0
    total_time = 0
    for rec in records:  # count all Dropped frames
        if "Dropped" in rec.name:
            droppedSum.data += rec.data
    for rec in records:
        if "ESBag" in rec.name:  # use ESBag records to count all frames in the simulation
            total_packets += rec.getCount()
            total_time = max(total_time, rec.time[-1])
    report.add_line_v2(f"Overall Frame Count", total_packets)
    report.add_line_v2(f"Overall Simulation Time", total_time)
    report.add_line_v2(f"Overall Dropped Frame Count", droppedSum.getCount())
    report.add_line_v2(f"Overall Dropped Frame Percentage", droppedSum.getCount()/total_packets)

    # insert summary text
    for orec in overall_records:  # for all names in records
        if "Dropped" not in orec.name and "TrafficSource" not in orec.name:
            report.insertRecordSummaryText(orec, f"Overall {orec.name}")

    # insert summary figures
    for orec in overall_records:  # for all names in records
        if "Dropped" not in orec.name and "TrafficSource" not in orec.name:
            #report.pageBreak()
            report.add_line(f"     {orec.name} for all {orec.type}")
            report.insertRecordDetailText(orec, f"{args.oPath}{figPath}{orec.type}_{orec.name}.png")  # and put that figure into report
            debugprint(f"    {orec.name}.png is inserted")

    # per Switch statistics section(s) ########################################
    print(f"Creating pdf report - PerSwitch Statistics")
    if not args.summaryOnly:
        report.pageBreak()
        report.add_heading_lvl1("2. Per-Switch Statistics")
        for rsw in rec_sws:  # for all switch no.s
            i = rec_sws.index(rsw)
            report.pageBreak()
            report.add_heading_lvl2(f"2.{i + 1}. SW{rsw} Statistics")
            debugprint(f"      Will add SWQueueingTime#Port Histograms...")
            for rec in records:
                if rsw == rec.no and "SW" == rec.type:
                    if "SWQueueingTime#Port" in rec.name:
                        if len(rec.data) <= 1:
                            continue
                        debugprint(f"        {args.oPath}{figPath}Histogram_{rec.name}SW{rsw}.png")
                        #report.pageBreak()
                        report.add_line(f"    Histogram_{rec.name}SW{rsw}")
                        report.insertImage(f"{args.oPath}{figPath}Histogram_{rec.name}SW{rsw}.png")
            for rn in rec_names:  # for all names in records
                for rec_sw in records_sw:  # in all switch records
                    if rsw == rec_sw.no and rn == rec_sw.name:  # if that name of record and switch no found
                        debugprint(f"      {rn}")
                        #report.pageBreak()
                        report.add_line(f"    {rec_sw.name}")
                        report.insertRecordDetailText(rec_sw, f"{args.oPath}{figPath}{rec_sw.type}{rec_sw.no}_{rec_sw.name}.png")
            print(f"    SW{rsw} is inserted")

    # per VL statistics section(s) ############################################
    print(f"Creating pdf report - PerVL Statistics")
    if not args.summaryOnly:
        report.pageBreak()
        report.add_heading_lvl1("3. Per-VL Statistics")

        for rvl in rec_vls:  # for all vl no.s
            debugprint(f"    VL{rvl} will be inserted ...")
            i = rec_vls.index(rvl)
            report.pageBreak()
            report.add_heading_lvl2(f"3.{i + 1}. VL{rvl} Statistics")

            # print total packet count and dropped ones
            total_packets = 0
            dropped_packets = 0
            for rec_vl in records_vl:
                if rvl == rec_vl.no and "ESBag" in rec_vl.name:  # count frames for that VL over ESBagLatency records
                    total_packets = rec_vl.getCount()
            for rec_vl in records_vl:
                if rvl == rec_vl.no and "Dropped" in rec_vl.name:
                    dropped_packets = rec_vl.getCount()
            report.add_line_v2(f"Total Frame Count", total_packets)
            report.add_line_v2(f"Dropped Frame Count", dropped_packets)
            report.add_line_v2(f"Dropped Frame Percentage", dropped_packets / total_packets if 0 != total_packets else 0)
            #report.pageBreak()

            # print histograms
            debugprint(f"      Will add Interarrival Histogram...")
            report.insertImage(f"{args.oPath}{figPath}VL{rvl}_InterArrival.png")
            debugprint(f"        {args.oPath}{figPath}VL{rvl}_InterArrival.png added")
            #report.pageBreak()

            debugprint(f"      Will add LatencyAt Histograms...")
            for rec in records:
                #debugprint(f"          Checking {rec} ->")
                if rvl == rec.no and "VL" == rec.type:
                    if "LatencyAt" in rec.name:
                        if len(rec.data) <= 1:
                            continue
                        debugprint(f"        {args.oPath}{figPath}Histogram_{rec.name}VL{rvl}.png")
                        #report.pageBreak()
                        report.add_line(f"    Histogram_{rec.name}VL{rvl}")
                        report.insertImage(f"{args.oPath}{figPath}Histogram_{rec.name}VL{rvl}.png")

            debugprint(f"      Will add all records...")
            for rn in rec_names:  # for all names
                if "Dropped" not in rn and "TrafficSource" not in rn:
                    for rec_vl in records_vl:  # in all VL records
                        if rvl == rec_vl.no and rn == rec_vl.name:  # if record no and name matches
                            debugprint(f"        {args.oPath}{figPath}{rec_vl.type}{rec_vl.no}_{rec_vl.name}.png")
                            #report.pageBreak()
                            report.add_line(f"    {rec_vl.type}{rec_vl.no}_{rec_vl.name}")
                            report.insertRecordDetailText(rec_vl, f"{args.oPath}{figPath}{rec_vl.type}{rec_vl.no}_{rec_vl.name}.png")

            print(f"    VL{rvl} is inserted")

    print(f"Saving report")
    # save
    report.savePDF()
    print(f"Report is ready at {args.oPath}{report.getFileName()}")


def printTextRecord(r, s):
    print(f"    {s}:")
    print(f"        Data count         : {r.getCount()}")
    print(f"        Final time         : {r.time[-1]}")
    print(f"        Maximum            : {r.getMax():.6f}")
    print(f"        Minimum            : {r.getMin():.6f}")
    if 0 != r.getMean() and r.getCount() >= 2:
        print(f"        {r.getMeanText().title():<19}: {r.getMean()}")
        if "QueueLength" not in r.name:
            print(f"        Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
            print(f"        Simulation mean is in {r.getConfidence99():.1f}% band of true mean with 99% confidence")
    gc.collect()


def printStatistics():
    # general statistics section ##############################################
    print(f"==========================================================================================")
    print(f"1. Overall Statistics")

    # insert summary text
    for orec in overall_records:
        printTextRecord(orec, f"{orec.name} for all {orec.type}")

    # per Switch statistics section(s) ########################################
    if not args.summaryOnly:
        print("2. Per-Switch Statistics")
        for rsw in rec_sws:
            i = rec_sws.index(rsw)
            print(f"        2.{i + 1}. SW{rsw} Statistics")
            for rn in rec_names:
                for r in records_sw:
                    if rsw == r.no and rn == r.name:
                        printTextRecord(r, f"        {r.name} for {r.type}{r.no}")

    # per VL statistics section(s) ############################################
    print("3. Per-VL Statistics")
    if not args.summaryOnly:
        for rvl in rec_vls:
            i = rec_vls.index(rvl)
            print(f"    3.{i + 1}. VL{rvl} Statistics")
            for rn in rec_names:
                for r in records_vl:
                    if rvl == r.no and rn == r.name:
                        printTextRecord(r, f"        {r.name} for {r.type}{r.no}")

    print(f"==========================================================================================")


def clean():
    global args
    global figPath
    shutil.rmtree(f"{args.oPath}{figPath}")


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
    myParser.add_argument('-debug',
                          help='If this flag is given, debug messages will be printed',
                          action="store_true")

    args = myParser.parse_args()

    debugprint = print if args.debug else lambda *a, **k: None

    if args.iPath is None:
        iPath = "./"
        print(f"Using current directory for simulation data.")
    else:
        if not args.iPath.endswith("/"):
            args.iPath += "/"
        print(f"Using '{args.iPath}' for simulation data.")
    if args.oPath is None:
        args.oPath = "./"
        print("Using current directory for outputs.")
    else:
        if args.oPath == "same":
            args.oPath = args.iPath
            print("Using input directory for outputs.")
        else:
            if not args.oPath.endswith("/"):
                args.oPath += "/"
            print(f"Using '{args.oPath}' for outputs.")
    if args.oFile is not None:
        figPath = f"{args.oFile}_{figPath}"

    # Get the data from simulation output
    getData()

    # Generate and save figures
    if not args.textOnly or args.keepFig:
        saveFigures()

    # Generate and save report or statistics
    if args.textOnly or args.figAndText:
        printStatistics()
    else:
        saveReport()

    # Clean temporary figures
    if not args.keepFig and not args.figAndText and not args.textOnly:
        clean()

    # Done!
