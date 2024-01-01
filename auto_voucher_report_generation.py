#!/usr/bin/python

"""
Title: Generate Automotically Voucher Report
Author: DEEWHY - Suleiman Dayo Abdullahi
Script Name: auto_voucher_report_generation.py

Description:
This Python script performs the following tasks:
- Connects to an Oracle database to retrieve data related to card types and their statuses.
- Processes the data to calculate various counts including activations, deactivations, expirations, etc.
- Generates CSV and TXT reports for two specific tables (UCMS_CARDS and Imported_Cards).
- Logs execution details in separate log files.

Instructions:
1. Ensure you have Python installed on your system.
2. Save the script code in a file named auto_voucher_report_generation.py.
3. Make sure to have the required modules (pandas, os, sys, time, datetime, ConfigParser, logging, socket, sqlalchemy).
   These modules are generally available with standard Python installations.
4. Create a configuration file named config.ini in the same directory as the script. Ensure it contains the necessary parameters like Oracle credentials, service name, etc.
5. Run the script using Python by executing the following command:
    python auto_voucher_report_generation.py

Note: Make sure to execute this script on the standby system to avoid any disruptions.

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

os.environ['LD_LIBRARY_PATH'] = '/opt/oracle/product/19.0.0'
os.environ['ORACLE_HOME'] = '/opt/oracle/product/19.0.0'    
    
def decrypt(key, encryped):
    msg = []
    for i, c in enumerate(encryped):
        key_c = ord(key[i % len(key)])
        enc_c = ord(c)
        msg.append(chr((enc_c - key_c) % 127))
    return ''.join(msg)



def setup_logging(workdir, now, logdirname):
    logfilename = logdirname+'/'+now.strftime('rmsReportingTool_%d%m%Y_%H%M.log')
    if not os.path.exists(logdirname):
        os.makedirs(logdirname)
    logging.basicConfig(filename=logfilename, filemode='w',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')



def card_count(source_tables, oracle_user, oracle_passwd, service_nm, csvname1, csvname2, name1, name2, logs):

    try:
        conn_str=('oracle+cx_oracle://{un}:{psd}@{sn}'.format(un=oracle_user,psd=oracle_passwd,sn=service_nm))
        engine = sqlalchemy.create_engine(conn_str)
    
        for table in source_tables:
            query = """
            SELECT 
                CAST (CARD_TYPE AS integer) CARD_TYPE,
                COUNT(case when CARD_STATUS='activated' THEN 1 end ) ACTIVATED,
                COUNT(case when CARD_STATUS='used' AND used_time < trunc(sysdate) THEN 1 end ) TOTAL_USED,
                COUNT(case when CARD_STATUS='deactivated' THEN 1 end ) DEACTIVATED,
                COUNT(case when CARD_STATUS='expired' AND expiry_date < trunc(sysdate) THEN 1 end ) EXPIRED,
                COUNT(case when CARD_STATUS='new' AND generated_time < trunc(sysdate) THEN 1 end ) NEW,
                COUNT(case when CARD_STATUS='bookedin' THEN 1 end ) BOOKEDIN,
                COUNT(case when CARD_STATUS='activated' THEN 1 end ) + 
                COUNT(case when CARD_STATUS='used' AND used_time < trunc(sysdate) THEN 1 end ) + 
                COUNT(case when CARD_STATUS='deactivated' THEN 1 end ) + 
                COUNT(case when CARD_STATUS='expired' AND expiry_date < trunc(sysdate) THEN 1 end ) + 
                COUNT(case when CARD_STATUS='new' AND generated_time < trunc(sysdate) THEN 1 end ) + 
                COUNT(case when CARD_STATUS='bookedin' THEN 1 end ) AS TOTAL,
                COUNT(case when CARD_STATUS='used' AND used_time >= trunc(sysdate - 1) AND used_time<trunc(sysdate) THEN 1 end ) DAILY_USED
            FROM {}
            WHERE SERIAL_NO is not null 
            GROUP BY CARD_TYPE
            ORDER BY CARD_TYPE
            """
            logging.info("Fetching the data for table %s",table)
            df = pd.read_sql(query.format(table), engine, index_col = 'card_type')

            if isinstance(df, pd.DataFrame):
                tot_rows = df.shape[0]
                logging.info("Total records in table %s with select conditions are %s",table,str(tot_rows))
     
                if table == "UCMS_CARDS":
                    df.to_csv(csvname1,mode='a',header = True)
                    df_str = df.to_string(index=True)
                    with open(name1, 'w') as file:
                        file.write(df_str + '\n')
                    
                else:
                    df.to_csv(csvname2,mode='a',header = True)
                    df_str = df.to_string(index=True)
                    with open(name2, 'w') as file:
                        file.write(df_str + '\n')
                    
            else:
                logging.info("No records found for all cards count case in table %s",table)
            
        
    except SQLAlchemyError as e:
       logging.info("TIME : "+str(time.strftime("%H:%M:%S", time.localtime(time.time())))+"Error occurred while connecting and fetching select query results"+str(e)) 
       print(e)




def main():

    workdir=os.getcwd()
    now = datetime.datetime.now()

    logdirname = workdir+'/'+now.strftime('rmsReporting_%d%m%Y%H%M')
    logs = setup_logging(workdir, now, logdirname)
    
    logging.info('Log Execution Directory is at path :%s',logdirname)
    
    fnm="config.ini"
    cf=ConfigParser.ConfigParser(allow_no_value=True)
    a=cf.read(os.path.join(workdir,fnm))
    
    if len(a)==0:
            logging.info("ERROR: Configuration file config.ini not found in Current Working directory :%s",workdir) 
            sys.exit()
            
    ipchk = cf.get('parameters', 'mated_ip')
    port = cf.get('parameters', 'port')
    actip = cf.get('parameters','rms_ip')
    dbport = cf.get('parameters','oracle_port')
    
    
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    res = sock.connect_ex((ipchk,int(port)))
    #print(res) 
    
    if res == 0:
        logging.info("The server is not standby. Please execute this script on standby system")
        sys.exit()
    
    source_tables = cf.get('parameters', 'SourceTable').split(',')
    oracle_user = cf.get('parameters', 'OracleUser')
    oracle_passwd_enc = cf.get('parameters', 'OraclePasswd')
    service_nm=cf.get('parameters','oracleRMS_servicename')
    service_nm=cf.get('parameters','oracleRMS_servicename')  
    
    key = "password encryption"
    oracle_passwd = decrypt(key, oracle_passwd_enc)
    #print oracle_passwd

    
    csvname1=logdirname+'/'+now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.csv') 
    csvname2=logdirname+'/'+now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.csv')
    name1=logdirname+'/'+now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.txt')
    name2=logdirname+'/'+now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.txt') 
    
    logging.info("Starting the select query, count and its result analysis")

    card_count(source_tables, oracle_user, oracle_passwd, service_nm, csvname1, csvname2, name1, name2, logs)

    logging.info('Tool Execution Ended ')



if __name__ == '__main__':
    main()
