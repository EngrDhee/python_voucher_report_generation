#!/usr/bin/python
"""
Title: Automatic Voucher Report Generation
Author: DEEWHY - Suleiman Dayo Abdullahi
Script Name: auto_voucher_report_generation.py

Description:
This Python script connects to an Oracle database to retrieve data related to card types and their statuses.
It processes the data to calculate various counts, including activations, deactivations, and expirations.
The script generates CSV and TXT reports for two specific tables (UCMS_CARDS and Imported_Cards).
Execution details are logged in separate log files.

Instructions:
1. Ensure Python is installed on your system.
2. Save the script as auto_voucher_report_generation.py.
3. Ensure you have the required modules (pandas, os, sys, time, datetime, ConfigParser, logging, socket, sqlalchemy).
   These modules are generally available with standard Python installations.
4. Create a configuration file named config.ini in the same directory as the script. Ensure it contains the necessary parameters like Oracle credentials, service name, etc.
5. Run the script using Python by executing the following command:
    python auto_voucher_report_generation.py

Note: Execute this script on the standby system to avoid disruptions.

After execution, the script will generate reports in CSV and TXT formats providing detailed information about card counts based on their statuses.

"""

import pandas as pd
import os
import sys
import time
import datetime
import ConfigParser
import logging
import socket
import sqlalchemy
import cx_Oracle
from sqlalchemy.exc import SQLAlchemyError

# Set environment variables for Oracle Client
os.environ['LD_LIBRARY_PATH'] = '/opt/oracle/product/19.0.0'
os.environ['ORACLE_HOME'] = '/opt/oracle/product/19.0.0'


def decrypt(key, encrypted):
    """
    Decrypts an encrypted message using a simple Caesar cipher.

    Parameters:
    - key (str): The decryption key.
    - encrypted (str): The message to be decrypted.

    Returns:
    - str: The decrypted message.
    """
    decrypted_msg = [chr((ord(c) - ord(key[i % len(key)])) % 127) for i, c in enumerate(encrypted)]
    return ''.join(decrypted_msg)


