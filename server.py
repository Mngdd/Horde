import socket
from _thread import *
import ast

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = list(open('USER_IP.txt', 'r', encoding='utf-8'))[0].strip()  # ipv4 этого компа
port = 5555  # от 0 до 65535, 0-1023 требует админа

server_ip = socket.gethostbyname(server)  # тут чета происходит, но я не шарю

try:
    s.bind((server, port))  # связываем сокет и порт

except socket.error as e:
    print(str(e))

s.listen(2)  # максимум челиксов на серве
print("Waiting for a connection")

user_nickname = None
user_data = {} #{'test': {'online': False, 'ip': -1, 'vars': [None]}}


def threaded_client(conn):  # вот тут крч мы с челом работаем
    global user_nickname, user_data
    conn.send(str.encode(str(user_nickname)))  # зачем не знаю
    reply = ''  # отве
    while True:
        try:
            data = conn.recv(4096)  # тк не знаем скока тонн информации нам пошлет юзер
            # читаем по 4кб
            reply = ast.literal_eval(data.decode('utf-8'))  # переводим полученную инфу в нормальны ебуквы
            if not data:  # если челикс ливает
                print('LEAVIN')
                conn.send(str.encode(f"чел {user_nickname} ливнул"))
                break
            else:
                # просто обработка того, что получили. Неинтересно
                print("client replied: ", reply)
                # arr = reply.split(":")
                # id = int(arr[0])
                # pos[id] = reply
                #
                # if id == 0:
                #     nid = 1
                # if id == 1:
                #     nid = 0
                #
                # reply = pos[nid][:]
                print(reply[0])
                user_data[reply[0][0]] = reply[0][1]

                print("Sending: ", reply)

            conn.sendall(str.encode(str(user_data)))  # всем рассылаем инфу(координаты)
        except Exception as e:
            print('SERVER//', e)
            break

    print("Connection Closed")
    conn.close()  # отключаемся


while True:
    conn, addr = s.accept()  # принимаем чела который заходит
    # conn - сокет, от него получаем и ему посылаем инфу, addr - просто адрес клиента
    print("Connected to: ", addr)

    start_new_thread(threaded_client, (conn,))  # параллельный поток для работы с новым юзером
