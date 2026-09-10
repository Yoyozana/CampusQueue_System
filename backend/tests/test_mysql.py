import pymysql

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Mqulwa@05"
)
print("Connected to MySQL successfully:", conn.get_server_info())
conn.close()
