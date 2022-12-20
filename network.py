import socket


# здесь тупа отправляем и получаем от серва
class Network:

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = list(open('USER_IP.txt', 'r', encoding='utf-8'))[0].strip()  # ipv4 хоста
        self.port = 5555  # порт узнать у хоста
        self.addr = (self.host, self.port)  # адрес хоста полный
        self.id = self.connect()

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
