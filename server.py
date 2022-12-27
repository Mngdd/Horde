import socket
from _thread import *
import ast


class Server:
    def __init__(self, port, capacity):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = list(open('USER_IP.txt', 'r', encoding='utf-8'))[0].strip()  # ipv4 этого компа
        self.port = port  # от 0 до 65535, 0-1023 требует админа
        self.server_ip = socket.gethostbyname(self.server)  # тут чета происходит, но я не шарю

        self.is_port_in_use(self.port)  # проверяем, занят ли порт

        try:
            self.s.bind((self.server, self.port))  # связываем сокет и порт
        except socket.error as e:
            print(str(e))

        self.s.listen(capacity)  # максимум челиксов на серве
        print("\tWaiting for a connection")
        self.user_nickname = None
        self.user_data = {}  # {'test': {'online': False, 'ip': -1, 'vars': [None]}}
        self.enemy_data = None  # тупа спрайт группа капец я умный да
        self.main()

    def is_port_in_use(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                raise Exception('PORT ALREADY IN USE')

    def threaded_client(self, conn):  # вот тут крч мы с челом работаем
        conn.send(str.encode(str(self.user_nickname)))  # зачем не знаю
        reply = 'NONE'  # отве
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

                    if usr == 'HOST':  # обработанные хостом данные
                        for p_data in reply[0]:  # обновляем игроков
                            self.user_data[p_data['NICK']] = p_data
                    elif usr == 'CLIENT':  # клиент посылает инфу о себе, обновляем у себя
                        print(reply[0][0])
                        print(reply[0][0]['NICK'])
                        self.user_data[reply[0][0]['NICK']] = reply[0][0]
                    else:
                        raise Exception('UNEXPECTED USER')

                # print("Sending: ", reply)
                conn.sendall(str.encode(str([self.user_data, self.enemy_data])))  # всем рассылаем инфу(координаты)
            except Exception as e:
                print('\tSERVER//', e, data)
                break

        print("\tConnection Closed")
        conn.close()  # отключаемся

    def main(self):
        while True:
            conn, addr = self.s.accept()  # принимаем чела который заходит
            # conn - сокет, от него получаем и ему посылаем инфу, addr - просто адрес клиента
            print("Connected to: ", addr)
            start_new_thread(self.threaded_client, (conn,))  # параллельный поток для работы с новым юзером


if __name__ == "__main__":
    mp_server = Server(int(list(open('USER_IP.txt', 'r', encoding='utf-8'))[1].strip()), 2)
