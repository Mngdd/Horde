from main import *
import pickle
import socket
import threading
import queue
import time


DEFAULT_PORT = 5070
SOCKET_BUFFER_SIZE = 4096

CMD_CREATE = 0
CMD_SYNC = 1


def receive_whole_msg(conn: socket.socket, end_msg=b'end'):
    chunk = conn.recv(SOCKET_BUFFER_SIZE)
    chunks = [chunk]
    while chunk != end_msg:
        chunk = conn.recv(SOCKET_BUFFER_SIZE)
        chunks.append(chunk)
    return b''.join(chunks[:-1])  # обрезаем последний т. к. он b'end'


class Server:
    def __init__(self, ip: str = '127.0.0.1', port: int = DEFAULT_PORT, max_players: int = 3):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.players = dict()
        self.max_players = max_players
        self.next_player_id = 0
        self.socket.listen()
        self.new_players_thread = threading.Thread(target=self.listen_for_new_players)
        self.new_players_thread.start()

    def listen_for_new_players(self):
        listening = True
        while listening:
            if len(self.players) > self.max_players:
                time.sleep(1)  # спим, чтобы не нагружать особо наверное
                continue
            conn, addr = self.socket.accept()
            time.sleep(0.5)
            # если ничего не получим в течение полусекунды, то нафиг надо
            try:
                data = conn.recv(SOCKET_BUFFER_SIZE, socket.MSG_DONTWAIT)  # выбросит исключение, если придется ждать
            except socket.EWOULDBLOCK or socket.EAGAIN:
                continue
            if data != b'connect':
                continue
            self.players[addr] = conn
            conn.send(b'connect')
            conn.send(self.next_player_id.to_bytes(64, 'little'))
            self.next_player_id += 1
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]):
        connected = True
        while connected:
            data = receive_whole_msg(conn)
            for other_addr, other_conn in self.players.items():
                if addr != other_addr:
                    other_conn.send(data)
                    other_conn.send(b'end')


class Client:
    def __init__(self, server_ip: str, server_port: int = DEFAULT_PORT):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((server_ip, server_port))
        self._conn.send(b'connect')
        assert self._conn.recv(SOCKET_BUFFER_SIZE) == b'connect'
        self.id = int.from_bytes(self._conn.recv(SOCKET_BUFFER_SIZE), 'little')
        self._cmd_queue = queue.Queue()
        self._listen_for_commands_thread = threading.Thread(target=self._listen_for_commands, args=(self._cmd_queue,))
        self._listen_for_commands_thread.start()

    def _listen_for_commands(self, cmd_queue: queue.Queue):
        connected = True
        while connected:
            data = receive_whole_msg(self._conn)
            try:
                cmd = pickle.loads(data)
            except pickle.PickleError:
                continue
            cmd_queue.put(cmd, block=False)

    def get_commands(self):
        commands = []
        while not self._cmd_queue.empty():
            try:
                commands.append(self._cmd_queue.get(block=False))
            except queue.Empty:
                break
        return commands

    def cmd_create(self, id_: int, class_name: str, args: tuple, kwargs: dict):
        self._conn.send(pickle.dumps((CMD_CREATE, id_, class_name, args, kwargs)))
        self._conn.send(b'end')

    def cmd_sync(self, id_: int, track_vars_dict: dict):
        self._conn.send(pickle.dumps((CMD_SYNC, id_, track_vars_dict)))
        self._conn.send(b'end')


class Synchronizable:  # TODO интегрировать в игру, протестировать, написать документацию
    def __init__(self, client: Client, args: tuple, kwargs: dict, create_for_all_players: bool = True):
        self.client = client
        self._track_vars = []
        self._not_track_vars = []
        # id селфа на разных компах могут совпадать, поэтому хэшим с id игрока
        self.id = hash((id(self), self.client.id))
        self._create_for_all_players = create_for_all_players
        self._args = args
        self._kwargs = kwargs

    @staticmethod
    def from_remote(id_: int, class_name: str, args: tuple, kwargs: dict):
        try:
            obj = globals()[class_name].__init__(*args, **kwargs)
            if isinstance(obj, Synchronizable):
                obj.id = id_
                obj._create_for_all_players = False
            return obj
        except Exception:
            return None

    def _start_tracking(self):
        self._not_track_vars = list(self.__dict__.keys())

    def _stop_tracking(self):
        self._track_vars = [k for k in self.__dict__.keys() if k not in self._not_track_vars]
        self._not_track_vars = []
        # делаем это не в ините, чтобы когда обьект создается по команде сервера было время отключить это
        if self._create_for_all_players:
            self.client.cmd_create(self.id, self.__class__.__name__, self._args, self._kwargs)

    def sync_to_server(self):
        track_vars_dict = {k: self.__dict__[k] for k in self.__dict__ if k in self._track_vars}
        self.client.cmd_sync(self.id, track_vars_dict)

    def sync_from_server(self, track_vars_dict: dict):
        try:
            for k, v in track_vars_dict.items():
                setattr(self, k, v)
            return True
        except Exception:
            return False
