import pygame
import sqlite3
from typing import Dict


class Trinket:
    def __init__(self, id=0, name="", description="") -> None:
        self._id: int = id
        self._name: str = name
        self._description: str = description

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class Perk:
    def __init__(self, id=0, name="", description="") -> None:
        self._id: int = id
        self._name: str = name
        self._description: str = description

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class User:
    def __init__(self, id=0, nickname="", count_kill=0, sum_money=0, perk="") -> None:
        self._id: int = id
        self._nickname: str = nickname
        self._count_kill: int = count_kill
        self._sum_money: int = sum_money
        self._perk: str = perk

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

    @property
    def perk(self) -> str:
        return self._perk


class Record:
    def __init__(self, db_path='horde.sqlite') -> None:
        self._con = sqlite3.connect(db_path)
        self._sorted_users: Dict[int, User] = {}
        self._perks: Dict[int, Perk] = {}
        self._trinkets: Dict[int, Trinket] = {}

    def load_result(self):
        cur = self._con.cursor()
        self._sorted_users = cur.execute(
            "SELECT player_id, nickname, count_kill, sum_money FROM player ORDER BY count_kill").fetchall()

    def load_perk(self):
        cur = self._con.cursor()
        self._perks = cur.execute(
            "SELECT perk_id, name_perk, description_perk FROM perk").fetchall()

    def load_trinket(self):
        cur = self._con.cursor()
        self._trinkets = cur.execute(
            "SELECT trinket_id, name_trinket, description_trinket FROM trinket").fetchall()



