import sqlite3
import logging
from os.path import isfile

structure = """
CREATE TABLE `bonus` (
    `ID` INTEGER NOT NULL, 
    `Inviter` INTEGER NOT NULL, 
    `Bonus` INTEGER NOT NULL,
    PRIMARY KEY (`ID`,`Inviter`)
);

CREATE TABLE `config` (
  `ID` INTEGER NOT NULL,
  `Lang` TEXT NOT NULL DEFAULT 'en',
  `Welcome` INTEGER NOT NULL DEFAULT '0',
  `WelcomeChannel` INTEGER DEFAULT NULL,
  `WelcomeMessage` TEXT NOT NULL DEFAULT 'Welcome {member}, invited by {inviter}, you are the {membernum} member on this server.',
  `WelcomeEmbed` INTEGER NOT NULL DEFAULT '1',
  `NumBot` INTEGER NOT NULL DEFAULT '0',
  `BotChannel` INTEGER DEFAULT NULL,
  `BotChannelName` TEXT NOT NULL DEFAULT 'Bots : {botnumber}',
  `MemberChannel` INTEGER DEFAULT NULL,
  `MemberChannelName` TEXT NOT NULL DEFAULT 'All Members : {memnumber}',
  `AdminRole` INTEGER DEFAULT NULL,
  `AutoRole` INTEGER DEFAULT NULL,
  `GoalName` TEXT NOT NULL DEFAULT 'Goal : {goal} members',
  `GoalID` INTEGER DEFAULT NULL,
  `Goodbye` INTEGER NOT NULL DEFAULT '0',
  `GoodbyeChannel` INTEGER DEFAULT NULL,
  `GoodbyeMessage` TEXT NOT NULL DEFAULT 'Goodbye {member}, there are now {membernum} member on this server.',
  `GoodbyeEmbed` INTEGER NOT NULL DEFAULT '1',
  `RemoveOldRankOnRankup` INTEGER NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
);

CREATE TABLE `goal` (
    `ID` INTEGER NOT NULL, 
    `Goal` INTEGER NOT NULL, 
    PRIMARY KEY (`ID`,`Goal`)
);

CREATE TABLE `invite` (
    `ID` INTEGER NOT NULL, 
    `Inviter` INTEGER NOT NULL, 
    `Invited` INTEGER NOT NULL,
    `HasLeave` INTEGER NOT NULL DEFAULT '0', 
    PRIMARY KEY (`ID`,`Inviter`,`Invited`)
);

CREATE TABLE `rank` (
    `ID` INTEGER NOT NULL, 
    `RankID` INTEGER NOT NULL, 
    `Count` INTEGER NOT NULL,
    PRIMARY KEY (`ID`,`RankID`, `Count`)
);
"""


