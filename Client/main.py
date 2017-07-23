import socket,time,platform
from threading import Thread
import time,math,psutil,cpuinfo,json
from subprocess import call,Popen,PIPE
import urllib.request,zipfile,os

connection=False
version=0
checksum=str(0)
s=None
SERVERIP='192.168.0.38'
SERVERPORT=5001
def connect():
    """
    This Method connects the Client with the Server.
    :return: nothing
    """
    global connection
    global s
    global version

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,
                          socket.IPPROTO_TCP)
        sockaddr = (SERVERIP, SERVERPORT)
        s.connect(sockaddr)
        connection=True
        s.send(jsonHardwareInformation())
        connection=True
        u = Thread(target=updateRequest)
        u.start()
        while (connection):
            recieved = s.recv(1000).decode() #trying to recieve ping from server
            if (recieved== ''): # if ping is empty Server must be offline or another instance of this Client is already connected
                print("No Connection,Server dead or CLient already connected")
                s.close()
                connection = False

            # starting to Update
            else:
                try:
                    jsonr = json.loads(recieved)
                    updateClientInfo(jsonr)
                except json.decoder.JSONDecodeError:
                    continue
            time.sleep(1)
    except (ConnectionResetError, ConnectionRefusedError,json.decoder.JSONDecodeError):
        print("No Connection,Server dead or CLient already connected")
        s.close()
        connection = False

def get_processor_name():
    """
    Returns the Name of the Processor of the Computer using the Script
    :return: The name of the Processofr from the Computer usng the Script
    """
    return cpuinfo.get_cpu_info().get('brand')
def get_hostname():
    """Returns the Hostname of the Computer using the Script
    :return: Hostname of the Computer"""
    return str(platform.node())
def get_ram():
    """Returns the RAM of the Computer using the Script
    :return:GPU of the Computer
    """
    if platform.system() == 'Linux':
        d = Popen(["lshw", "-c", "display"], stdout=PIPE).stdout.read()
        d = (str(d).split("\\n"))
        gpus = []
        for g in d:
            if 'Produkt' in g or 'product' in g:
                gpus.append(g.lstrip()[9:])
        return str(gpus)
    if platform.system()=='Windows': #just for testing
        import wmi
        computer = wmi.WMI()
        gpu_info = computer.Win32_VideoController()[0]
        return format(gpu_info.Name)
    return 'System not Linux or Windows'
def jsonHardwareInformation():
        """Returns a JSON-String of the Hardwareinformation in bytes
        :return:JSON-STRING of the Hardware Information"""
        m = '{"hostname": "' + get_hostname() + '","cpu":"' + get_processor_name() + '","ram":"' + get_ram() + '","gpu":"' + get_gpu() + '"}'
        mbytes=str.encode(m)
        return mbytes

def updateRequest():
    """While  the Client is connected to the Server,it sends JSON-Strings with the actual version of the Client
    :return:nothing"""
    global connection
    try:
        while connection:
            checkUpdate()
            print('UpdateRequest')
            s.send(str.encode('{"Update":"' + version +'","checksum":"' + checksum +'"}'))
            time.sleep(20)
    except ConnectionResetError:
        connection=False
def checkUpdate():
    """Read the actual version of the Client out of the updateinfo.txt and saves it in the version variable
    :return:nothing"""
    global version
    global  checksum
    try:
        file=open('updateinfo.txt','r')
        info=json.loads(file.read())
        version=info['version']
        checksum=info['checksum']
        file.close()
    except FileNotFoundError:
        print("No Version Found:Getting actual Version from Server")
        version='0'
        checksum='0'
def updateClientInfo(jsono):

    """Updates the updateinfo.txt with new  Information out of a JSON-String
    :return:nothing"""
    print (jsono['name'])
    try:
        os.remove('./'+jsono['name'])
    except FileNotFoundError:
        pass
    try:
            os.remove('./downloads/' + jsono['name'][:-4]+'.txt')
    except FileNotFoundError:
        pass
    urllib.request.urlretrieve(jsono['url'],jsono['name'])

    file = open('updateinfo.txt', 'w')
    if platform.system()== 'Linux':
        call([jsono['script'],jsono['name']])
        fileInfo=open('./downloads/'+jsono['name'][:-4]+ ".txt",'r')
        d=fileInfo.read()
        file.write(d[:-1]+',"checksum":"'+jsono['checksum']+'"}')
        file.close()
    if platform.system()=='Windows':
        file.write('{"name": "'+jsono['name']+'", "version": "'+ str(jsono['version'])+'", "url": "' +jsono['url']+ '"}')
        file.close()
    print("Updated")

while(True):
    if connection==False:
        print('Trying to connect')
        t=Thread(target=connect)
        t.start()

    time.sleep(60)