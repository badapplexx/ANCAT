import os
#import pandas as pd
import matplotlib.pyplot as plt
#from pylab import title, figure, xlabel, ylabel, xticks, bar, legend, axis, savefig
from fpdf import FPDF
from datetime import datetime
import statistics
import math
import gc

tg_95 = 1.96
tg_99 = 2.58

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
        return f"{self.index}: name='{self.name}{self.type}{self.no}', block='{self.block}', count='{len(self.data)}'"

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

def getData(dir):
    print(f"Reading directory contents {dir}")
    # vci file operations
    for file in os.listdir(dir):
        if file.endswith(".vci"):
            file_vci = open(os.path.join(dir, file))
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
    for file in os.listdir(dir):
        if file.endswith(".vec"):
            file_vec = open(os.path.join(dir, file))
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
    return records


def printMultiRecord(r):
    for i in range(len(r)):
        print(r[i], sep="\n")


def saveFigures(records):

    time_range_small = 0.02
    time_range_medium = 0.1

    # Individual figures ######################################################
    for rec in records:
        # 2D line plot
        plt.figure(figsize=(10, 10))
        plt.suptitle(f"{rec.name} for {rec.type}{rec.no}" + " in " + rec.block)

        plt.subplot(3,1,1)
        plt.grid(True)
        plt.xlabel("time")
        xdat = [xd for xd in rec.time if xd < time_range_small]
        ydat = rec.data[:len(xdat)]
        plt.plot(xdat, ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=10)

        plt.subplot(3,1,2)
        plt.grid(True)
        plt.xlabel("time")
        xdat = [xd for xd in rec.time if xd < time_range_medium]
        ydat = rec.data[:len(xdat)]
        plt.plot(xdat, ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=5)

        plt.subplot(3,1,3)
        plt.grid(True)
        plt.xlabel("time")
        plt.plot(rec.time, rec.data,
                 color="black",
                 linestyle="solid",
                 linewidth=1,
                 marker=".",
                 markersize=2)
        plt.savefig(f"{rec.type}{rec.no}_{rec.name}")
        plt.close()
        plt.clf()
        print(f"Printing individual figures: {int(100*(records.index(rec)+1)/len(records))}%")
        gc.collect()

    # Combined figures ########################################################
    rn = set()
    for x in records:
        rn.add(x.name)
    rec_names = list(rn)
    for r in rec_names:
        plt.figure(figsize=(10, 10))
        plt.suptitle(f"{r}")

        plt.grid(True)
        plt.xlabel("time")
        for x in records:
            if r == x.name:
                plt.subplot(3,1,1)
                plt.grid(True)
                plt.xlabel("time")
                xdat = [xd for xd in x.time if xd < time_range_small]
                ydat = x.data[:len(xdat)]
                plt.plot(xdat, ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=10,
                         label=f"{x.type}{x.no}")
                plt.subplot(3,1,2)
                plt.grid(True)
                plt.xlabel("time")
                xdat = [xd for xd in x.time if xd < time_range_medium]
                ydat = x.data[:len(xdat)]
                plt.plot(xdat, ydat,
                         linestyle="solid",
                         linewidth=1,
                         marker=".",
                         markersize=5,
                         label=f"{x.type}{x.no}")
                plt.subplot(3,1,3)
                plt.grid(True)
                plt.xlabel("time")
                plt.plot(x.time, x.data,
                         linestyle="solid",
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
                         label=f"{x.type}{x.no}")
        plt.legend()
        plt.savefig(f"Combined_{r}")
        plt.close()
        plt.clf()
        print(f"Printing combined figures: {int(100*(rec_names.index(r)+1)/len(rec_names))}%")
        gc.collect()


class Report(FPDF):
    def __init__(self):
        FPDF.__init__(self)
        self.now = datetime.now()
        self.set_title("ANCAT Simulation Results")
        self.set_author("ANCAT")

        self.add_page()

        # add title
        self.set_font("Courier", "B", 28)
        self.cell(0, 10, "ANCAT Simulation Results", 0, 1, "C")
        self.set_font("Courier", "B", 20)
        self.cell(0, 7, self.now.strftime("%H:%M    %m.%d.%Y"), 0, 1, "C")
        self.cell(0, 3, "", 0, 1)

    def add_heading_lvl1(self, s):
        self.set_font("Courier", "B", 18)
        self.cell(0, 5, "", 0, 1)
        self.cell(0, 10, s, 0, 1, "L")
        self.cell(0, 3, "", 0, 1)

    def add_heading_lvl2(self, s):
        self.set_font("Courier", "B", 14)
        self.cell(0, 2, "", 0, 1)
        self.cell(5)
        self.cell(0, 10, s, 0, 1, "L")

    def add_line(self, s):
        self.set_font("Courier", "", 12)
        self.cell(10)
        self.cell(0, 7, s, 0, 1, "L")

    def add_line_v2(self, s, d):
        self.set_font("Courier", "", 12)
        self.cell(10)
        self.cell(100, 7, s, 0, 0, "L")
        self.set_font("Courier", "B", 12)
        self.cell(100, 7, f"{d}", 0, 1, "L")

    def save(self):
        self.output(f"ANCAT_{self.now.strftime('%Y%m%d%H%M')}.pdf", 'F')

    def insertRecord(self, r, s):
        self.add_line_v2(f"    Maximum            : ", r.getMax())
        self.add_line_v2(f"    Minimum            : ", r.getMin())
        self.add_line_v2(f"    Mean               : ", r.getMean())
        if 0 != r.getMean():
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
            self.add_line(f"    Simulation mean is in {r.getConfidence99():.1f}% band of true mean with 99% confidence")
        self.image(s, x=None, y=None, w=200, h=0, type="", link="")
        gc.collect()

    def insertTextRecord(self, r, s):
        self.add_line(f"{s}:")
        self.add_line_v2(f"    Maximum            : ", r.getMax())
        self.add_line_v2(f"    Mean               : ", r.getMean())
        if 0 != r.getMean():
            self.add_line(f"    Simulation mean is in {r.getConfidence95():.1f}% band of true mean with 95% confidence")
        gc.collect()

