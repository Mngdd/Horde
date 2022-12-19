import socket
from _thread import *

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = "127.0.0.1"  # ipv4 этого компа
port = 5555  # от 0 до 65535, 0-1023 требует админа

server_ip = socket.gethostbyname(server)  # тут чета происходит, но я не шарю

try:
    s.bind((server, port))  # связываем сокет и порт

except socket.error as e:
    print(str(e))

s.listen(2)  # максимум челиксов на серве
print("Waiting for a connection")

currentId = "0"
pos = ["0:50,50", "1:100,100"]


def threaded_client(conn):  # вот тут крч мы с челом работаем
    global currentId, pos
    conn.send(str.encode(currentId))  # чел узнает какой у него ID на сервере
    currentId = "1"  # ваще переделать это, тут типа id 0 занят, поэтому ставим 1
    reply = ''  # отве
    while True:
        try:
            data = conn.recv(2048)  # тк не знаем скока тонн информации нам пошлет юзер
            # читаем по 2кб
            reply = data.decode('utf-8')  # переводим полученную инфу в нормальны ебуквы
            if not data:  # если челикс ливает
                conn.send(str.encode("Goodbye"))
                break
            else:
                # просто обработка того, что получили. Неинтересно
                print("Recieved: " + reply)
                arr = reply.split(":")
                id = int(arr[0])
                pos[id] = reply

                if id == 0: nid = 1
                if id == 1: nid = 0

                reply = pos[nid][:]
                print("Sending: " + reply)

            conn.sendall(str.encode(reply))  # всем рассылаем инфу(координаты)
        except:
            break

    print("Connection Closed")
    conn.close()  # отключаемся


while True:
    conn, addr = s.accept()  # принимаем чела который заходит
    # conn - сокет, от него получаем и ему посылаем инфу, addr - просто адрес клиента
    print("Connected to: ", addr)

    start_new_thread(threaded_client, (conn,))  # параллельный поток для работы с новым юзером
