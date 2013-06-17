import npyscreen
from os import path


class commandhandler():
    def __init__(self, parent, librewired):
        self.parent = parent
        self.librewired = librewired
        self.validCommands = self.parent.validCommands

    def checkCommand(self, string):
        command = 0
        for acommand in self.validCommands:
            if acommand.upper() == string[0:len(acommand)].upper():
                command = acommand
                break
        if not command:
            return 0
        parameter = string[len(command):].strip()
        if command == '/nick':
            self.changeNick(parameter)
        elif command == '/status':
            self.changeStatus(parameter)
        elif command == '/icon':
            self.changeIcon(parameter)
        elif command == '/ping':
            pass
        elif command == '/topic':
            self.setTopic(parameter)
        elif command == '/me':
            self.sendActionChat(parameter)
        elif command == '/clear':
            self.parent.box.values = []
            self.parent.box.update()
        return 1

    def changeNick(self, newNick):
        if newNick:
            self.librewired.changeNick(newNick)
            return 1
        return 0

    def changeStatus(self, newStatus):
        if newStatus:
            self.librewired.changeStatus(newStatus)
            return 1
        return 0

    def setTopic(self, newTopic):
        if not self.librewired.privileges['changeTopic']:
            npyscreen.notify_confirm("You are not allowed to change chat Topic", "Failed")
            return 0
        if not self.librewired.setChatTopic(self.parent.chat, newTopic):
            return 0

    def sendActionChat(self, chattext):
        if chattext:
            if self.librewired.sendChat(self.parent.chat, chattext, True):
                return 1
        return 0

    def changeIcon(self, iconpath):
        if not iconpath:
            return 0
        if not self.librewired.loadIcon(iconpath):
            return 0
        return 1
