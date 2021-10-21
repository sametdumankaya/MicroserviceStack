CREATE TABLE magi.events (
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
leading_indicator varchar(50),
main_indicator varchar(50),
trailing_indicator varchar(50),
output_name varchar(100),
version int
);

CREATE TABLE magi.indicators (
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
leading_indicator MEDIUMTEXT,
main_indicator MEDIUMTEXT,
trailing_indicator MEDIUMTEXT,
output_name varchar(100),
version int
);

CREATE TABLE magi.contributors (
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
contribution double,
indicator MEDIUMTEXT,
event MEDIUMTEXT,
output_name varchar(100),
version int
);

CREATE TABLE magi.plots (
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
histogram LONGTEXT,
events LONGTEXT,
output_name varchar(100),
version int
);

CREATE TABLE magi.metadata (
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
params_json LONGTEXT,
output_name varchar(100),
version int
);