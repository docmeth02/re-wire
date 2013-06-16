import npyscreen
import curses
from includes import commandHandler, userList, autoCompleter


class chatview(npyscreen.FormBaseNew):
    def __init__(self, parent, formid, chatid, **kwargs):
        self.chat = chatid
        self.parent = parent
        self.formid = formid
        self.chattopic = 0
        self.librewired = self.parent.librewired
        self.validCommands = ['/nick', '/status', '/ping', '/icon', '/topic', '/me', '/clear']
        self.commandHandler = commandHandler.commandhandler(self, self.librewired)
        super(chatview, self).__init__(**kwargs)
        self.add_handlers({"^D": self.closeForm})
        self.add_handlers({"^T": self.parent.nextForm})

    def create(self):
        chat = "Public Chat"
        if self.chat != 1:
            chat = "Private Chat %s @s" % (self.chatid, self.parent.host)
        self.name = "re:wire @%s: %s " % (self.parent.host, chat)
        self.box = self.add(npyscreen.Pager, rely=1, relx=1, width=self.max_x - 18, height=self.max_y - 4,
                            max_width=self.max_x - 18, max_height=self.max_y - 5, editable=False)
        self.chatlabel = self.add(npyscreen.TitleText, name="Chat:", relx=1, rely=self.max_y - 4, editable=False)
        self.userlist = userList.userlist(self, self.max_x - 17, 1, 14, self.max_y - 5)
        self.topic = self.add(npyscreen.TitleText, name="Topic:", value="", begin_entry_at=9, hidden=1,
                              relx=1, rely=self.max_y - 3, editable=False, max_width=self.max_x - 20)
        self.chatinput = self.add(autoCompleter.autocompleter, relx=7, rely=self.max_y - 4,
                                  begin_entry_at=1, max_width=self.max_x - 15)
        self.chatinput.hookParent(self)
        self.chatinput.handlers[curses.ascii.NL] = self.chatinputenter
        self.chatinput.handlers[curses.KEY_BACKSPACE] = self.chatinput.backspace

    def deferred_update(self, instance, forced):
        if self.parent.getActiveForm() == self.formid:  # we're active right now
            if forced:
                instance.display()
            else:
                instance.update()
            return 1
        # since we are not the active form, there is no need to update the screen
        return 0

    def chatinputenter(self, *args):
        self.chatinput.lastcomplete = 0
        self.chatinput.laststr = 0
        chat = self.chatinput.value
        if chat:
            if not self.commandHandler.checkCommand(chat):
                self.parent.sendChat(self.chat, chat)
        self.chatinput.value = ""

    def focusInput(self, *args):
        self.chatinput.edit()

    def chatreceived(self, nick, chat, action):
        if action:
            self.appendChat("*** %s %s" % (str(nick), str(chat)))
        else:
            self.appendChat(str(chat), str(nick))

    def appendChat(self, chat, nick=False):
        length = len(chat)
        width = self.box.width
        if nick:
            length += len(nick)+2
        if length > width:
            if nick:
                lines = wrap(chat, width - (len(nick) + 2))
                for i in range(0, len(lines)):
                    if not i:
                        lines[i] = "%s: %s" % (nick, lines[i])
                    else:
                        spacing = " " * (len(nick) + 2)
                        lines[i] = spacing + lines[i]
            else:
                lines = wrap(chat, width)
        else:
            if nick:
                chat = "%s: %s" % (nick, chat)
            lines = [chat]
        for achat in lines:
            self.box.values += [achat]
        self.box.h_show_end("")
        self.deferred_update(self.box, True)

    def updateTopic(self, topic):
        self.topic.value = topic
        if not self.topic.value:
            self.topic.hidden = 1
        elif self.topic.hidden:
            self.topic.hidden = 0
        self.deferred_update(self.topic, True)
        return

    def closeForm(self, *args):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
