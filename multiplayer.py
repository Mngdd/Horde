# from main import Pawn, Player, Enemy, Deployable, Item, Projectile, Weapon
import pickle
import socket
import threading
import queue
import time


DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 5070
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
    def __init__(self, ip: str = DEFAULT_SERVER_IP, port: int = DEFAULT_SERVER_PORT, max_players: int = 3):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.players = dict()
        self.max_players = max_players
        self.unused_player_ids = [i for i in range(max_players)]
        self.socket.listen()
        self.new_players_thread = threading.Thread(target=self.listen_for_new_players)
        self.new_players_thread.start()
        self.ip = ip
        self.port = port

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
                conn.setblocking(False)
                data = conn.recv(SOCKET_BUFFER_SIZE)  # выбросит исключение, если сюда ничего не отправили
                conn.setblocking(True)
            except BlockingIOError:
                continue
            if data != b'connect':
                continue
            self.players[addr] = conn
            conn.send(b'connect')
            next_player_id = min(self.unused_player_ids)
            self.unused_player_ids.remove(next_player_id)
            conn.send(next_player_id.to_bytes(64, 'little'))
            thread = threading.Thread(target=self.handle_client, args=(conn, addr, next_player_id))
            thread.start()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int], player_id: int):
        print(f'подключился игрок № {player_id}')
        connected = True
        while connected:
            try:
                data = receive_whole_msg(conn)
            except ConnectionResetError:
                connected = False
                self.unused_player_ids.append(player_id)
                break
            for other_addr, other_conn in self.players.items():
                if addr != other_addr:
                    try:
                        other_conn.send(data)
                        other_conn.send(b'end')
                    except ConnectionResetError:
                        pass
        print(f'отключился игрок № {player_id}')


class Client:
    def __init__(self, server_ip: str = DEFAULT_SERVER_IP, server_port: int = DEFAULT_SERVER_PORT):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((server_ip, server_port))  # выбрасывает ConnectionRefusedError, если не получается
        self._conn.send(b'connect')
        if self._conn.recv(SOCKET_BUFFER_SIZE) != b'connect':
            raise ConnectionRefusedError
        self.id = int.from_bytes(self._conn.recv(SOCKET_BUFFER_SIZE), 'little')
        self._sync_commands = dict()
        self._create_commands = []
        self._listen_for_commands_thread = threading.Thread(target=self._listen_for_commands)
        self._listen_for_commands_thread.start()

    def _listen_for_commands(self):
        connected = True
        while connected:
            data = receive_whole_msg(self._conn)
            try:
                cmd = pickle.loads(data)
                if cmd[0] == CMD_SYNC:
                    id_ = cmd[1]
                    self._sync_commands[id_] = cmd
                elif cmd[0] == CMD_CREATE:
                    self._create_commands.append(cmd)
            except pickle.PickleError:
                continue

    def get_sync_command(self, id_: int):
        return self._sync_commands.pop(id_, None)

    def get_create_commands(self):
        res = tuple(reversed(self._create_commands))  # reversed чтобы сначала шли старые команды
        self._create_commands.clear()
        return res

    def cmd_create(self, id_: int, class_name: str, args: tuple, kwargs: dict):
        print((CMD_CREATE, id_, class_name, args, kwargs))
        self._conn.send(pickle.dumps((CMD_CREATE, id_, class_name, args, kwargs)))
        self._conn.send(b'end')

    def cmd_sync(self, id_: int, track_vars_dict: dict):
        self._conn.send(pickle.dumps((CMD_SYNC, id_, track_vars_dict)))
        self._conn.send(b'end')


class Synchronizable:  # TODO интегрировать в игру, протестировать, написать документацию
    def __init__(self, client: Client, args: tuple, kwargs: dict, create_for_all_players: bool = True):
        """не передавать в args или kwargs группы и прочие Surface-ы"""
        self.client = client
        self._track_vars = []
        self._not_track_vars = []
        # id селфа на разных компах могут совпадать, поэтому хэшим с id игрока
        self.id = hash((id(self), self.client.id))
        self._create_for_all_players = create_for_all_players
        self._args = args
        self._kwargs = kwargs

    @staticmethod
    def from_remote(id_: int, class_name: str, args: tuple, kwargs: dict, globals_: dict):
        # try:
        obj = globals_[class_name](*args, **kwargs)
        if isinstance(obj, Synchronizable):
            obj.id = id_
            obj._create_for_all_players = False
        return obj
        # except Exception:
        #     return None

    def _start_tracking(self):
        self._not_track_vars = list(self.__dict__.keys())

    def _stop_tracking(self, create_for_all_players: bool = True):
        self._track_vars = self._track_vars + [k for k in self.__dict__.keys() if k not in self._not_track_vars]
        self._not_track_vars = []
        # делаем это не в ините, чтобы когда обьект создается по команде сервера было время отключить это
        if self._create_for_all_players and create_for_all_players:
            self.client.cmd_create(self.id, self.__class__.__name__, self._args, self._kwargs)

    def sync_to_server(self):
        track_vars_dict = {k: self.__dict__[k] for k in self.__dict__ if k in self._track_vars}
        self.client.cmd_sync(self.id, track_vars_dict)

    def _sync_from_server(self, track_vars_dict: dict):
        # try:
        for k, v in track_vars_dict.items():
            setattr(self, k, v)
        return True
        # except Exception:
        #     return False

    def sync_from_server(self):
        cmd = self.client.get_sync_command(self.id)
        if cmd:
            self._sync_from_server(cmd[2])


def input_server_credentials(attempt_default_credentials: bool = True) -> tuple[str, int]:
    if attempt_default_credentials:
        return DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT
    invalid_ip = True
    while invalid_ip:
        ip = input('ip сервера: ')
        try:
            socket.inet_aton(ip.strip())
        except socket.error:
            invalid_ip = True
        else:
            invalid_ip = False
    invalid_port = True
    while invalid_port:
        try:
            port = int(input('порт сервера: ').strip())
            assert 0 <= port <= 65536
        except ValueError or AssertionError:
            invalid_port = True
        else:
            invalid_port = False
    return ip, port


if __name__ == '__main__':
    server = Server()
    print(f'адрес сервера: {server.ip}:{server.port}')
