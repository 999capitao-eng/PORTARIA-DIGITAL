import sqlite3
import time

conn = sqlite3.connect("portaria.db")
conn.execute("BEGIN EXCLUSIVE")
print("Banco travado por 30 segundos. Use a aplicação agora.")
time.sleep(30)
conn.rollback()
print("Banco liberado.")
