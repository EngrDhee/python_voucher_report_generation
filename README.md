Title : Globacom Voucher Report Generation
Author : DEEWHY - Suleiman Dayo Abdullahi
Date : 23 September,2023
Script Name: auto_voucher_report_generation.py


Description:
This Python script performs the following tasks:
- Connects to an Oracle database to retrieve data related to card types and their statuses.
- Processes the data to calculate various counts including activations, deactivations, expirations, etc.
- Generates CSV and TXT reports for two specific tables (UCMS_CARDS and Imported_Cards).
- Logs execution details in separate log files.


Instructions:
Before execution of the tool please encrypt the Gloabacom RMS oracle password by following script
Command : python password_encryption.py  
Script will prompt tp ask for the password . Enter the oracle password.
* After the execution, script will provide the encrypted password. Please store it in the config.ini file for password field.  

RMS Voucher Report Generation Tool Execution steps :-

1)  source rmsenv/bin/activate  (In case of using python virtual environment)
2)  Execution Command : ./auto_voucher_report_generation.py

Note : 
1) Please keep the config.ini in same directory as Tool
2) Please install the panda,cx_Oracle,sqlalchemy libraries compatible with python v2.7.5 . For this you can Also setup the python virtual environment

[requirement.txt]
configparser==4.0.2
cx-Oracle==7.3.0
pandas==0.24.2
SQLAlchemy==1.4.23
virtualenv==20.7.2

3) Also before executing please setup the orcale environment on the lab
4) Please update the following parameters in Config file :-

[parameters]
column_Params                #### Column output paramereters of the table in the database that is needed in the query of card serials separated by ",".
datetime_Params              #### Timestamps for each status in a column of the table to query and the system time separated by ",".
status_Params                #### Status paramereters of different categories separated by ",".
source_tables                #### source tables names .There can be two or more table names separated by "," 
OracleUser                   ### rms database username
OraclePasswd                 ### rms password
oracleRMS_servicename
standby_ip
active_ip
port                         #### standby server port number
oracle_port                  ##### Active server oracle port . Use command  "sudo find . -type f -name listener.ora" on the server to find port.
5) Make sure to execute this script on the standby system to avoid any disruptions.
6) After execution, the script will generate reports in CSV and TXT formats providing detailed information about card counts based on their statuses.
