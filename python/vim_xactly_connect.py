import jaydebeapi as jdb

conn = None
try:
    conn = jdb.connect(
        "com.xactly.connect.jdbc.Driver",
        "jdbc:xactly://implement1.xactlycorp.com:443?useSSL=true",
        ["tmurdock_boomi@xactlyincent.com","14mD3Lt4"],
        "/Users/tmurdock/down/xjdbc-with-dependencies-1.2.0-RELEASE.jar"
    )
except Exception as e:
    print(e)
    exit()


curs = conn.cursor()
curs.execute("select * from (show step s_testing);")
print(curs.fetchall())

curs.close()
conn.close()
