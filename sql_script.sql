use soccer;


CREATE TABLE inplay (id int NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), insert_time datetime, crawler varchar(255), fp char(255) NOT NULL,
league char(255), date Date NOT NULL,  team_h char(255) NOT NULL, team_a char(255) NOT NULL, minute smallint NOT NULL,  
corner_h smallint, corner_a smallint,  yellow_h smallint, yellow_a smallint,  red_h smallint, red_a smallint,
throw_h smallint, throw_a smallint,  freekick_h smallint, freekick_a smallint,  goalkick_h smallint, goalkick_a smallint,  penalty_h smallint, penalty_a smallint,
goal_h smallint, goal_a smallint,  attacks_h smallint, attacks_a smallint,  dangerous_attacks_h smallint, dangerous_attacks_a smallint,
possession_h smallint, possession_a smallint,  on_target_h smallint, on_target_a smallint,  off_target_h smallint, off_target_a smallint,  odds_fulltime varchar(255),
odds_double varchar(255),  odds_corners varchar(255), odds_asian_corners varchar(255), odds_match_goals varchar(255), odds_alter_goals varchar(255), 
odds_goals_odd_even varchar(255), odds_most_corners varchar(255));


drop table inplay;

select * from inplay;
select count(*) from inplay