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


# Notes
Keep the config.ini in the same directory as the tool.

Install the required libraries using the provided requirements.txt. You can also set up a Python virtual environment.

Set up the Oracle environment on the lab before executing.

Update the Config file (config.ini) parameters.

Execute this script on the standby system to avoid disruptions.

After execution, the script will generate reports in CSV and TXT formats, providing detailed information about card counts based on their statuses.