def setup_logging(workdir, now, logdirname):
    """
    Set up logging configuration.

    Parameters:
    - workdir (str): The working directory.
    - now (datetime): The current date and time.
    - logdirname (str): The directory for log files.
    """
    logfilename = logdirname + '/' + now.strftime('rmsReportingTool_%d%m%Y_%H%M.log')
    if not os.path.exists(logdirname):
        os.makedirs(logdirname)
    logging.basicConfig(
        filename=logfilename, filemode='w',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def card_count(source_tables, oracle_user, oracle_passwd, service_nm, csvname1, csvname2, name1, name2, logs, column_params, status_params, datetime_params):
    """
    Performs card count analysis based on various parameters.

    Parameters:
    - source_tables (list): List of tables to analyze.
    - oracle_user (str): Oracle database username.
    - oracle_passwd (str): Decrypted Oracle database password.
    - service_nm (str): Oracle service name.
    - csvname1 (str): Path for the CSV report for UCMS_CARDS.
    - csvname2 (str): Path for the CSV report for Imported_Cards.
    - name1 (str): Path for the TXT report for UCMS_CARDS.
    - name2 (str): Path for the TXT report for Imported_Cards.
    - logs: Logging information.
    - column_params (list): List of column parameters.
    - status_params (list): List of status parameters.
    - datetime_params (list): List of datetime parameters.
    """
    try:
        conn_str = ('oracle+cx_oracle://{un}:{psd}@{sn}'.format(un=oracle_user,psd=oracle_passwd,sn=service_nm))
        engine = sqlalchemy.create_engine(conn_str)

        for table in source_tables:
            query = """
            SELECT
                CAST ({column_params[0]} AS integer) CARD_TYPE,
                COUNT(case when {column_params[1]}={status_params[0]} THEN 1 end ) ACTIVATED,
                COUNT(case when {column_params[1]}={status_params[1]} AND {datetime_params[0]} < trunc({datetime_params[1]}) THEN 1 end ) TOTAL_USED,
                COUNT(case when {column_params[1]}={status_params[4]} THEN 1 end ) DEACTIVATED,
                COUNT(case when {column_params[1]}={status_params[2]} AND {datetime_params[2]} < trunc({datetime_params[1]}) THEN 1 end ) EXPIRED,
                COUNT(case when {column_params[1]}={status_params[5]} AND {datetime_params[3]} < trunc({datetime_params[1]}) THEN 1 end ) NEW,
                COUNT(case when {column_params[1]}={status_params[3]} THEN 1 end ) BOOKEDIN,
                COUNT(case when {column_params[1]}={status_params[0]} THEN 1 end ) +
                    COUNT(case when {column_params[1]}={status_params[1]} AND {datetime_params[0]} < trunc({datetime_params[1]}) THEN 1 end ) +
                    COUNT(case when {column_params[1]}={status_params[4]} THEN 1 end ) +
                    COUNT(case when {column_params[1]}={status_params[2]} AND {datetime_params[2]} < trunc({datetime_params[1]}) THEN 1 end ) +
                    COUNT(case when {column_params[1]}={status_params[5]} AND {datetime_params[3]} < trunc({datetime_params[1]}) THEN 1 end ) +
                    COUNT(case when {column_params[1]}={status_params[3]} THEN 1 end ) AS TOTAL,
                COUNT(case when {column_params[1]}={status_params[1]} AND {datetime_params[0]} >= trunc({datetime_params[1]} - 1)
                    AND {datetime_params[0]}<trunc({datetime_params[1]}) THEN 1 end ) DAILY_USED
            FROM {table}
            WHERE {column_params[2]} is not null
            GROUP BY {column_params[0]}
            ORDER BY {column_params[0]}
            """
            logging.info("Fetching the data for table %s", table)
            df = pd.read_sql(query.format(
                table=table, column_params=column_params, status_params=status_params, datetime_params=datetime_params
            ), engine, index_col=column_params[0]
            )

            if isinstance(df, pd.DataFrame):
                tot_rows = df.shape[0]
                logging.info("Total records in table %s with select conditions are %s", table, str(tot_rows))

                if table == source_tables[0]:
                    df = df.sort_index(axis=0, ascending=False)
                    df.to_csv(csvname1, mode='a', header=True)
                    df_str = df.to_string(index=True)
                    with open(name1, 'w') as file:
                        file.write(df_str + '\n')

                else:
                    df.to_csv(csvname2, mode='a', header=True)
                    df_str = df.to_string(index=True)
                    with open(name2, 'w') as file:
                        file.write(df_str + '\n')

            else:
                logging.info("No records found for all cards count case in table %s", table)

    except SQLAlchemyError as e:
        logging.info("TIME: " + str(time.strftime("%H:%M:%S", time.localtime(time.time()))) +
                     "Error occurred while connecting and fetching select query results" + str(e))
        print(e)


def main():
    workdir = os.getcwd()
    now = datetime.datetime.now()

    logdirname = workdir + '/' + now.strftime('rmsReporting_%d%m%Y%H%M')
    logs = setup_logging(workdir, now, logdirname)

    logging.info('Log Execution Directory is at path :%s', logdirname)

    fnm = "config1.ini"
    cf = ConfigParser.ConfigParser(allow_no_value=True)
    a = cf.read(os.path.join(workdir, fnm))

    if len(a) == 0:
        logging.info("ERROR: Configuration file config.ini not found in Current Working directory :%s", workdir)
        sys.exit()

    ipchk = cf.get('parameters', 'mated_ip')
    port = cf.get('parameters', 'port')
    actip = cf.get('parameters', 'rms_ip')
    dbport = cf.get('parameters', 'oracle_port')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    res = sock.connect_ex((ipchk, int(port)))

    if res == 0:
        logging.info("The server is not standby. Please execute this script on a standby system")
        sys.exit()

    column_params = cf.get('parameters', 'ColumnParams').split(',')
    datetime_params = cf.get('parameters', 'DateTimeParams').split(',')
    status_params = cf.get('parameters', 'StatusParams').split(',')
    source_tables = cf.get('parameters', 'SourceTable').split(',')
    oracle_user = cf.get('parameters', 'OracleUser')
    oracle_passwd_enc = cf.get('parameters', 'OraclePasswd')
    service_nm = cf.get('parameters', 'oracleRMS_servicename')
    service_nm = cf.get('parameters', 'oracleRMS_servicename')

    key = "password encryption"
    oracle_passwd = decrypt(key, oracle_passwd_enc)

    csvname1 = logdirname + '/' + now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.csv')
    csvname2 = logdirname + '/' + now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.csv')
    name1 = logdirname + '/' + now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.txt')
    name2 = logdirname + '/' + now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.txt')

    logging.info("Starting the select query, count and its result analysis")

    card_count(source_tables, oracle_user, oracle_passwd, service_nm, csvname1, csvname2, name1, name2, logs, column_params,
               status_params, datetime_params)

    logging.info('Tool Execution Ended ')


if __name__ == '__main__':
    main()
