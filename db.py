import mysql.connector
from mysql.connector import pooling

connection_pool = pooling.MySQLConnectionPool(
    pool_name="gambling_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="mysql",
    database="gambling_db"
)

def get_connection():
    return connection_pool.get_connection()