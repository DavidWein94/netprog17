from socket import *
from flask import *
import threading,json,time,datetime,zipfile,os
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
def newUpdate():
    time.sleep(8)
    while(True):
        inpu=input('For Entering new Update write Yes:')
        if inpu =="Yes":
            name=input("Name of Update: ")
            version=input("Version of Update: ")
            createUpdatePackage(name,version)

        else:
            print('No new Update added\n')
        time.sleep(10)
def createUpdatePackage(name,version):
    upList=UpdatePackage.query.all()
    for u in upList:
        if u.packageName == (name + '.zip') :
            print('Update with this name already exists!\n')
            return
        if float(u.version) ==version:
            print("Update with this version already exists\n")
            return

    update = UpdatePackage(name +'.zip', float(version), LocalUrl + name, "unzip")
    file = open('./downloads/' + update.packageName[:-4] + '.txt', 'w+')
    file.write('{"request":"update","name":"' + update.packageName + '","version":"' + str(
        update.version) + '","url":"' + update.url + '","script":"' + update.script + '"}')
    file.close()
    zf = zipfile.ZipFile('./downloads/'+ update.packageName, mode='w')
    zf.write('./downloads/'+ update.packageName[:-4] + '.txt')
    zf.close()
    os.remove('./downloads/' + update.packageName[:-4] + '.txt')
    db.session.add(update)
    db.session.commit()
    print('Added new Update: ' + name +' \n' )
def initialaseUpdateDB():
    if(len(list(UpdatePackage.query.all())) == 0):
        createUpdatePackage('UpdateA',1.0)
        createUpdatePackage('UpdateAb', 1.5)
        createUpdatePackage('UpdateB', 2.0)
        createUpdatePackage('UpdateC', 3.0)
        createUpdatePackage('UpdateD', 4.0)
        createUpdatePackage('UpdateE', 5.0)
def createServer():
    global serversocket
    print('Waiting for Connections\n')

    try:
        while (1):
            (clientsocket, address) = serversocket.accept()
            print('Connected\n')
            print(address)
            jsonobject=json.loads(clientsocket.recv(200).decode())
            #print(jsonobject['hostname'])
            #print(jsonobject['cpu'])
            if(db.session.query(Client.query.filter(Client.hostname==jsonobject['hostname']).exists()).scalar()== True and db.session.query(Client.query.filter(Client.ip==address[0] ).exists()).scalar() == True):

                clienten = Client.query.filter(Client.hostname == jsonobject['hostname']).all()
                for clientb in clienten:
                    Client.query.filter(Client.ip == clientb.ip)
                    idc = clientb.id
                lockcs.acquire()
                if idc in csockets.values():
                    print('Existing:Connected\n')
                    clientsocket.close()
                else:
                    clientsocket.setblocking(0)
                    print('Existing:Not Connected\n')
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
                        #print(updatemessage)
                        k.send(str.encode(updatemessage))
                       # print('UpdateMessageSend')
                    else:
                        continue
                        #print("Actual version")
                except (BlockingIOError, ConnectionAbortedError, ConnectionResetError, TimeoutError):
                    print('No UpdateRequests \n')
        time.sleep(10)

@app.route('/')
def main():
     return render_template('clients.html', clients=Client.query.all(),updateslink=URL+"/updates")

@app.route('/updates')
def updates():
     return render_template('updates.html', updates=UpdatePackage.query.all(),home=URL)

@app.route('/updates/downloads/<update>', methods=['GET'])
def return_file(update):
    updatefile=update + ".zip"
    return send_from_directory(directory='downloads', filename=updatefile, as_attachment=True)
def runFlask():
    app.run(host='0.0.0.0', port=5000, threaded=True)




if __name__ == "__main__":
    initialaseUpdateDB()
    t = Thread(target=createServer)
    t.start()
    a = Thread(target=checkAlive)
    a.start()
    cU = Thread(target=checkUpdateRequest)
    cU.start()
    update = Thread(target=newUpdate)
    update.start()
    flas=Thread(target=runFlask)
    flas.run()