class DatabaseHandler:
    def __init__(self):
        if not isfile('invitemanager-delta.db'):
            logging.info("Database created")
            self.db = sqlite3.connect("invitemanager-delta.db")
            cursor = self.db.cursor()
            cursor.executescript(structure)
            cursor.close()
        else:
            self.db = sqlite3.connect("invitemanager-delta.db")

    def db_update(self):
        cursor = self.db.cursor()
        cursor.executescript(structure)
        cursor.close()

    def add_goodbye(self):
        cursor = self.db.cursor()
        new = [
        "`Goodbye` INTEGER NOT NULL DEFAULT '0'",
        "`GoodbyeChannel` INTEGER DEFAULT NULL",
        "`GoodbyeMessage` TEXT NOT NULL DEFAULT 'Goodbye {member}, there are now {membernum} member on this server.'",
        "`GoodbyeEmbed` INTEGER NOT NULL DEFAULT '1'"
        ]
        for n in new:
            cursor.execute("ALTER TABLE `config` ADD COLUMN " + n)
        cursor.close()
        self.db.commit()

    def update_invite_leave(self, leave, guild, invited):
        cursor = self.db.cursor()
        query = "UPDATE `invite` SET `hasleave` = ? WHERE `ID` = ? AND `Invited` = ?"
        query_tuple = (leave, guild, invited)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def add_invite(self, guild, inviter, invited):
        cursor = self.db.cursor()
        query = "DELETE FROM `invite` WHERE `ID`=? AND `Invited`=?"
        query_tuple = (guild, invited)
        cursor.execute(query, query_tuple)
        query = "INSERT OR IGNORE INTO `invite`(`ID`,`Inviter`,`Invited`) VALUES (?,?,?)"
        query_tuple = (guild, inviter, invited)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def set_bonus(self, guild, member, bonus):
        cursor = self.db.cursor()
        query = "INSERT INTO `bonus`(`ID`,`Inviter`,`Bonus`) VALUES (?,?,?) ON CONFLICT DO UPDATE SET `Bonus`=?"
        query_tuple = (guild, member, bonus, bonus)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def get_bonus(self, guild, member):
        cursor = self.db.cursor()
        query = "SELECT `bonus` FROM `bonus` WHERE `inviter`=? AND `ID`=?"
        query_tuple = (member, guild)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        return data[0] if data else 0

    def get_invites_data(self, guild, member):
        cursor = self.db.cursor()
        query = "SELECT COUNT(`invited`),SUM(`hasleave`) FROM `invite` WHERE `inviter`=? AND `ID`=?"
        query_tuple = (member, guild)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        query = "SELECT `bonus` FROM `bonus` WHERE `inviter`=? AND `ID`=?"
        query_tuple = (member, guild)
        cursor.execute(query, query_tuple)
        bonus = cursor.fetchone()
        bonus = 0 if not bonus else bonus[0]
        invites = data[0]
        leave = 0 if not data[1] else data[1]
        cursor.close()
        return [invites - leave, leave, bonus]
    
    def get_top_invites(self, guild, limit):
        cursor = self.db.cursor()
        query = "SELECT `inviter`, COUNT(`invited`)-SUM(`hasleave`) as `invites` FROM `invite` WHERE `ID`=? GROUP BY `inviter` ORDER BY `invites` DESC LIMIT ?"
        query_tuple = (guild, limit)
        cursor.execute(query, query_tuple)
        data = cursor.fetchall()
        cursor.close()
        return data 

    def get_inviter(self, guild, invited):
        cursor = self.db.cursor()
        query = "SELECT `inviter` FROM `invite` WHERE `invited`=? AND `ID`=?"
        query_tuple = (invited, guild)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        cursor.close()
        return data[0] if data else None

    def set_config(self, guild, key, value):
        cursor = self.db.cursor()
        query = "INSERT INTO `config`(`ID`,{}) VALUES (?,?) ON CONFLICT DO UPDATE SET {}=?".format(key, key)
        query_tuple = (guild, value, value)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def get_config(self, guild, key):
        cursor = self.db.cursor()
        query = "SELECT {} FROM `config` WHERE `ID`=?".format(key)
        query_tuple = (guild,)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        if not data:
            query = "INSERT INTO `config`(`ID`) VALUES (?)"
            query_tuple = (guild,)
            cursor.execute(query, query_tuple)

            query = "SELECT {} FROM `config` WHERE `ID`=?".format(key)
            query_tuple = (guild,)
            cursor.execute(query, query_tuple)
            data = cursor.fetchone()
        return data[0] if data else None

    def get_all_config(self, guild):
        cursor = self.db.cursor()
        query = "SELECT * FROM `config` WHERE `ID`=?"
        query_tuple = (guild,)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        if not data:
            query = "INSERT INTO `config`(`ID`) VALUES (?)"
            query_tuple = (guild,)
            cursor.execute(query, query_tuple)

            query = "SELECT * FROM `config` WHERE `ID`=?"
            query_tuple = (guild,)
            cursor.execute(query, query_tuple)
            data = cursor.fetchone()
        return data or None

    def set_goals(self, guild, goals):
        cursor = self.db.cursor()
        query = "DELETE FROM `goal` WHERE `ID`=?"
        query_tuple = (guild,)
        cursor.execute(query, query_tuple)
        query = "INSERT INTO `goal`(`ID`,`Goal`) VALUES (?,?)"
        records = [(guild, goal) for goal in goals]
        cursor.executemany(query, records)
        cursor.close()
        self.db.commit()

    def get_goal(self, guild, num):
        cursor = self.db.cursor()
        query = "SELECT MIN(`Goal`) FROM `goal` WHERE `ID`=? AND `Goal`>?"
        query_tuple = (guild, num)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        return data[0] if data else None

    def get_goals(self, guild):
        cursor = self.db.cursor()
        query = "SELECT `Goal` FROM `goal` WHERE `ID`=?"
        query_tuple = (guild,)
        cursor.execute(query, query_tuple)
        data = cursor.fetchall()
        data = [d[0] for d in data]
        return data or None

    def set_rank(self, guild, rank, count):
        cursor = self.db.cursor()
        query = "INSERT INTO `rank`(`RankID`,`Count`,`ID`) VALUES (?,?,?) ON CONFLICT DO UPDATE SET `Count`=?"
        query_tuple = (rank, count, guild, count)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def del_rank(self, rank):
        cursor = self.db.cursor()
        query = "DELETE FROM `rank` WHERE `RankID`=?"
        query_tuple = (rank,)
        cursor.execute(query, query_tuple)
        cursor.close()
        self.db.commit()

    def get_rank_count(self, guild, count):
        cursor = self.db.cursor()
        # also get the old rank id (the one nearest to the count but lower than it)
        query = "SELECT `RankID` FROM `rank` WHERE `Count`=? AND `ID`=?"
        query_tuple = (count, guild)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        query = "SELECT `RankID` FROM `rank` WHERE `Count`<? AND `ID`=? ORDER BY `Count` DESC"
        cursor.execute(query, query_tuple)
        data2 = cursor.fetchone()
        return data[0] if data else 0, data2[0] if data2 else 0

    def get_rank_with_id(self, rank_id):
        cursor = self.db.cursor()
        query = "SELECT `RankID` FROM `rank` WHERE `RankID`=?"
        query_tuple = (rank_id,)
        cursor.execute(query, query_tuple)
        data = cursor.fetchone()
        return data[0] if data else 0

    def get_ranks(self, guild):
        cursor = self.db.cursor()
        query = "SELECT * FROM `rank` WHERE `ID`=? ORDER BY `Count` DESC"
        query_tuple = (guild,)
        cursor.execute(query, query_tuple)
        data = cursor.fetchall()
        return data or None
