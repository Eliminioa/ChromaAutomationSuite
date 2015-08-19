drop table if exists players;
drop table if exists lores;
CREATE TABLE players (
  username text PRIMARY KEY NOT NULL ,
  side integer NOT NULL ,
  recruited boolean NOT NULL ,
  usertype integer NOT NULL,
  accessInfo text
);

CREATE TABLE lores (
  loreID integer PRIMARY KEY AUTOINCREMENT NOT NULL ,
  author text ,
  title text ,
  creationDate integer ,
  content text ,
  series text ,
  chapter integer ,
  wordCount integer
);

INSERT INTO players (username, side, recruited, usertype) VALUES ('Eliminioa', 1, 0 , 2);