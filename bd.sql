DROP TABLE IF EXISTS perk;
CREATE TABLE perk (
    perk_id INT PRIMARY KEY,
    name_perk TEXT NOT NULL
    description_perk TEXT NOT NULL
);


DROP TABLE IF EXISTS trinket;
CREATE TABLE trinket (
    trinket_id INT PRIMARY KEY,
    name_trinket TEXT NOT NULL,
    description_trinket TEXT NOT NULL
);


DROP TABLE IF EXISTS player;
CREATE TABLE player (
    player_id INT PRIMARY KEY,
    nickname TEXT NOT NULL,
    count_kill INT NOT NULL,
    sum_money INT NOT NULL,
    perk_id int NOT NULL,
    FOREIGN KEY (perk_id) 
      REFERENCES perk(perk_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION,
);



INSERT INTO perk(perk_id, name_perk, description_perk) VALUES(1, 'Бегит', 'хоп хоп такой и потом быстро так бежиш');
INSERT INTO perk(perk_id, name_perk, description_perk) VALUES(2, 'Анжумання', 'типа стрелять чтоб мощно так');
INSERT INTO perk(perk_id, name_perk, description_perk) VALUES(3, 'прес качат', 'чтоб хп болш было');

INSERT INTO trinket(trinket_id, name_trinket, description_trinket) VALUES(1, 'Парное оружие', 'чиста как гееенгста ходить с двумя пушками еуу');
INSERT INTO trinket(trinket_id, name_trinket, description_trinket) VALUES(2, 'вампирисзсм', 'за 15 убитых врагов восстанавливает 10 хп');
INSERT INTO trinket(trinket_id, name_trinket, description_trinket) VALUES(3, 'ну типа чтоб стрелят быстро', 'темп стрельбы и ударов мили оружием выше');


INSERT INTO player(player_id, nickname, count_kill, sum_money, perk_id) VALUES(1, 'ultra mega pon:)', 999, 1000, 1);
INSERT INTO player(player_id, nickname, count_kill, sum_money, perk_id) VALUES(2, 'ultra mini pon:(', 0, 0, 2);
