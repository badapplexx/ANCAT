import os
import pandas as pd
import matplotlib.pyplot as plot
from pylab import title, figure, xlabel, ylabel, xticks, bar, legend, axis, savefig
from fpdf import FPDF
from datetime import datetime
import statistics
from enum import Enum


class RecordType(Enum):
    NONE = 0
    PER_VL = 1
    PER_SWITCH = 2


class Record:
    def __init__(self):
        self.index = -1
        self.block = ""
        self.name = ""
        self.type = RecordType.NONE
        self.id = -1
        self.count = 0
        self.time = []
        self.data = []

    def __str__(self):
        return f"{self.index}: name='{self.name}#{self.id}', block='{self.block}', count='{len(self.data)}'"

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
        return statistics.pstdev(self.data)


def getData(dir):
    # vci file operations
    for file in os.listdir(dir):
        if file.endswith(".vci"):
            file_vci = open(os.path.join(dir, file))
            lines_vci = file_vci.readlines()
            vector_lines = [x for x in lines_vci if "vector" in x]
            vector_lines_splitted = list(map(str.split, vector_lines))
            dataCount = len(vector_lines)
            data_lines = lines_vci[-dataCount - 1:]
            data_lines_splitted = list(map(str.split, data_lines))
            records = [Record() for i in range(dataCount)]
            for i in range(dataCount):
                records[i].index = i
                records[i].block = vector_lines_splitted[i][2]
                records[i].count = data_lines_splitted[i][7]
                name_splitted = vector_lines_splitted[i][3].split("_")
                records[i].name = name_splitted[0]
                if("VL" in name_splitted[1]):
                    records[i].type = RecordType.PER_VL
                    records[i].id = int(name_splitted[1][2:])
                elif("SW" in name_splitted[1]):
                    records[i].type = RecordType.PER_SWITCH
                    records[i].id = int(name_splitted[1][2:])
                else:
                    records[i].type = RecordType.NONE
                    records[i].id = int(name_splitted[1])

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
    return records


def printMultiRecord(r):
    for i in range(len(r)):
        print(r[i], sep="\n")


def saveFigures(records):
    # 2D line plot
    plot.xlabel("time")
    plot.ylabel("data")
    plot.plot(records[0].time, records[0].data,
              color="black",
              linestyle="dashed",
              linewidth=1,
              marker=".",
              markerfacecolor="black",
              markersize=1,
              label="mylabel")

    plot.title(records[0].name + " in " + records[0].block)
    plot.savefig('plot_2d.png')

    # histogram plot
    rng = (0, 5)
    bins = 1
    plot.hist(records[1].data, bins, rng,
              histtype="bar",
              rwidth=0.8)
    plot.savefig('plot_histogram.png')

    # scatter plot
    rng = (0, 5)
    bins = 1
    plot.scatter(records[2].time,
                 records[2].data,
                 marker=".",
                 s=30)
    plot.savefig('plot_scatter.png')


class Report(FPDF):
    def __init__(self):
        FPDF.__init__(self)
        self.now = datetime.now()
        self.set_title("ANCAT Simulation Results")
        self.set_author("ANCAT")

        self.add_page()

        # add title
        self.set_font("Arial", "B", 28)
        self.cell(0, 10, "ANCAT Simulation Results", 0, 1, "C")
        self.set_font("Arial", "B", 20)
        self.cell(0, 7, self.now.strftime("%H:%M    %m.%d.%Y"), 0, 1, "C")
        self.cell(0, 3, "", 0, 1)

    def add_heading_lvl1(self, s):
        self.set_font("Arial", "B", 18)
        self.cell(0, 5, "", 0, 1)
        self.cell(0, 10, s, 0, 1, "L")
        self.cell(0, 3, "", 0, 1)

    def add_heading_lvl2(self, s):
        self.set_font("Arial", "B", 14)
        self.cell(0, 2, "", 0, 1)
        self.cell(5)
        self.cell(0, 10, s, 0, 1, "L")

    def add_line(self, s):
        self.set_font("Arial", "", 12)
        self.cell(10)
        self.cell(0, 7, s, 0, 1, "L")

    def add_line_v2(self, s, d):
        self.set_font("Arial", "", 12)
        self.cell(10)
        self.cell(100, 7, s, 0, 0, "L")
        self.set_font("Arial", "B", 12)
        self.cell(100, 7, f"{d}", 0, 1, "L")

    def save(self):
        self.output(f"ANCAT_{self.now.strftime('%Y%m%d%H%M')}.pdf", 'F')


def saveReport(records):
    report = Report()

    # general statistics section
    report.add_heading_lvl1("1. General Statistics")
    report.add_line(f"- Maximum end-to-end latency1: {3.14159}")
    report.add_line(f"- Maximum end-to-end latency2: {2.14159}")
    report.add_line(f"- Maximum end-to-end latency3: {1.14159}")
    report.add_line(f"- Maximum end-to-end latency4: {0.14159}")

    # per VL statistics section(s)
    report.add_heading_lvl1("2. Per-VL Statistics")
    report.add_heading_lvl2("2.a. VL#0")
    report.add_line_v2("- Maximum end-to-end latency4:", 0.14159)
    report.add_line_v2("- Maximum end-to-end latency4:", 0.14159)
    report.add_line_v2("- Maximum end-to-end latency4:", 0.14159)
    report.add_line_v2("- Maximum end-to-end latency4:", 0.14159)
    report.image("plot_2d.png", x=None, y=None, w=50, h=0, type="", link="")
    report.add_line("width: 50")
    report.image("plot_2d.png", x=None, y=None, w=100, h=0, type="", link="")
    report.add_line("width: 100")
    report.image("plot_2d.png", x=None, y=None, w=200, h=0, type="", link="")
    report.add_line("width: 200")


    # save
    report.save()


if __name__ == "__main__":
    records = getData(".")
    printMultiRecord(records)
    # saveFigures(records)
    # saveReport(records)
