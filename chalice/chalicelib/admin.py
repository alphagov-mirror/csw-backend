import os
import psycopg2
#from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from chalicelib.models import DatabaseHandle


# native lambda admin function to be invoked
# TODO add authentication or rely on API permissions and assume roles to control access
def execute_database_create_tables(app, event, context):

    try:
        dbh = DatabaseHandle(app)

        table_list = []
        message = ""

        for table_name in event['Tables']:
            model = dbh.get_model(table_name)
            table_list.append(model)

        created = dbh.create_tables(table_list)
    except Exception as err:
        app.log.error(str(err))
        created = False
        message = str(err)

    if created:
        response = ", ".join(event['Tables'])
    else:
        response = f"Table create failed: {message}"
    return response


# def execute_database_create_all_tables(event, context):
    #
    #     try:
    #     dbh = DatabaseHandle(app)
    #
    #   models = dbh.get_models()
    #   table_names = []
    #   table_list = []
    #
    #   for table_name in models:
    #       table_list.append(models[table_name])
    #       table_names.append(table_name)
    #   message = ""
    #
    #   created = dbh.create_tables(table_list)
    # except Exception as err:
    #   created = False
    #   message = str(err)
    #
    # if created:
    #   response = ", ".join(table_names)
    # else:
    #   response = f"Tables created"
    # return response


def execute_database_create_item(app, event, context):

    try:
        dbh = DatabaseHandle(app)

        item = dbh.create_item(event)
        data = item.serialize()
        json_data = app.utilities.to_json(data)

    except Exception as err:
        app.log.error(str(err))
        json_data = None

    return json_data


def execute_database_get_item(app, event, context):

    app.log.debug('database_get_item function')
    try:

        dbh = DatabaseHandle(app)

        item = dbh.get_item(event)
        data = item.serialize()
        json_data = app.utilities.to_json(data)

    except Exception as err:
        app.log.error(str(err))
        json_data = None

    return json_data


def execute_database_run(app, event, context):

    try:

        dbh = DatabaseHandle(app)
        dbh.set_credentials(event['User'], event['Password'])
        status = dbh.execute_commands(event['Commands'])
    except Exception as err:
        app.log.error(str(err))
        status = False

    return status


def execute_database_list_models(app, event, context):

    try:

        dbh = DatabaseHandle(app)

        models = dbh.get_models()
        tables = models.keys()

    except Exception as err:
        app.log.error(str(err))
        tables = []

    return tables

def execute_database_create(app, event, context):

    app.log.debug(os.environ['CSW_HOST'])
    app.log.debug(event['User'])
    app.log.debug(event['Database'])

    try:

        app.log.debug("Attempt database connection")
        con = psycopg2.connect(
            database='postgres',
            user=event['User'],
            host=os.environ['CSW_HOST'],
            password=event['Password']
        )

        app.log.debug("Set autocommit to on")
        #con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        con.autocommit = True

        app.log.debug("Get cursor")
        cur = con.cursor()

        app.log.debug("Execute database create")
        database = event['Database']
        statement = f"CREATE DATABASE {database};"
        status = cur.execute(statement)

        app.log.debug("Close connection")
        cur.close()
        con.close()
    except Exception as err:
        app.log.error(str(err))
        status = False

    return status