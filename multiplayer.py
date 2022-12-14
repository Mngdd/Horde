from main import *
import pickle
import socket


CMD_CREATE = 0
CMD_SYNCH = 1


def cmd_create(id_: int, class_name: str, args: tuple, kwargs: dict):
    return pickle.dumps((CMD_CREATE, id_, class_name, args, kwargs))


def cmd_synch(id_: int, track_vars_dict: dict):
    return pickle.dumps((CMD_SYNCH, id_, track_vars_dict))


class Synchronizable:  # TODO интегрировать в игру, протестировать, написать документацию
    def __init__(self, client: socket.socket, player_id: int, args: tuple, kwargs: dict,
                 create_for_all_players: bool = True):
        self.client = client
        self._track_vars = []
        self._not_track_vars = []
        # id селфа на разных компах могут совпадать, поэтому хэшим с id игрока
        self.id = hash((id(self), player_id))
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
            byets_sent = self.client.send(cmd_create(self.id, self.__class__.__name__, self._args, self._kwargs))
            assert byets_sent <= 4096

    def synch_to_server(self):
        track_vars_dict = {k: self.__dict__[k] for k in self.__dict__ if k in self._track_vars}
        bytes_sent = self.client.send(cmd_synch(self.id, track_vars_dict))
        # получатель получит обрезанное сообщение; надо увеличить везде буфера или реализовать получение по частям
        assert bytes_sent <= 4096

    def synch_from_server(self, track_vars_dict: dict):
        try:
            for k, v in track_vars_dict.items():
                setattr(self, k, v)
            return True
        except Exception:
            return False
