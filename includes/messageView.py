from time import time
from datetime import datetime
from includes import rewireFunctions
import npyscreen
import curses


class messageview():
    def __init__(self, parent, formid):
        self.parent = parent
        self.formid = formid
        self.msguserids = self.parent.msguserids
        self.nicks = self.parent.msgnicks
        self.msgs = self.parent.msgs
        self.max_x = self.parent.max_x
        self.max_y = self.parent.max_y
        self.displayUid = 0
        self.displayMsg = 0

    def build(self):
        self.popup = npyscreen.FormBaseNew(name="Messages - %s" % self.parent.host,
                                           framed=True, relx=0, rely=0, lines=self.max_y - 3,
                                           columns=self.max_x - 3)
        self.popup.formid = self.formid
        self.popup.show_atx = 1
        self.popup.show_aty = 1
        self.popup.add_handlers({curses.KEY_F3: self.close})
        self.popup.add_handlers({curses.KEY_F1: self.parent.prevForm})
        self.popup.add_handlers({curses.KEY_F2: self.parent.nextForm})
        self.popup.add_handlers({curses.KEY_F4: self.parent.openNewsView})

        self.select = self.popup.add_widget(npyscreen.MultiLineAction, relx=2, rely=2,
                                            max_height=self.max_y - 8, height=self.max_y-8, values=[],
                                            width=13, max_width=13, color="DEFAULT", widgets_inherit_color=True)

        self.box = self.popup.add_widget(npyscreen.Pager, values="", relx=15, rely=4, hidden=1,
                                         width=self.max_x - 22, max_width=self.max_x - 22, editable=0,
                                         color="CURSOR", widgets_inherit_color=True, autowrap=True)
        self.select.actionSelected = self.nickSelected
        self.select.actionHighlighted = self.nickSelected

        self.prev = self.popup.add(npyscreen.ButtonPress, relx=13, rely=2, name="<<", hidden=1)
        self.prev.add_handlers({curses.ascii.NL: self.prevPressed})
        self.next = self.popup.add(npyscreen.MiniButton, relx=18, rely=2, name=">>", hidden=1)
        self.next.add_handlers({curses.ascii.NL: self.nextPressed})
        self.msgnav = self.popup.add_widget(npyscreen.FixedText, name="msgnav", editable=0, relx=24, rely=2,
                                            value="", color="NO_EDIT", hidden=1)

        self.reply = self.popup.add(npyscreen.MiniButton, relx=self.max_x-23, rely=2, name="Reply", hidden=1)
        self.reply.add_handlers({curses.ascii.NL: self.replyPressed})

        self.clear = self.popup.add(npyscreen.MiniButton, relx=self.max_x-15, rely=2, name="Clear", hidden=1)
        self.clear.add_handlers({curses.ascii.NL: self.clearPressed})
        self.msgheader = self.popup.add_widget(npyscreen.FixedText, name="msgheader", editable=0, relx=15, rely=3,
                                               value="", color="CAUTION", hidden=1)
        self.cancel = self.popup.add(npyscreen.ButtonPress, relx=2, rely=self.max_y-6, name="Close")

        self.cancel.whenPressed = self.close
        self.updateSidebar()
        if not len(self.msgs):
            self.popup.editw = 8
        return self.popup

    def updateSidebar(self):
        self.select.values = []
        self.select.update()
        for auserid in self.msguserids:
            if not auserid in self.nicks:
                continue
            self.select.values.append(self.nicks[auserid])
        self.select.display()
        return

    def nickSelected(self, nick, *args):
        self.displayMsgs(nick)

    def clearPressed(self, *args, **kwargs):
        userid = self.displayUid
        if not userid in self.msgs:
            return 0
        msgid = self.displayMsg
        try:
            msg = self.msgs[userid][msgid]
        except IndexError:
            return 0
        index = (len(self.msgs[userid])-1) - msgid  # we display the messages in reverse - delete reversed too
        del(self.msgs[userid][index])
        if not len(self.msgs[userid]):
            del(self.msgs[userid])
            nick = self.nicks[userid]
            del(self.nicks[userid])
            for i in range(0, len(self.msguserids)):
                if self.msguserids[i] == userid:
                    self.msguserids.pop(i)
                    break
            self.displayMsg = 0
            self.displayUid = 0
            self.toggleWidgets(1)
            self.updateSidebar()
            return 1
        self.displayMsgs(self.nicks[self.displayUid])

    def displayMsgs(self, nick):
        userid = self.getIdByNick(nick)
        if not userid in self.msgs:
            return 0
        msgcount = len(self.msgs[userid])
        if self.displayUid == userid:
            display = self.displayMsg
        else:
            self.displayUid = userid
            self.displayMsg = 0
            display = 0
        if display > msgcount:
            self.displayMsg = msgcount - 1
            display = msgcount - 1
        try:
            msgs = list(reversed(self.msgs[userid]))
            msg = msgs[display]
            del(msgs)
        except IndexError:
            return 0
        self.msgnav.value = "%s messages (%s/%s)" % (nick, display+1, msgcount)
        self.box.values = [msg.text]
        received = datetime.fromtimestamp(msg.date)
        received = received.strftime("%Y-%m-%d %H:%M")
        if not msg.read:
            read = "New Message"
            msg.read = time()
            self.parent.removeNotification('MSG', 1, userid)
        else:
            read = datetime.fromtimestamp(msg.read)
            read = read.strftime("%Y-%m-%d %H:%M")
        self.msgheader.value = "received: %s - read: %s" % (received, read)

        self.prev.editable = 0
        if display > 0:
            self.prev.editable = 1

        self.next.editable = 0
        if display < msgcount - 1:
            self.next.editable = 1

        self.toggleWidgets(0)

    def toggleWidgets(self, state):
        if not self.msgnav.hidden == state:
            self.msgnav.hidden = state
        self.msgnav.update()

        if not self.msgheader.hidden == state:
            self.msgheader.hidden = state
        self.msgheader.update()

        if not self.box.hidden == state:
            self.box.hidden = state
        self.box.display()

        if not self.reply.hidden == state:
            self.reply.hidden = state
        self.reply.update()

        if not self.clear.hidden == state:
            self.clear.hidden = state
        self.clear.update()

        if not self.next.hidden == state:
            self.next.hidden = state
        self.next.update()

        if not self.prev.hidden == state:
            self.prev.hidden = state
        self.prev.update()
        return

    def getIdByNick(self, nick):
        for aid, anick in self.nicks.items():
            if nick == anick:
                return aid
        return 0

    def nextPressed(self, *args, **kwargs):
        self.displayMsg += 1
        self.displayMsgs(self.nicks[self.displayUid])

    def prevPressed(self, *args, **kwargs):
        if self.displayMsg:
            self.displayMsg -= 1
            self.displayMsgs(self.nicks[self.displayUid])

    def replyPressed(self, *args, **kwargs):
        message = rewireFunctions.composeMessage(self.displayUid)
        if message:
            if not self.parent.sendPrivateMessage(self.displayUid, message):
                pass  # show error here
        return

    def close(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
        self.parent.msgview = 0


class rewireMsg():
    def __init__(self, userid, nick, date, text):
        self.userid = userid
        self.nick = nick
        self.date = date
        self.text = text
        self.read = 0
