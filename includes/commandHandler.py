import npyscreen
from os import path
from sys import argv
from curses import beep, flash


class commandhandler():
    def __init__(self, parent, librewired):
        self.parent = parent
        self.librewired = librewired
        self.validCommands = self.parent.validCommands

    def checkCommand(self, string):
        command = 0
        for acommand in self.validCommands:
            check = string
            if " " in check:
                check = check.split(" ")[0]
            if acommand.upper() == check.upper():
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
        elif command == '/clear-all':
            self.parent.applyCommandToAll('/clear')
        elif command == '/clear':
            self.parent.box.values = []
            self.parent.box.update()
        elif command == '/afk-all':
            self.parent.applyCommandToAll('/afk')
        elif command == '/afk':
            if ' [afk]' in self.librewired.status\
                    or ' [zZz]' in self.librewired.status:
                return 1
            self.librewired.status = self.librewired.status + ' [afk]'
            self.librewired.changeStatus(self.librewired.status)
        elif command == '/away-all':
            self.parent.applyCommandToAll('/away')
        elif command == '/away':
            if ' [afk]' in self.librewired.status\
                    or ' [zZz]' in self.librewired.status:
                return 1
            self.librewired.status = self.librewired.status + ' [zZz]'
            self.librewired.changeStatus(self.librewired.status)
        elif command == '/back-all':
            self.parent.applyCommandToAll('/back')
        elif command == '/back':
            status = 0
            if ' [afk]' in self.librewired.status:
                status = self.librewired.status[:self.librewired.status.find(' [afk]')]
            elif ' [zZz]' in self.librewired.status:
                status = self.librewired.status[:self.librewired.status.find(' [zZz]')]
            if status:
                self.librewired.status = status
                self.librewired.changeStatus(self.librewired.status)
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
        if not path.exists(iconpath):
            homepath = path.dirname(argv[0])
            if path.exists(path.join(homepath, iconpath)):
                iconpath = path.join(homepath, iconpath)
            else:
                beep()
                return 0
        if not self.librewired.loadIcon(iconpath):
            return 0
        return 1
