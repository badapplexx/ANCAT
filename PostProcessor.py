import os
import pandas as pd
import matplotlib.pyplot as plt
from pylab import title, figure, xlabel, ylabel, xticks, bar, legend, axis, savefig
from fpdf import FPDF
from datetime import datetime
import statistics


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
        return statistics.pstdev(self.data)


def getData(dir):
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
                records[i].count = data_lines_splitted[i][7]
                name_splitted = vector_lines_splitted[i][3].split("_")
                records[i].name = name_splitted[0]
                for c in name_splitted[1]:
                    if c.isdigit():
                        ind = name_splitted[1].index(c)
                        records[i].type = name_splitted[1][:ind]
                        records[i].no = int(name_splitted[1][ind:])
                        break

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

    time_range_small = 0.02
    time_range_medium = 0.1

    for rec in records:
        # 2D line plot
        plt.figure(figsize=(10, 10))
        plt.suptitle(f"{rec.name} for {rec.type}{rec.no}" + " in " + records[0].block)

        plt.subplot(3,1,1)
        plt.grid(True)
        plt.xlabel("time")
        xdat = [xd for xd in rec.time if xd < time_range_small]
        ydat = rec.data[:len(xdat)]
        plt.plot(xdat, ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=0.5,
                 marker=".",
                 markersize=5)

        plt.subplot(3,1,2)
        plt.grid(True)
        plt.xlabel("time")
        xdat = [xd for xd in rec.time if xd < time_range_medium]
        ydat = rec.data[:len(xdat)]
        plt.plot(xdat, ydat,
                 color="black",
                 linestyle="solid",
                 linewidth=0.5,
                 marker=".",
                 markersize=2)

        plt.subplot(3,1,3)
        plt.grid(True)
        plt.xlabel("time")
        plt.plot(rec.time, rec.data,
                 color="black",
                 linestyle="solid",
                 linewidth=0.5)
        plt.savefig(f"{rec.name}{rec.type}{rec.no}")
        plt.close()
        print(f"Printing all figures: {int(100*(records.index(rec)+1)/len(records))}%")

    rec_names = set()
    for x in records:
        rec_names.add(x.name)

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
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
                         label=f"{x.type}{x.no}")
                plt.subplot(3,1,2)
                plt.grid(True)
                plt.xlabel("time")
                xdat = [xd for xd in x.time if xd < time_range_medium]
                ydat = x.data[:len(xdat)]
                plt.plot(xdat, ydat,
                         linestyle="solid",
                         linewidth=0.5,
                         marker=".",
                         markersize=2,
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
        plt.savefig(f"{r}_all")
        plt.close()
        print(f"Printing combined figures: {int(100*(rec_names.index(r)+1)/len(rec_names))}%")

    # 2D line plot
    plt.xlabel("time")
    plt.ylabel("data")
    plt.plot(records[0].time, records[0].data,
              color="black",
              linestyle="dashed",
              linewidth=1,
              marker=".",
              markerfacecolor="black",
              markersize=1,
              label="mylabel")

    plt.title(records[0].name + " in " + records[0].block)
    #plt.savefig('plot_2d.png')

    # histogram plot
    rng = (0, 5)
    bins = 1
    plt.hist(records[1].data, bins, rng,
              histtype="bar",
              rwidth=0.8)
    #plt.savefig('plot_histogram.png')

    # scatter plot
    rng = (0, 5)
    bins = 1
    plt.scatter(records[2].time,
                 records[2].data,
                 marker=".",
                 s=30)
    #plt.savefig('plot_scatter.png')


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
    records = getData("C:\\Users\\ozerg\\Desktop\\Share\\tez\\portProcessing\\this\\Experiment2")
    # printMultiRecord(records)
    saveFigures(records)
    # saveReport(records)
