from flask import Flask
import pymysql.cursors

app = Flask(__name__)
app.secret_key = 'some key that you will never guess'
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='DB_project',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


from app import routes