def saveReport(records):
    report = Report()

    # general statistics section ##############################################
    print(f"Creating pdf report - General Statistics")
    report.add_heading_lvl1("1. General Statistics")
    report.add_heading_lvl2("1.1. Summary")
    for r in records:
        if "E2ELatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall E2ELatency")
    for r in records:
        if "ESBagLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall ESBagLatency")
    for r in records:
        if "ESSchedulingLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall ESSchedulingLatency")
    for r in records:
        if "ESTotalLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall ESTotalLatency")
    for r in records:
        if "SWQueueingTime" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall SWQueueingTime")
    for r in records:
        if "SWQueueLength" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.insertTextRecord(rall, "Overall SWQueueLength")

    for r in records:
        if "E2ELatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_E2ELatency")
    report.insertRecord(rall, "Combined_E2ELatency.png")
    print(f"    Combined_E2ELatency.png is inserted")
    for r in records:
        if "ESBagLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_ESBagLatency")
    report.insertRecord(rall, "Combined_ESBagLatency.png")
    print(f"    Combined_ESBagLatency.png is inserted")
    for r in records:
        if "ESSchedulingLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_ESSchedulingLatency")
    report.insertRecord(rall, "Combined_ESSchedulingLatency.png")
    print(f"    Combined_ESSchedulingLatency.png is inserted")
    for r in records:
        if "ESTotalLatency" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_ESTotalLatency")
    report.insertRecord(rall, "Combined_ESTotalLatency.png")
    print(f"    Combined_ESTotalLatency.png is inserted")
    for r in records:
        if "SWQueueingTime" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_SWQueueingTime")
    report.insertRecord(rall, "Combined_SWQueueingTime.png")
    print(f"    Combined_SWQueueingTime.png is inserted")
    for r in records:
        if "SWQueueLength" in r.name:
            rall = Record()
            rall.data += r.data
            rall.count += int(r.count)
    report.add_page()
    report.add_line(f"    Combined_SWQueueLength")
    report.insertRecord(rall, "Combined_SWQueueLength.png")
    print(f"    Combined_SWQueueLength.png is inserted")

    # per Switch statistics section(s) ########################################
    print(f"Creating pdf report - PerSwitch Statistics")
    report.add_page()
    report.add_heading_lvl1("2. Per-Switch Statistics")
    for r in records:
        if "SWQueueLength" in r.name:
            if 0 != records.index(r):
                report.add_page()
            report.insertRecord(r, f"{r.type}{r.no}_SWQueueLength.png")
            print(f"    {r.type}{r.no} is inserted")

    # per VL statistics section(s) ############################################
    print(f"Creating pdf report - PerVL Statistics")
    report.add_page()
    report.add_heading_lvl1("3. Per-VL Statistics")

    vls = (set())
    for r in records:
        if "VL" in r.type:
            vls.add(r.no)
    VL_set = list(vls)

    for vno in VL_set:
        i = VL_set.index(vno)
        report.add_page()
        report.add_heading_lvl2(f"3.{i+1}. VL{vno} Statistics")
        for r in records:
            if "E2ELatency" in r.name and "VL" == r.type and vno == r.no:
                report.add_line(f"    E2ELatency")
                report.insertRecord(r, f"VL{vno}_E2ELatency.png")
        for r in records:
            if "ESTotalLatency" in r.name and "VL" == r.type and vno == r.no:
                report.add_page()
                report.add_line(f"    ESTotalLatency")
                report.insertRecord(r, f"VL{vno}_ESTotalLatency.png")
        for r in records:
            if "ESSchedulingLatency" in r.name and "VL" == r.type and vno == r.no:
                report.add_page()
                report.add_line(f"    ESSchedulingLatency")
                report.insertRecord(r, f"VL{vno}_ESSchedulingLatency.png")
        for r in records:
            if "ESBagLatency" in r.name and "VL" == r.type and vno == r.no:
                report.add_page()
                report.add_line(f"    ESBagLatency")
                report.insertRecord(r, f"VL{vno}_ESBagLatency.png")
        for r in records:
            if "SWQueueingTime" in r.name and "VL" == r.type and vno == r.no:
                report.add_page()
                report.add_line(f"    SWQueueingTime")
                report.insertRecord(r, f"VL{vno}_SWQueueingTime.png")
        print(f"    VL{vno} is inserted")

    print(f"Saving report")
    # save
    report.save()
    print(f"Report is ready")


def clean():
    for file in os.listdir():
        if file.endswith(".png"):
            os.remove(file)
            #print(f"Removing file {file}")


if __name__ == "__main__":
    records = getData("C:\\Users\\ozerg\\Desktop\\Share\\tez\\portProcessing\\this")
    #records = getData("C:\\Workspaces\\Github\\AFDX\\simulations\\results")
    #printMultiRecord(records)
    saveFigures(records)
    saveReport(records)
    clean()
