# Automatic Voucher Report Generation

## Overview
This README provides comprehensive instructions, including prerequisites, setup steps, and parameter configurations, 
making it easier for users to understand and use your script.


- **Title**: Automatic Voucher Report Generation
- **Author**: DEEWHY - Suleiman Dayo Abdullahi
- **Date**: 23 September 2023
- **Script Name**: auto_voucher_report_generation.py

## Description

This Python script automates the generation of voucher reports for Globacom. It performs the following tasks:

- Connects to an Oracle database to retrieve data related to card types and their statuses.
- Processes the data to calculate various counts, including activations, deactivations, expirations, etc.
- Generates CSV and TXT reports for two specific tables (UCMS_CARDS and Imported_Cards).
- Logs execution details in separate log files.

## Instructions

Before executing the tool, follow these steps:

1. Encrypt the Globacom RMS Oracle password by running the following script:
   ```bash
   python password_encryption.py

   
The script will prompt you to enter the Oracle password.
After execution, it will provide the encrypted password. Store it in the config.ini file for the password field.


# In case of using Python virtual environment
source rmsenv/bin/activate

# Execution Command
./auto_voucher_report_generation.py


Notes
Keep the config.ini in the same directory as the tool.

Install the required libraries using the provided requirements.txt. You can also set up a Python virtual environment.


[requirements.txt]
configparser==4.0.2
cx-Oracle==7.3.0
pandas==0.24.2
SQLAlchemy==1.4.23
virtualenv==20.7.2



Set up the Oracle environment on the lab before executing.

Update the following parameters in the Config file (config.ini):

[parameters]

Note: The placeholder parameters are generic and are placed there for understanding, thus doesn't contain any sensitive details of any company.

column_Params =type_name,status_name,serial_number                             # Column parameters in table in the database separated by ","
datetime_Params =time_used,system_date,date_expired,time_generated             # Timestamps for each status  and system date in the table separated by ","
status_Params ='active','utilize','inactive','expire','suspend','available'    # Unique status parameters in the status_name column separated by ","
source_tables =table1, table2                                                  # Source tables names. There can be two or more table names separated by ","
OracleUser =oracle_name                                                        # Database username
OraclePasswd =oracle_passwd                                                    # Database password
oracleRMS_servicename =servicename                                             
standby_ip =10.10.10.10                                                        
active_ip =127.0.0.1                                                           
port   =11111                                                                  # Standby server port number
oracle_port =22222                           # Active server Oracle port. Use command "sudo find . -type f -name listener.ora" on the server to find port.



Execute this script on the standby system to avoid disruptions.

After execution, the script will generate reports in CSV and TXT formats, providing detailed information about card counts based on their statuses.
