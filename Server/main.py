#!/usr/bin/python
from socket import *
from flask import *
import threading,json,time,datetime,zipfile,os,hashlib,pydoc,sys
from flask_sqlalchemy import SQLAlchemy
from threading import Thread



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)
serversocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
serversocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
serversocket.bind(('0.0.0.0', 5001))
serversocket.listen(5)
LocalUrl='http://192.168.0.38:5000/updates/downloads/'
URL="http://192.168.0.38:5000"
CHECK_ALIVE=1
CHECK_UPDATE=3
maxV=0

class Client(db.Model):
    """Clienten Class"""
    id = db.Column('client_id', db.Integer, primary_key=True)
    hostname = db.Column(db.String(100))
    datum = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    ram = db.Column(db.String(200))
    cpu = db.Column(db.String(40))
    alive = db.Column(db.String(40))
    gpu = db.Column(db.String(40))

    def __init__(self,hostname,ip,cpu,ram,gpu,date):
        """
        Constructs a new Client object.
        :param hostname: Hostname of the Client
        :param ip: IP-Address of the Client
        :param cpu: CPU of the Client
        :param ram: RAM of the Client
        :param gpu: GPU of the Client
        :param date: Date of the last Connection of the Client
        :param alive: If Client is still connected with the Server
        :return: returns nothing
        """
        self.hostname=hostname
        self.ram=ram
        self.cpu=cpu
        self.gpu=gpu
        self.ip=ip
        self.datum=date
        self.alive=str(True)

class UpdatePackage(db.Model):
    """
    Update Class
    """
    id = db.Column('client_id', db.Integer, primary_key=True)
    packageName=db.Column(db.String(100))
    version=db.Column(db.Float)
    url=db.Column(db.String(100))
    script=db.Column(db.String(100))
    checksum=db.Column(db.String(100))
    def __init__(self,packageName,version,url,script):
        """
        Constructs a new Update object.
        :param packageName:  Name of the Update
        :param version: Version of the Update
        :param url: Url of the Update
        :param script: Script to install the Update
        :return:  returns nothing
        """
        self.packageName=packageName
        self.version=version
        self.url=url
        self.script=script


db.create_all()
def newUpdate():
    """
    This Method takes a Name and a Version from User Input to create a new Update.
    :return:nothing
    """
    time.sleep(2)
    while(True):
        inpu=input('For Entering new Update write New:')

        if inpu =="New":

            name=input("Name of Update: ")
            try:
                name.encode("ascii")
            except UnicodeEncodeError:
                print('UpdateName must be ASCII compatible')
                continue
            version=input("Version of Update: ")
            try:
                float(version)
            except ValueError:
                print("Version must be a Number!")
                continue
            createUpdatePackage(name.replace(' ',''),version)
        elif inpu=="Quit":
            
            serversocket.close()
            print ('Socket closed')
            print('Server stopped')
            os._exit(1)
        else:
            print('No new Update added\n')

        time.sleep(2)
def createUpdatePackage(name,version):
    """
    This Method creates a new Update and saves it in the Database.
    :param name: Name of the Update
    :param version: Version of the Update
    :return: nothing
    """
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
    update.checksum=hashlib.md5(open('./downloads/' + update.packageName, 'rb').read()).hexdigest()
    os.remove('./downloads/' + update.packageName[:-4] + '.txt')
    db.session.add(update)

    db.session.commit()

    settingMax()
    print('Added new Update: ' + name +' \n' )
def initialaseUpdateDB():
    """
    If the Database is empty,this method fills it with Start Updates.
    :return: nothings
    """
    if(len(list(UpdatePackage.query.all())) == 0):
        createUpdatePackage('UpdateA',1.0)
        createUpdatePackage('UpdateAb', 1.5)
        createUpdatePackage('UpdateB', 2.0)
        createUpdatePackage('UpdateC', 3.0)
        createUpdatePackage('UpdateD', 4.0)
        createUpdatePackage('UpdateE', 5.0)


