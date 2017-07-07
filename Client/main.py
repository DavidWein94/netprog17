import socket,time,platform
from threading import Thread
import time,math,psutil,cpuinfo,json
from subprocess import call,Popen,PIPE

connection=False

def connect():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,
                          socket.IPPROTO_TCP)
        sockaddr = ('192.168.0.59', 5001)
        s.connect(sockaddr)
        connection=True
    except (ConnectionResetError, ConnectionRefusedError):
        print("No Connection,Server dead or CLient already connected")
        s.close()
        connection = False

def get_processor_name():
    return cpuinfo.get_cpu_info().get('brand')
def get_hostname():
    return str(platform.node())
def get_ram():
    return str(math.ceil(psutil.virtual_memory()[0]/2.**30))
def get_gpu():
    if platform.system() == 'Linux':
        d = Popen(["lshw", "-c", "display"], stdout=PIPE).stdout.read()
        d = (str(d).split("\\n"))
        gpus = []
        for g in d:
            if 'Produkt' in g or 'product' in g:
                gpus.append(g.lstrip()[9:])
        return str(gpus)
    if platform.system()()=='Windows': #just for testing
        import wmi
        computer = wmi.WMI()
        gpu_info = computer.Win32_VideoController()[0]
        return format(gpu_info.Name)

while(True):
    if connection==False:
        print('Trying to connect')
        t=Thread(target=connect)
        t.start()

    time.sleep(60)