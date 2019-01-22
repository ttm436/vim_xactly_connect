import json
from functools import reduce
import jaydebeapi as jdb

conn = None
curs = None
settings = None
with open('/Users/tmurdock/xactly_connect.json') as settings_file:
    settings = json.load(settings_file)

def close_connection():
    global conn
    global curs
    if (curs is not None):
        curs.close()
        curs = None
    if (conn is not None):
        conn.close()
        conn = None

def open_connection(name):
    global conn
    global curs
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

def execute_command(command):
    if (curs):
        curs.execute(command)
    else:
        print("You must make a connection before executing a command")

def result_string():
    out_str = ""
    result = curs.fetchall()
    if (result):
        desc = map(lambda a: str(a[0]), curs.description)
        out_str += reduce(lambda a, b: a + '|' + b, desc) + "\n"
        for a in result:
            out_str += reduce(lambda b, c: str(b) + '|' + str(c), a) + "\n"
    return out_str

def result_print():
    print(result_string())

def result_write():
    with open('/Users/tmurdock/.wbresult', 'w') as out_file:
        out_file.write(result_string())

    