def createServer():
    """
    This Method connects to the Clients and starts Worker Threads for them.
    :return: nothing
    """
    global serversocket
    skip=False
    print('Waiting for Connections\n')
    for c in db.session.query(Client):  # at start no client ist connectet
        c.alive = str(False)
        db.session.commit()
    
        while (1):
            try:
                (clientsocket, address) = serversocket.accept()
                print('Connected\n')
                print(address)
                rec=clientsocket.recv(1024).decode()
                jsonobject=json.loads(rec)
                #print(jsonobject['hostname'])
                #print(jsonobject['cpu'])

                db.session.commit()

            # if(len(Client.query.filter(Client.hostname==jsonobject['hostname']) != 0 and Client.query.filter(Client.ip==address[0] )) == True):
                clienten =Client.query.filter(Client.hostname == jsonobject['hostname']).all()


                for clientb in clienten:

                    if clientb.ip ==address[0] and clientb.hostname== jsonobject['hostname']:
                        skip=True
                        # print(str(clientb.alive) +"  " + str(clientb.id))
                        if clientb.alive==str(True):
                            print('Existing:Already Connected\n')
                            clientsocket.close()
                            break
                        else:
                            clientsocket.setblocking(0)
                            print('Existing:Not Connected\n')
                            clientb.datum = str(datetime.datetime.now())[:16]
                            #clientb.alive=str(True)

                            db.session.commit()



                            cID = Client.query.filter(Client.hostname == jsonobject['hostname']).first().id
                            a = Thread(target=checkAliveSocket, args=(clientsocket, cID,))
                            a.start()
                            cU = Thread(target=checkUpdateRequest, args=(clientsocket,))
                            cU.start()
                            break
                if skip==False:
                    c=Client(jsonobject['hostname'],address[0],jsonobject['cpu'],jsonobject['ram'],jsonobject['gpu'],str(datetime.datetime.now())[:16])
                    db.session.add(c)

                    db.session.commit()

                    cID =Client.query.filter(Client.hostname == jsonobject['hostname']).first().id
                    a = Thread(target=checkAliveSocket, args=(clientsocket, cID, ))
                    a.start()
                    cU = Thread(target=checkUpdateRequest, args=(clientsocket, ))
                    cU.start()
                    print('New Client ' + jsonobject['hostname'] + ' added!')
                skip=False
            except Exception:
                continue
    finally:
        serversocket.close()

def checkAliveSocket(s,cID):
    """
    This Method checks if the Client is still connected.
    :param s: Socket which connects to Client
    :param cID: ID of the Client in the Database
    :return: nothing
    """
    open=True
    client=Client.query.filter(Client.id == cID).first()
    hostname=client.hostname
    while open:
            try:
                s.send(str.encode("Ping"))
                client.alive = str(True)
                client.datum = str(datetime.datetime.now())[:16]
                e = db.session.query(Client).all()
                k = Client.query.all()

                #db.session.remove(client)
                db.session.commit()


            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError,OSError):
                client.alive = str(False)

                db.session.commit()

                #s.close()
                open=False
                print('Client with hostname=[' + str(hostname) + '] lost connection.')
            time.sleep(CHECK_ALIVE)


def settingMax():
    """
    This Method sets Max to to maximum Version of all Updates
    :return: nothing
    """
    global maxV
    global maxUp
    for upd in UpdatePackage.query.all():
        if (float(upd.version) > float(maxV)):
            maxV = upd.version
            maxUp = upd
            # print(max)
    print('Max Version: ' +str(maxV))

def checkUpdateRequest(s):
    """
    This Method checks for UpdateRequests of the Client
    :param s: Socket which connects to the CLient
    :return: nothing
    """
    global maxV
    global maxUp
    while True:
        try:
            recieved = s.recv(100).decode("utf-8")
           # print(recieved)
            jsonupdate = json.loads(recieved)
            if (float(jsonupdate['Update']) < float(maxV) or str(maxUp.checksum) != str(jsonupdate['checksum'])):
                updatemessage = '{"request":"update","name":"' + maxUp.packageName + '","version":"' + str(
                maxUp.version) + '","url":"' + maxUp.url + '","script":"' + maxUp.script + '","checksum":"' + maxUp.checksum + '"}'
                s.send(str.encode(updatemessage))
                print('UpdateMessageSend')
        except (BlockingIOError, TimeoutError, BrokenPipeError,json.decoder.JSONDecodeError):
            time.sleep(CHECK_UPDATE)
            continue
        except (ConnectionAbortedError, ConnectionResetError):
            s.close()
            return
        time.sleep(CHECK_UPDATE)


@app.route('/')

def main():
     """
     Main Site of the FlaskApp shows all CLients with Information.
     :return: Table of all Clients in HTML.
     """
     return render_template('clients.html', clients=Client.query.all(),updateslink=URL+"/updates")

@app.route('/updates')
def updates():
     """
     Update Site show all avaiable Updates.
     :return: Table of Updates in HTML
     """
     return render_template('updates.html', updates=UpdatePackage.query.all(),home=URL)

@app.route('/updates/downloads/<update>')
def return_file(update):
    """
    Download specific Update from link
    :param update: The Update which can be downloaded
    :return: HTML of the download Site
    """
    updatefile=update + ".zip"
    return send_from_directory(directory='downloads', filename=updatefile, as_attachment=True)
def runFlask():
    """
    Starts the flask App.
    :return: nothing
    """
    app.run(host='0.0.0.0', port=5000, threaded=True)



if __name__ == "__main__":
    initialaseUpdateDB()
    settingMax()
    print('Server started.')
    t = Thread(target=createServer)
    t.start()
    update = Thread(target=newUpdate)
    update.start()
    flas=Thread(target=runFlask)
    flas.run()
