import socket
import time


# здесь тупа отправляем и получаем от серва
class Network:
    def __init__(self, ip_port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip_port[0]  # ipv4 хоста
        self.port = int(ip_port[1])  # порт узнать у хоста
        self.addr = (self.host, self.port)  # адрес хоста полный
        for i in range(4):
            if i == 3:
                raise ConnectionRefusedError('CONNECTION REFUSED')
            time.sleep(0.5)  # чтоб сервак успел создаться если я хост
            try:
                self.id = self.connect()
                break
            except ConnectionRefusedError:
                print('CONNECTION REFUSED, ATTEMPT:', i)

    def connect(self):  # тут подключаемся к серву
        self.client.connect(self.addr)
        return self.client.recv(4096).decode()  # получаем id игрока

    def send(self, data):
        """
        :param data: str
        :return: str
        """
        try:
            self.client.send(str.encode(data))  # отправляем data
            reply = self.client.recv(4096).decode()  # получаем ответ сервера (переменные всякие)
            return reply
        except socket.error as e:
            return str(e)
