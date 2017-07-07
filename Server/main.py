from socket import *
from flask import *
import threading,json,time,datetime
from flask_sqlalchemy import SQLAlchemy
from threading import Thread



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
db=SQLAlchemy(app)
csockets={}
lockcs=threading.Lock()
serversocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
serversocket.bind(('0.0.0.0', 5001))
serversocket.listen(5)
LocalUrl='http://192.168.0.59:5000/updates/downloads/'
URL="http://192.168.0.59:5000"


class Client(db.Model):
    id = db.Column('client_id', db.Integer, primary_key=True)
    hostname = db.Column(db.String(100))
    datum = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    ram = db.Column(db.String(200))
    cpu = db.Column(db.String(40))
    alive = db.Column(db.String(40))
    gpu = db.Column(db.String(40))

    def __init__(self,hostname,ip,cpu,ram,gpu,date):
        self.hostname=hostname
        self.ram=ram
        self.cpu=cpu
        self.gpu=gpu
        self.ip=ip
        self.datum=date
        self.alive=str(True)

class UpdatePackage(db.Model):
    id = db.Column('client_id', db.Integer, primary_key=True)
    packageName=db.Column(db.String(100))
    version=db.Column(db.Float)
    url=db.Column(db.String(100))
    script=db.Column(db.String(100))

    def __init__(self,packageName,version,url,script):
        self.packageName=packageName
        self.version=version
        self.url=url
        self.script=script


db.create_all()
if(len(list(UpdatePackage.query.all())) == 0):
    update1=UpdatePackage('UpdateA.zip',1.0,LocalUrl+"UpdateA","unzip")
    update2=UpdatePackage('UpdateAb.zip',1.5,LocalUrl+"UpdateAb","unzip")
    update3=UpdatePackage('UpdateB.zip',2.0,LocalUrl+"UpdateB","unzip")
    update4 = UpdatePackage('UpdateC.zip', 3.0, LocalUrl+"UpdateC","unzip")
    update5 = UpdatePackage('UpdateD.zip', 4.0, LocalUrl+"UpdateD","unzip")
    db.session.add(update1)
    db.session.add(update2)
    db.session.add(update3)
    db.session.add(update4)
    db.session.add(update5)
    db.session.commit()

def createServer():
    global serversocket
    print('Waiting for Connections')

    try:
        while (1):
            (clientsocket, address) = serversocket.accept()
            print('Connected')
            print(address)
            jsonobject=json.loads(clientsocket.recv(200).decode())
            print(jsonobject['hostname'])
            print(jsonobject['cpu'])
            if(db.session.query(Client.query.filter(Client.hostname==jsonobject['hostname']).exists()).scalar()== True and db.session.query(Client.query.filter(Client.ip==address[0] ).exists()).scalar() == True):

                clienten = Client.query.filter(Client.hostname == jsonobject['hostname']).all()
                for clientb in clienten:
                    Client.query.filter(Client.ip == clientb.ip)
                    idc = clientb.id
                lockcs.acquire()
                if idc in csockets.values():
                    print('Existing:Connected')
                    clientsocket.close()
                else:
                    clientsocket.setblocking(0)
                    print('Existing:Not Connected')
                    csockets.update({clientsocket: idc})
                    Client.query.filter(Client.id == idc)[0].datum = str(datetime.datetime.now())[:16]
                    db.session.commit()
                lockcs.release()
            else:
                c=Client(jsonobject['hostname'],address[0],jsonobject['cpu'],jsonobject['ram'],jsonobject['gpu'],str(datetime.datetime.now())[:16])
                db.session.add(c)
                db.session.commit()
                lockcs.acquire()
                csockets.update({clientsocket: c.id})
                lockcs.release()
    finally:
        serversocket.close()

def checkAlive():
    global serversocket
    for c in Client.query.all():  #at start no client ist connectet
        c.alive=str(False)
        db.session.commit()
    while(True):

        lockcs.acquire()
        keys=csockets.keys()
        lockcs.release()

        for s in list(keys):
            try:
                s.send(str.encode("Ping"))
                Client.query.filter(Client.id == csockets[s])[0].alive = str(True)
                Client.query.filter(Client.id == csockets[s])[0].datum = str(datetime.datetime.now())[:16]
                db.session.commit()
            except (ConnectionAbortedError,ConnectionResetError):
                Client.query.filter(Client.id == csockets[s])[0].alive=str(False)
                db.session.commit()
                lockcs.acquire()
                csockets.pop(s)
                lockcs.release()

        time.sleep(10)


def checkUpdateRequest():
    while True:
        listUpdates = {}
        max = 0
        maxUp = None
        for upd in UpdatePackage.query.all():
            if (float(upd.version) > float(max)):
                max = upd.version
                maxUp = upd
        lockcs.acquire()
        keys = list(csockets.keys())
        lockcs.release()
        if len(list(keys)) > 0:
            for k in keys:
                try:
                    jsonupdate = json.loads(k.recv(100).decode("utf-8"))
                    if (float(jsonupdate['Update']) < float(max)):
                        updatemessage = '{"request":"update","name":"' + maxUp.packageName + '","version":"' + str(
                            maxUp.version) + '","url":"' + maxUp.url + '","script":"' + maxUp.script +'"}'
                        print(updatemessage)
                        k.send(str.encode(updatemessage))
                        print('UpdateMessageSend')
                    else:
                        print("Actual version")
                except (BlockingIOError, ConnectionAbortedError, ConnectionResetError, TimeoutError):
                    print('No recv')
        time.sleep(10)

@app.route('/')
def main():
     return render_template('clients.html.', clients=Client.query.all(),updateslink=URL+"/updates")

@app.route('/updates')
def updates():
     return render_template('updates.html.', updates=UpdatePackage.query.all())

@app.route('/updates/downloads/<update>', methods=['GET'])
def return_file(update):
    updatefile=update + ".zip"
    return send_from_directory(directory='downloads', filename=updatefile, as_attachment=True)
def runFlask():
    app.run(host='0.0.0.0', port=5000, threaded=True)




if __name__ == "__main__":
    t = Thread(target=createServer)
    t.start()
    a = Thread(target=checkAlive)
    a.start()
    cU = Thread(target=checkUpdateRequest)
    cU.start()
    flas=Thread(target=runFlask)
    flas.run()