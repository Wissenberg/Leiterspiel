import smbus
import time
import random
import sqlite3
import datetime
import sys

class Settings:
    i2cAddress = 0x25
    busnumber = 1


class MCP23017:
    def __init__(self, i2c_address=Settings.i2cAddress, busnumber=Settings.busnumber):
        assert busnumber in [0, 1]
        self.i2c_address = i2c_address
        self.smbus = smbus.SMBus(busnumber)
        # configure default registers
        self._regs = {'conf': {'A': 0x00, 'B': 0x01},
                      'input': {'A': 0x12, 'B': 0x13},
                      'output': {'A': 0x14, 'B': 0x15}}

    def write_config(self, portab, value):
        assert portab in ['A', 'B']
        reg = self._regs['conf'][portab]
        self.smbus.write_byte_data(self.i2c_address, reg, value)

    def read_config(self, portab):
        assert portab in ['A', 'B']
        reg = self._regs['conf'][portab]
        return self.smbus.read_byte_data(self.i2c_address, reg)

    def write_output(self, portab, value):
        assert portab in ['A', 'B']
        reg = self._regs['output'][portab]
        self.smbus.write_byte_data(self.i2c_address, reg, value)

    def read_output(self, portab):
        assert portab in ['A', 'B']
        reg = self._regs['output'][portab]
        return self.smbus.read_byte_data(self.i2c_address, reg)

    def read_input(self, portab):
        assert portab in ['A', 'B']
        reg = self._regs['input'][portab]
        return self.smbus.read_byte_data(self.i2c_address, reg)

class DatabaseManager:
    def __init__(self):
        self.open_db_connection()

    def open_db_connection(self):
        try:
            self.con = sqlite3.connect('TopList.db')
            self.cur = self.con.cursor()
        except ConnectionError:
            self.open_db_connection()    
    
    def writeScore(self, timeCompleted, score, fails):   
        self.cur.execute("INSERT INTO scoreboard (time_stamp, player_id, score, timeCompleted, fails) VALUES ('%s',(SELECT player_id FROM player WHERE name = '%s'),%s,'%s',%s);" % (datetime.datetime.now(),self.checkForDuplicateName(),score,timeCompleted,fails))
        self.con.commit()

    def readScoreboard(self):
        scoreboard = []
        self.cur.execute("SELECT * FROM scores;")
        rows = self.cur.fetchall()
        
        for row in rows:
            scoreboard.append(row)
        
        return scoreboard
    
    def getUsername(self):
        return input("Bitte geben Sie ihren Benutzernamen für die Bestenliste ein: ")

    def checkForDuplicateName(self):
        username = self.getUsername()
        self.cur.execute("SELECT * FROM player;")
        rows = self.cur.fetchall()
        for row in rows:
            #[1,"Test"]
            if row[1] == username:
                return username

        self.cur.execute("INSERT INTO player(name)VALUES ('%s');" % username)
        return username

class GameController:
    def __init__(self):
        self.db = DatabaseManager()
        self.ioExpander = MCP23017()
        self.ioExpander.write_config(portab='B',value=0x1)
        self.ioExpander.write_config(portab='A',value=0x0)
        self.currentlevel = 0
        self.fails = 0
        self.playTime = 0
        self.isLedOn = 0
        self.score = 0

    
    def main(self):
        done = False
        self.startPlayTime = time.time()
        while not done:
            # Verloren
            if self.currentlevel == -1:
                print("Verloren")
                self.endPlayTime = time.time()
                self.db.writeScore(self.calcPlaytime(),self.calcScore(gameOver = True), self.fails)
                self.printScoreboard()
                self.playAgain()
            if self.currentlevel == 0:
                self.lvl(0x1)
            elif self.currentlevel == 1:
                self.lvl(0x3)
            elif self.currentlevel == 2:
                self.lvl(0x7)
            elif self.currentlevel == 3:
                self.lvl(0xF)
            elif self.currentlevel == 4:
                self.lvl(0x1F)
            elif self.currentlevel == 5:
                self.lvl(0x3F)
            elif self.currentlevel == 6:
                self.lvl(0x7F)
            # Gewonnen
            elif self.currentlevel == 7:
                self.endPlayTime = time.time()
                self.db.writeScore(self.calcPlaytime(),self.calcScore(gameOver = True), self.fails)
                self.printScoreboard()
                self.playAgain()


    def lvl(self, bitValue):
        startTime = time.time() 
        endTime = time.time()
        flashingSpeed = round(random.uniform(0.25,0.8),2)
        self.ioExpander.write_output('A', bitValue)

        while True:
            if (endTime - startTime) >= flashingSpeed:
                self.toggle_LED(bitValue)
                startTime = time.time()
                flashingSpeed = round(random.uniform(0.25,0.8),2)

            if self.readInput() == True and self.isLedOn == 1:
                self.currentlevel += 1
                self.calcScore()
                self.waitABit()
                break
            elif self.readInput() == True and self.isLedOn == 0:
                self.currentlevel -= 1
                self.fails += 1
                self.ioExpander.write_output('A', bitValue >> 2)
                self.waitABit()
                break

            endTime = time.time()

    def toggle_LED(self,bitValue):
        if self.isLedOn == 0:
            self.ioExpander.write_output('A', bitValue)
            self.isLedOn = 1
        else:
            self.ioExpander.write_output('A', bitValue >> 1)
            self.isLedOn = 0
    
    def waitABit(self):
        startTime = time.time()
        while True:
            if self.readInput() == False and self.currentlevel != -1:
                endTime = time.time()
                if (endTime - startTime) >= 0.5:
                    break 
            elif self.currentlevel == -1:
                break

    def readInput(self):
        return self.ioExpander.read_input('B')

    def calcScore(self, gameOver=False):
        self.score += 100
        if self.currentlevel == 7 or gameOver == True:
            self.score -= (self.fails * 120)
            if self.score < 0:
                self.score = 0
            return self.score

    def calcPlaytime(self):
        self.playTime = self.endPlayTime - self.startPlayTime
        return self.playTime
    
    def printScoreboard(self):
        scoreboard = self.db.readScoreboard()
        for x in scoreboard:
            print(x)

    def playAgain(self):
        userInput = input("Wollen Sie eine weitere Runde spielen? [y/n] ")
        if userInput == "y" or userInput == "Y" or userInput == "j" or userInput == "J":
            self.currentlevel = 0
            self.score = 0
            self.fails = 0
            self.startPlayTime = time.time()
        elif userInput == "n" or userInput == "N":
            self.setAllLedsOff()
            sys.exit()
        else:
            print("Fehler! ...")
            self.playAgain()
    
    def setAllLedsOff(self):
        self.ioExpander.write_output('A',0x0)
if __name__ == '__main__':
    main = GameController()
    main.main()