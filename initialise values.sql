DROP TABLE IF EXISTS Exploration;

DROP TABLE IF EXISTS SAR;

CREATE TABLE Exploration (
'my_goal' TEXT NOT NULL PRIMARY KEY,
'epsilon' REAL NOT NULL
);

CREATE TABLE SAR (
'puck_pos_x' INTEGER NOT NULL,
'puck_pos_y' INTEGER NOT NULL,
'puck_speed_x' INTEGER NOT NULL,
'puck_speed_y' INTEGER NOT NULL,
'next_pos_x' INTEGER NOT NULL,
'next_pos_y' INTEGER NOT NULL,
'reward' INTEGER NOT NULL
);

INSERT INTO Exploration
VALUES('left', 0.999);
INSERT INTO Exploration
VALUES('right', 0.999);

