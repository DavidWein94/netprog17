import socket,time
from threading import Thread

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



while(True):
    if connection==False:
        print('Trying to connect')
        t=Thread(target=connect)
        t.start()

    time.sleep(60)