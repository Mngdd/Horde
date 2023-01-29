DROP TABLE IF EXISTS perk;
CREATE TABLE perk (
    perk_id INT PRIMARY KEY,
    name_perk TEXT NOT NULL,
    description_perk TEXT NOT NULL,
    func_name TEXT NOT NULL
);


DROP TABLE IF EXISTS trinket;
CREATE TABLE trinket (
    trinket_id INT PRIMARY KEY,
    name_trinket TEXT NOT NULL,
    description_trinket TEXT NOT NULL,
    func_name TEXT NOT NULL
);


DROP TABLE IF EXISTS player;
CREATE TABLE player (
    player_id INT PRIMARY KEY,
    nickname TEXT NOT NULL,
    count_kill INT NULL,
    sum_money INT NULL
);

DROP TABLE IF EXISTS player_perks;
CREATE TABLE player_perks (
    player_id INT NOT NULL,
    perk_id INT NOT NULL,
    FOREIGN KEY (player_id)
      REFERENCES player(player_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION,
    FOREIGN KEY (perk_id)
      REFERENCES perk(perk_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION
);

DROP TABLE IF EXISTS player_trinkets;
CREATE TABLE player_trinkets (
    player_id INT NOT NULL,
    trinket_id INT NOT NULL,
    FOREIGN KEY (player_id)
      REFERENCES player(player_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION,
    FOREIGN KEY (trinket_id)
      REFERENCES trinket(trinket_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION
);

INSERT INTO perk(perk_id, name_perk, description_perk, func_name) VALUES(1, 'Бегит', 'хоп хоп такой и потом быстро так бежиш, типа усейн болт типа пон', 'begit');
INSERT INTO perk(perk_id, name_perk, description_perk, func_name) VALUES(2, 'Анжумання', 'типа стрелять чтоб мощно так', 'sila');
INSERT INTO perk(perk_id, name_perk, description_perk, func_name) VALUES(3, 'прес качат', 'чтоб хп болш было', 'hp');

INSERT INTO trinket(trinket_id, name_trinket, description_trinket, func_name) VALUES(1, 'Парное оружие', 'чиста как гееенгста ходить с двумя пушками еуу', 'AKIMBO');
INSERT INTO trinket(trinket_id, name_trinket, description_trinket, func_name) VALUES(2, 'вампирисзсм', 'за 15 убитых врагов восстанавливает 10 хп', 'VAMPIRE_1');
INSERT INTO trinket(trinket_id, name_trinket, description_trinket, func_name) VALUES(3, 'ну типа чтоб стрелят быстро', 'темп стрельбы и ударов мили оружием выше', 'FAST_SHOOT_1');

INSERT INTO player(player_id, nickname, count_kill, sum_money) VALUES(1, 'ultra mega pon:)', 999, 1000);
INSERT INTO player(player_id, nickname, count_kill, sum_money) VALUES(2, 'ultra mini pon:(', 0, 0);
INSERT INTO player(player_id, nickname, count_kill, sum_money) VALUES(3, 'testik', 10, 10);

INSERT INTO player_perks(player_id, perk_id) VALUES(1, 1);
INSERT INTO player_perks(player_id, perk_id) VALUES(1, 2);
INSERT INTO player_perks(player_id, perk_id) VALUES(2, 3);

INSERT INTO player_trinkets(player_id, trinket_id) VALUES(1, 1);
INSERT INTO player_trinkets(player_id, trinket_id) VALUES(2, 1);
INSERT INTO player_trinkets(player_id, trinket_id) VALUES(2, 2);

