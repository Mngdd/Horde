import sqlite3
from typing import Dict, List


class Trinket:
    def __init__(self, id=0, name="", description="", func_name="") -> None:
        self._id: int = id
        self._name: str = name
        self._description: str = description
        self._func_name: str = func_name

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def func_name(self) -> str:
        return self._func_name

class PlayerTrinkets:
    def __init__(self, player_id=0, trinket_id=0) -> None:
        self._player_id: int = player_id
        self._trinket_id: int = trinket_id

    @property
    def player_id(self) -> int:
        return self._player_id
    
    @property
    def trinket_id(self) -> int:
        return self._trinket_id


class PlayerPerks:
    def __init__(self, player_id=0, perk_id=0) -> None:
        self._player_id: int = player_id
        self._perk_id: int = perk_id

    @property
    def player_id(self) -> int:
        return self._player_id
    
    @property
    def perk_id(self) -> int:
        return self._perk_id


class Perk:
    def __init__(self, id=0, name="", description="", func_name="") -> None:
        self._id: int = id
        self._name: str = name
        self._description: str = description
        self._func_name: str = func_name

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def func_name(self) -> str:
        return self._func_name



class Player:
    def __init__(self, id=0, nickname="", count_kill=0, sum_money=0) -> None:
        self._id: int = id
        self._nickname: str = nickname
        self._count_kill: int = count_kill
        self._sum_money: int = sum_money

    @property
    def id(self) -> int:
        return self._id

    @property
    def nickname(self) -> str:
        return self._nickname

    @property
    def count_kill(self) -> int:
        return self._count_kill

    @property
    def sum_money(self) -> int:
        return self._sum_money



class Record:
    def __init__(self, db_path='horde.sqlite') -> None:
        self._con = sqlite3.connect(db_path)
        self._players = []
        self._perks = []
        self._trinkets = []
        self._update_kill = []

    def load_players(self):
        self._players.clear()
        cur = self._con.cursor()
        self._players = cur.execute(
            "SELECT player_id, nickname, count_kill, sum_money FROM player ORDER BY count_kill").fetchall()

    def get_records(self):
        cur = self._con.cursor()
        self._players = cur.execute(
            "SELECT player_id, nickname, count_kill, sum_money FROM player ORDER BY count_kill").fetchall()
        return self._players[::-1]

    def get_perks(self):
        cur = self._con.cursor()
        self._perks = cur.execute(
            "SELECT perk_id, name_perk, description_perk FROM perk").fetchall()
        return self._perks

    def get_trinkets(self):
        cur = self._con.cursor()
        self._trinkets = cur.execute(
            "SELECT trinket_id, name_trinket, description_trinket FROM trinket").fetchall()
        return self._trinkets

    def add_nickname(self, nickname):
        cmd_max_id = "SELECT MAX(player_id) FROM player"
        cur = self._con.execute(cmd_max_id).fetchall()
        max_id = cur[0][0] + 1
        cmd = f"INSERT OR REPLACE INTO player(player_id, nickname) VALUES({max_id}, '{nickname}')"
        cur = self._con.execute(cmd)
        self._con.commit()
        self.load_players()

    def update_player(self, nickname, count_kill, sum_money, perk_id):
        cur = self._con.cursor()
        self._players = cur.execute(
            f"UPDATE player SET count_kill = {count_kill}, sum_money = {sum_money}, perk_id = {perk_id} WHERE nickname = '{nickname}'")
        self._con.commit()
        self.load_players()

    # def save_money(self, nickname, money):
    #     cur = self._con.cursor()
    #     self._update_money = cur.execute(f"UPDATE player set sum_money = {money} WHERE nickname = '{nickname}'")
    #     self.load_players()

    # def get_money(self):
    #     cmd_max_id = "SELECT MAX(player_id) FROM player"
    #     cur = self._con.cursor()
    #     nickname = cur.execute(f"SELECT nickname FROM player WHERE player_id = {cmd_max_id}")
    #     self._money = cur.execute(f"SELECT sum_money FROM player WHERE nickname = '{nickname}'")
    #     return self._money

    def update_kill(self, count_kill, nickname):
        cur = self._con.cursor()
        cmd = f"UPDATE player set count_kill = {count_kill} WHERE nickname = '{nickname}'"
        self._update_kill = cur.execute(cmd)
        self._con.commit()
        self.load_players()
        return self._update_kill

