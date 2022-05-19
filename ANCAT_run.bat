set OMNET_PATH=C:\omnetpp-6.0
set AFDX_PATH=C:\Workspaces\Github\AFDX_6
set XLSX_PATH=C:\Workspaces\Github\ANCAT
set XLSX_NAME=Config_Exp2.xlsx
set REPORT_PATH=C:\Workspaces\Github\ANCAT
set REPORT_NAME=exp2

python PreProcessor.py -i %XLSX_PATH%\%XLSX_NAME% -o %AFDX_PATH%\afdx\simulations
python SimProcessor.py -omnetPath %OMNET_PATH% -afdxPath %AFDX_PATH%
python PostProcessor.py -iPath %AFDX_PATH%\afdx\simulations\results -oPath %REPORT_PATH% -oFile %REPORT_NAME%
PAUSE
