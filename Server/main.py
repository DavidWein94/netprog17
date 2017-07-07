from socket import *
from flask import *
from flask_sqlalchemy import SQLAlchemy
from threading import Thread



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
db=SQLAlchemy(app)

serversocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
serversocket.bind(('0.0.0.0', 5001))
serversocket.listen(5)


class Client(db.Model):
    id = db.Column('client_id', db.Integer, primary_key=True)
    hostname = db.Column(db.String(100))
    datum = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    ram = db.Column(db.String(200))
    cpu = db.Column(db.String(40))
    alive = db.Column(db.String(40))
    gpu = db.Column(db.String(40))




@app.route('/')
def main():
     return render_template('clients.html.', clients=Client.query.all())


def runFlask():
    app.run(host='0.0.0.0', port=5000, threaded=True)




if __name__ == "__main__":

    flas=Thread(target=runFlask)
    flas.run()