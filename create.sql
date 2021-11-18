CREATE TABLE player(
	player_id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	PRIMARY KEY (player_id AUTOINCREMENT)
);

CREATE TABLE scoreboard (
	score_id INTEGER NOT NULL,
	time_stamp DATETIME NOT NULL,
	player_id INTEGER NOT NULL,
	score INTEGER NOT NULL,
	timeCompleted VARCHAR(255) NOT NULL,
	fails INTEGER NOT NULL,
	PRIMARY KEY(score_id AUTOINCREMENT),
	FOREIGN KEY(player_id) REFERENCES player(player_id)
);

INSERT INTO player (name) VALUES 
("Test 1"),
("Test 2")
;


INSERT INTO scoreboard (time_stamp, player_id, score, timeCompleted, fails) VALUES
('2021-10-28 10:09:40', 1, 800, '20.23',0),
('2021-10-28 10:10:12', 2, 775, '21.123',1)
;

CREATE VIEW scores AS 
					
	SELECT strftime('%d.%m.%Y %H:%M:%S', scoreboard.time_stamp) AS 'Eingetragen am', 
		(SELECT name AS Name FROM player WHERE player_id = scoreboard.player_id) AS Spielername,
			score AS Punkte FROM scoreboard ORDER BY fails, score, timeCompleted LIMIT 10;