python PreProcessor.py -i D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\results\Config_Exp12.xlsx -o D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\omnetpp
python PreProcessor.py -i D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\results\Config_Exp12.xlsx -o C:\Workspaces\Github\AFDX\simulations
python SimProcessor.py -omnetPath C:\omnetpp-5.6.2 -afdxPath C:\Workspaces\Github\AFDX 
PAUSE
copy C:\Workspaces\Github\AFDX\simulations\results\General-#0.vec D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\omnetpp
copy C:\Workspaces\Github\AFDX\simulations\results\General-#0.vci D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\omnetpp
python PostProcessor.py -iPath D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\omnetpp -oPath D:\Documents\docs-tez-depo\ThesisWork\ANCAT\Exp1\12\results -oFile exp12
PAUSE
