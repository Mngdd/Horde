# Horde
pygame top-down game

## Введение

Цель игрока - выжить 3 волны. Для того, чтобы не умереть от врагов в магазине можно купить оружие. Чем круче оружие, тем дороже оно стоит.
Ник игрока, количество убийств записываются в базу данных и при прохождения уровня появляется таблица всех игроков. Место в таблице рекордов определяется количеством убитых.
Перк - усиление, которое можно купить навсегда.
Тринкет - усиление на одну игру.

## Управление

W - вперед;   
A - влево;   
S - вниз;    
D - вправо;        
E - открыть магазин/подобрать оружие;          
Q - бросить оружие;    
Левая кнопка мыши - стрелять;

## База данных

База данных состоит из 5 таблиц.   
Таблица `player`: id игрока, ник, количество убийств, количество денег.    
Таблица `perk`: id, название, описание, название связанной функции.   
Таблица `trinket`: id, название, описание, название связанной функции.    
Таблица `player_perks`: id игрока, id перка.    
*связывает все перки игрока с самим игроком.     
Таблица `player_trinkets`: id игрока, id тринкета.    
*связывает все тринкеты игрока с самим игроком

