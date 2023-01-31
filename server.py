import socket
import threading
from _thread import *
import ast


class Server:
    def __init__(self, port, capacity):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = list(open('SERVER_PORT.txt', 'r', encoding='utf-8'))[0].strip()  # ipv4 этого компа
        self.port = port  # от 0 до 65535, 0-1023 требует админа
        self.server_ip = socket.gethostbyname(self.server)  # тут чета происходит, но я не шарю

        self.is_port_in_use(self.port)  # проверяем, занят ли порт

        try:
            self.s.bind((self.server, self.port))  # связываем сокет и порт
        except socket.error as e:
            print(str(e))
        print(self.s)

        self.s.listen(capacity)  # максимум челиксов на серве
        print("\tWaiting for a connection")
        self.user_nickname = None
        self.user_data = {}  # {'test': {'online': False, 'ip': -1, 'vars': [None]}}
        self.enemy_data = []  # тупа спрайт группа капец я умный да
        self.bullets = []
        self.main()

    @staticmethod
    def is_port_in_use(port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                raise Exception('PORT ALREADY IN USE')

    def threaded_client(self, conn):  # вот тут крч мы с челом работаем
        # кароч сначала отдаем нынешнюю инфу хосту/юзеру потом обрабатываем новую. иначе рассинхрон жеский
        conn.send(str.encode(str(self.user_nickname)))
        reply = 'NONE'  # отве
        data = None
        while True:
            try:
                data = conn.recv(4096)  # тк не знаем скока тонн информации нам пошлет юзер
                # читаем по 4кб
                # print("\tclient replied: ", data)
                if not data:  # если челикс ливает
                    print('LEAVIN')
                    conn.send(str.encode(f"чел {self.user_nickname} ливнул"))
                    break
                else:
                    reply = list(ast.literal_eval(data.decode('utf-8')))  # переводим полученную инфу в нормальны ебуквы

                    # просто обработка того, что получили. Неинтересно
                    usr = reply.pop(0)
                    conn.sendall(str.encode(str([self.user_data])))

                    # всем рассылаем инфу(координаты)
                    self.enemy_data = []
                    self.bullets = []
                    self.bids = []

                    with locker:  # работает и без блокировки потоков отлично, но лишним не будет
                        if usr == 'HOST':  # обработанные хостом данные
                            for object_data in reply[0]:  # обновляем игроков
                                if 'TYPE' in object_data:  # пуля или враг
                                    if object_data['TYPE'] == 'E':  # враг
                                        self.enemy_data.append(object_data)
                                    else:  # пуля
                                        self.bullets[object_data['ID']] = object_data
                                else:
                                    self.user_data[object_data['NICK']] = object_data
                            if debug:
                                print('HOST SENT:', reply[0][0])
                        elif usr == 'CLIENT':  # клиент посылает инфу о себе, обновляем у себя
                            for i in range(len(reply[0])):
                                if i == 0:
                                    self.user_data[reply[0][i]['NICK']] = reply[0][i]
                                else:
                                    if reply[0][i]['ID'] not in self.bids:
                                        self.bullets.append(reply[0][i])
                                        self.bids.append(reply[0][i]['ID'])
                                    else:
                                        self.bullets[reply[0][i]['ID']] = reply[0][i]
                            if debug:
                                print('CLIENT SENT:', reply[0][0])
                        else:
                            raise Exception('UNEXPECTED USER')
                        for client_id in clients:
                            if clients[client_id] != conn:
                                clients[client_id].send(str.encode(str(['B', self.bullets])))
                        if debug:
                            print('SERVER DATA:', self.user_data, self.enemy_data)
            except Exception as e:
                print('\tSERVER//', e, 'DATA:', data)
                break

        print("\tConnection Closed")
        # clients.remove(conn)  # пока не стоит удалять
        conn.close()  # отключаемся

    def main(self):
        while True:
            conn, addr = self.s.accept()  # принимаем чела который заходит
            # conn - сокет, от него получаем и ему посылаем инфу, addr - просто адрес клиента
            print("Connected to: ", addr)

            clients[len(clients) + 1 if clients else 1] = conn
            start_new_thread(self.threaded_client, (conn,))  # параллельный поток для работы с новым юзером


if __name__ == "__main__":
    clients = {}
    locker = threading.Lock()
    debug = False
    mp_server = Server(int(list(open('SERVER_PORT.txt', 'r', encoding='utf-8'))[1].strip()), 2)
