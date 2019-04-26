"""
API LAMBDAS
"""
import os
import re
import json
from datetime import datetime
# from peewee import Case, fn
# from botocore.exceptions import ClientError
from chalice import Rate

from app import app
from chalicelib.database_handle import DatabaseHandle


def read_script(script_path):
    """
    Read a script of SQL and parse into discrete commands by separating at the semi colons.
    """
    try:
        commands = []
        abs_path = os.path.join(os.getcwd(), script_path)
        app.log.debug(os.getcwd())
        print(abs_path)
        with open(abs_path,'r') as script:
            command = ""
            lines = script.readlines()
            for line in lines:
                # Ignore script comments
                if not re.match("^\-{2}", line):
                    # Treat empty lines as breaks between commands
                    if re.match("^\s*$", line):

                        if len(command) > 0:
                            # Only add command to array if it's non-empty
                            commands.append(command)
                            command = ""

                    else:
                        # If non-empty and not a comment then it's part of the previous command
                        command += line
            # If there's no new line at the end of the script
            # then the last command gets missed if you don't do this
            if len(command) > 0:
                commands.append(command)
    except Exception as err:
        print (f"Failed to open script: {script_path}: " + str(err))

    return commands


def execute_update_stats_tables(event, context):
    """
    The summary stats are produced daily as static tables.
    These could be rendered as views or materialized views but since the data is not changing that frequently
    that adds significant processing load for little benefit.
    By regenerating the stats on a schedule we can make the interface much faster and keep the database
    processing load lighter.
    """
    status = 0
    commands = []
    try:
        dbh = DatabaseHandle(app)
        commands = read_script('chalicelib/api/sql/summary_stats.sql')
        app.log.debug(json.dumps(commands))
        dbh.execute_commands(commands, 'csw')
        status = 1
    except Exception as err:
        app.log.error("Update stats tables error: " + app.utilities.to_json(data))
    return {
        "status": status,
        "commands": commands
    }


@app.schedule(Rate(24, unit=Rate.HOURS))
def scheduled_update_stats_tables(event):
    """
    The default behaviour is that the stats are generated automatically once every 24 hours
    """
    return execute_update_stats_tables(event, {})

@app.lambda_function()
def update_stats_tables(event, context):
    """
    For the purposes of testing we can manually regenerate the stats summary tables on demand
    """
    return execute_update_stats_tables(event, context)

# TODO provide a number of GET only routes
# TODO API authentication | whitelisting?
# /api/[ health | prometheus]/... - for health
# /api/dashboardify/... - for the big screens
# /api/stats/... - for raw json data