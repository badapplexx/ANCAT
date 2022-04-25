set OMNET_PATH=C:\omnetpp-5.7
set AFDX_PATH=C:\omnetpp-5.7\samples\AFDX-Master-git
set XLSX_PATH=C:\Users\ozerg\Desktop\Share\ANCAT\input_data\Exp20
set XLSX_NAME=Config.xlsx
set REPORT_PATH=C:\Users\ozerg\Desktop
set REPORT_NAME=exp20

PreProcessor.exe -i %XLSX_PATH%\%XLSX_NAME% -o %AFDX_PATH%\simulations
SimProcessor.exe -omnetPath %OMNET_PATH% -afdxPath %AFDX_PATH% 
PostProcessor.exe -iPath %AFDX_PATH%\simulations\results -oPath %REPORT_PATH% -oFile %REPORT_NAME%
PAUSE
