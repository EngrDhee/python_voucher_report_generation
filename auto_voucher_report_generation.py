#!/usr/bin/python

# Import necessary libraries
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
    # Decrypt message using Caesar cipher
    decrypted_msg = [chr((ord(c) - ord(key[i % len(key)])) % 127) for i, c in enumerate(encrypted)]
    return ''.join(decrypted_msg)


def server_login(cf):
    """
    Checks if the server is on standby.

    Parameters:
    - cf: ConfigParser object containing parameters.

    Exits the script if the server is not on standby.
    """
    # Extract parameters from the configuration file
    ipchk = cf.get('parameters', 'mated_ip')
    port = cf.get('parameters', 'port')
    actip = cf.get('parameters', 'rms_ip')
    dbport = cf.get('parameters', 'oracle_port')

    # Check if the server is on standby
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    res = sock.connect_ex((ipchk, int(port)))

    if res == 0:
        logging.info("The server is not standby. Please execute this script on a standby system")
        sys.exit()


def setup_logging(workdir, now, logdirname):
    """
    Set up logging configuration.

    Parameters:
    - workdir (str): The working directory.
    - now (datetime): The current date and time.
    - logdirname (str): The directory for log files.
    """
    # Set up logging file configuration
    logfilename = logdirname + '/' + now.strftime('rmsReportingTool_%d%m%Y_%H%M.log')
    if not os.path.exists(logdirname):
        os.makedirs(logdirname)
    logging.basicConfig(
        filename=logfilename, filemode='w',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def query_db_4_count(oracle_passwd, logs, cf):
    """
    Performs card count analysis based on various parameters.

    Parameters:
    - oracle_passwd (str): Decrypted Oracle database password.
    - logs: Logging information.
    - cf: ConfigParser object containing parameters.

    Returns:
    - tuple: (df_map: dict, source_tables: list)
    """
    # Extract parameters from the configuration file
    column_params = cf.get('parameters', 'ColumnParams').split(',')
    datetime_params = cf.get('parameters', 'DateTimeParams').split(',')
    status_params = cf.get('parameters', 'StatusParams').split(',')
    source_tables = cf.get('parameters', 'SourceTable').split(',')
    oracle_user = cf.get('parameters', 'OracleUser')
    service_nm = cf.get('parameters', 'oracleRMS_servicename')

    try:
        # Create connection string for Oracle database
        conn_str = ('oracle+cx_oracle://{un}:{psd}@{sn}'.format(un=oracle_user,psd=oracle_passwd,sn=service_nm))
        engine = sqlalchemy.create_engine(conn_str)

        logging.info("Starting the select query, count, and result analysis")
        df_map = {}

        # Iterate through each table for analysis
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

            # Execute SQL query and store results in a Pandas DataFrame
            df = pd.read_sql(query.format(
                table=table, column_params=column_params, status_params=status_params, datetime_params=datetime_params
            ), engine, index_col=column_params[0]
            )
            df_map[table] = df

        return df_map, source_tables

    except SQLAlchemyError as e:
        logging.info("TIME: " + str(time.strftime("%H:%M:%S", time.localtime(time.time()))) +
                     "Error occurred while connecting and fetching select query results" + str(e))
        print(e)


def convert_df_2_csv_txt(logdirname, df_details, now):
    """
    Converts DataFrames to CSV and TXT files.

    Parameters:
    - logdirname (str): The directory for log files.
    - df_details (tuple): (df_map: dict, source_tables: list)
    - now (datetime): The current date and time.
    """
    # Extract parameters from the tuple
    csvname1 = logdirname + '/' + now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.csv')
    csvname2 = logdirname + '/' + now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.csv')
    name1 = logdirname + '/' + now.strftime('Report_UCMSDataFrame_%d%m%Y_%H%M.txt')
    name2 = logdirname + '/' + now.strftime('Report_ImportedDataFrame_%d%m%Y_%H%M.txt')
    df_map = df_details[0]
    source_tables = df_details[1]

    # Iterate through each table and process DataFrame
    for table, df in df_map.items():
        if isinstance(df, pd.DataFrame):
            tot_rows = df.shape[0]
            logging.info("Total records in table %s with select conditions are %s", table, str(tot_rows))

            # Process data for UCMS_CARDS table
            if table == source_tables[0]:
                df = df.sort_index(axis=0, ascending=False)
                df.to_csv(csvname1, mode='a', header=True)
                df_str = df.to_string(index=True)
                with open(name1, 'w') as file:
                    file.write(df_str + '\n')

            # Process data for Imported_Cards table
            if table == source_tables[1]:
                df.to_csv(csvname2, mode='a', header=True)
                df_str = df.to_string(index=True)
                with open(name2, 'w') as file:
                    file.write(df_str + '\n')

        else:
            logging.info("No records found for all cards count case in table %s", table)


def main():
    # Get the current working directory and time
    workdir = os.getcwd()
    now = datetime.datetime.now()

    # Create a directory for logging files
    logdirname = workdir + '/' + now.strftime('rmsReporting_%d%m%Y%H%M')
    logs = setup_logging(workdir, now, logdirname)

    logging.info('Log Execution Directory is at path :%s', logdirname)

    # Read configuration file
    fnm = "config.ini"
    cf = ConfigParser.ConfigParser(allow_no_value=True)
    a = cf.read(os.path.join(workdir, fnm))

    # Check if the configuration file is present
    if len(a) == 0:
        logging.info("ERROR: Configuration file config.ini not found in Current Working directory :%s", workdir)
        sys.exit()

    # Check server status
    server_login(cf)

    # Decrypt Oracle database password
    key = "password encryption"
    oracle_passwd_enc = cf.get('parameters', 'OraclePasswd')
    oracle_passwd = decrypt(key, oracle_passwd_enc)

    # Query database for card count analysis
    df_details = query_db_4_count(oracle_passwd, logs, cf)

    # Convert DataFrames to CSV and TXT
    convert_df_2_csv_txt(logdirname, df_details, now)

    logging.info('Tool Execution Ended ')


if __name__ == '__main__':
    main()
