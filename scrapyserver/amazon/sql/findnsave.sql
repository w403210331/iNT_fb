/*
 areaid :
 area   :
 short  : state short
 state  :
 url    :
 */
CREATE TABLE `findnsave_area` (
  `areaid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `area` varchar(255) NOT NULL DEFAULT '',
  `short` varchar(8) NOT NULL DEFAULT '',
  `state` varchar(64) NOT NULL DEFAULT '',
  `url` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`areaid`),
  UNIQUE KEY `area_state_city` (`areaid`,`area`,`state`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8


/*
 id     :
 name   :
 nameid :
 uri    :
 */
CREATE TABLE `findnsave_store` (
  `_ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `id` int(32) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `nameid` varchar(128) NOT NULL DEFAULT '',
  `uri` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID` (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

/*
 id     :
 name   :
 nameid :
 uri    :
 */
CREATE TABLE `findnsave_brand` (
  `_ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `id` int(32) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `nameid` varchar(128) NOT NULL DEFAULT '',
  `uri` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID` (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

