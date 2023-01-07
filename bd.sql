DROP TABLE IF EXISTS perk;
CREATE TABLE perk (
    perk_id INT PRIMARY KEY,
    name_perk TEXT NOT NULL
    description_perk TEXT NOT NULL
);


DROP TABLE IF EXISTS player;
CREATE TABLE player (
    player_id INT PRIMARY KEY,
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


--INSERT INTO player(player_id, count_kill, sum_money, perk_id) VALUES(1, 999, 1000, 1);
--INSERT INTO player(player_id, count_kill, sum_money, perk_id) VALUES(2, 0, 10, 2);
