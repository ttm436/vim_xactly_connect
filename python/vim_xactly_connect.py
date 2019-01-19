import vim
import json
import jaydebeapi as jdb

conn = None
curs = None
settings = None
with open('~/xactly_connect.json') as settings_file:
    settings = json.load(settings_file)

def close_connection():
    if (curs):
        curs.close()
        curs = None
    if (conn):
        conn.close()
        conn = None

def set_connection(name):

    setting = settings[name]
    close_connection()
    try:
        conn = jdb.connect(
            setting['driver_class'],
            setting['url'],
            [setting['username'],setting['password']],
            setting['path']
        )
    except Exception as e:
        print(e)
        exit()
    curs = conn.cursor()

def execute_command(command)
    if (curs):
        curs.execute()
    else:
        print("You must make a connection before executing a command")

def print_result()
    print(curs.fetchall())

