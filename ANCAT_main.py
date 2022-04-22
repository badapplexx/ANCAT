import os
import argparse


if(False):
    omnet_path = "C:/omnetpp-5.7"
    xlsx_file_name = "C:/Users/ozerg/Desktop/Share/ANCAT/input_data/Exp2/Config_Exp2.xlsx"
    afdx_model_path = "C:/omnetpp-5.7/samples/AFDX-Master-git"
    report_path = "C:/Users/ozerg/Desktop/"
    report_name = "exp2"
else:
    myParser = argparse.ArgumentParser(description="ANCAT")

    # Add the arguments
    myParser.add_argument('-omnetPath',
                          metavar="<input path>",
                          type=str,
                          help='Location of the omnetpp installation',
                          required=True)
    myParser.add_argument('-afdxPath',
                          metavar="<Output path>",
                          type=str,
                          help='Location of the AFDX model (project)',
                          required=True)
    myParser.add_argument('-xlsx',
                          metavar="<Output path>",
                          type=str,
                          help='Location of the input xlsx file',
                          required=True)
    myParser.add_argument('-reportPath',
                          metavar="<Output path>",
                          type=str,
                          help='Location of the ANCAT report ouutput',
                          required=True)
    myParser.add_argument('-reportName',
                          metavar="<Output path>",
                          type=str,
                          help='Special name for the report',
                          required=False)
    myParser.add_argument('-keepFig',
                          help='If this flag is given, mid-process figures will not be deleted.',
                          action="store_true")

    args = myParser.parse_args()
    omnet_path = args.omnetPath
    xlsx_file_name = args.xlsx
    afdx_model_path = args.afdxPath
    report_path = args.reportPath
    report_name = " -oFile " + args.reportName if args.reportName is not None else ""
    keepFig = " -keepFig" if args.keepFig else ""

os.system("python PreProcessor.py"
          + " -iPath " + xlsx_file_name
          + " -oPath " + afdx_model_path + "/simulations")
os.system("python SimProcessor.py"
          + " -omnetPath " + omnet_path
          + " -afdxPath " + afdx_model_path)
os.system("python PostProcessor.py"
          + " -iPath " + afdx_model_path + "/simulations/results/"
          + " -oPath " + report_path
          + report_name
          + keepFig)



