import npyscreen
import curses
from includes import rewiredInstance


class NewConnection(npyscreen.FormBaseNew):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.formid = "MAIN"
        super(NewConnection, self).__init__(**kwargs)
        self.add_handlers({"^D": self.exit_application})
        self.add_handlers({"^Q": self.exit_application})
        self.add_handlers({"^T": self.parent.switchNextForm})

    def create(self):
        start_x = int(round((self.max_x - 36) / 2))
        start_y = int(round((self.max_y - 5) / 2))
        self.name = "re:wire new connection"
        self.server = self.add(npyscreen.TitleText, relx=start_x, rely=start_y,
                               name="Server:      ", value="re-wired.info", field_width=20, begin_entry_at=16)
        self.server.handlers[curses.KEY_BACKSPACE] = self.server.entry_widget.h_delete_left
        self.user = self.add(npyscreen.TitleText, relx=start_x, rely=start_y+1,
                             name="Username:", value="guest", field_width=20, begin_entry_at=16)
        self.user.handlers[curses.KEY_BACKSPACE] = self.user.entry_widget.h_delete_left
        self.password = self.add(npyscreen.TitlePassword, relx=start_x, rely=start_y+2,
                                 name="Password: ", value="", field_width=20, begin_entry_at=16)
        self.password.handlers[curses.KEY_BACKSPACE] = self.password.entry_widget.h_delete_left
        self.reconnect = self.add(npyscreen.Checkbox, relx=start_x, rely=start_y+3,
                                  name="Reconnect automatically")
        self.connect = self.add(npyscreen.MiniButton, relx=start_x+6, rely=start_y+4,
                                name="Connect")
        self.quit = self.add(npyscreen.MiniButton, relx=start_x+16, rely=start_y+4, name="Quit")
        self.quit.add_handlers({curses.ascii.NL: self.exit_application})
        self.connect.add_handlers({curses.ascii.NL: self.doConnect})

    def exit_application(self, *args):
        self.parent.shutdown()
        curses.beep()
        self.parentApp.setNextForm(None)
        self.editing = False
        raise SystemExit

    def backspace(self, *args):
        curses.beep()

    def doConnect(self, *args):
        if not self.server.value:
            self.server.edit()
            return 0
        server = self.server.value
        port = 2000
        if ':' in server:
            server, port = server.split(':', 1)
            try:
                port = int(port)
            except:
                self.server.edit()
                return 0
        if not self.user.value:
            self.user.edit()
            return 0
        user = self.user.value
        password = self.password.value
        autoreconnect = int(self.reconnect.value)
        conID = self.parent.conID
        self.parent.conID += 1
        self.parent.servers[conID] = rewiredInstance.rewiredInstance(self.parent,
                                                                     conID, server, port, user, password, autoreconnect)
        if self.parent.servers[conID].fail:
            if self.parent.servers[conID].fail == 1:
                npyscreen.notify_confirm("Failed to connect to %s" % server, "Failed to connect")
            if self.parent.servers[conID].fail == 2:
                npyscreen.notify_confirm("Login Failed", "Login Failed")
            self.parent.servers[conID].librewired.keepalive = 0
            del(self.parent.servers[conID])
            return 0
        form = "%s-CHAT1" % (conID)
        self.parent.servers[conID].forms.append(form)
        self.parent.registerForm(form, self.parent.servers[conID].chats[1])
        self.parent.switchForm(form)
