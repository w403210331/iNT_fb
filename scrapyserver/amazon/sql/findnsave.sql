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
  `id` int(11) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `nameid` varchar(128) NOT NULL DEFAULT '',
  `uri` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID` (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

CREATE TABLE `findnsave_brand` (
  `_ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `id` int(11) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `nameid` varchar(128) NOT NULL DEFAULT '',
  `uri` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID` (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

CREATE TABLE `findnsave_category` (
  `_ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `id` int(11) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `nameid` varchar(128) NOT NULL DEFAULT '',
  `uri` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID` (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

CREATE TABLE `findnsave_sale_t` (
  `_ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `area` varchar(16) NOT NULL DEFAULT '',
  `id` int(11) unsigned NOT NULL,
  `name` varchar(128) NOT NULL DEFAULT '',
  `priceCurrency` varchar(16) NOT NULL DEFAULT '',
  `price` float(16) NOT NULL DEFAULT 0,
  `priceRegular` float(16) NOT NULL DEFAULT 0,
  `priceUtilDate` varchar(16) NOT NULL DEFAULT '',
  `priceOff` varchar(16) NOT NULL DEFAULT '',
  `retailer` varchar(64) NOT NULL DEFAULT '',
  `category` varchar(128) NOT NULL DEFAULT '',
  `brand` varchar(64) NOT NULL DEFAULT '',
  `desc` text NOT NULL DEFAULT '',
  PRIMARY KEY (`_ID`),
  UNIQUE KEY `ID_area` (`id`, `area`),
  KEY `name` (`name`),
  KEY `retailer` (`retailer`),
  KEY `category` (`category`),
  KEY `brand` (`brand`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8

