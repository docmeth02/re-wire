import npyscreen
import curses
from includes import rewireFunctions
from includes import userinfoView
from threading import Timer


class transferview():
    def __init__(self, parent, formid):
        self.parent = parent
        self.formid = formid
        self.librewired = self.parent.librewired
        self.max_x = self.parent.max_x
        self.max_y = self.parent.max_y
        self.transfers = []
        self.refreshtimer = 0

    def build(self):
        self.popup = npyscreen.FormMultiPage(name="%s Transfers" % self.parent.host,
                                             framed=True, relx=0, rely=0, lines=self.max_y - 3,
                                             columns=self.max_x - 2)
        self.popup.on_ok = self.close
        self.popup.formid = self.formid
        self.popup.show_atx = 1
        self.popup.show_aty = 1
        self.popup.beforeEditing = self.beforeEditing
        self.popup.afterEditing = self.afterEditing

        self.popup.add_handlers({curses.KEY_F1: self.parent.prevForm})
        self.popup.add_handlers({curses.KEY_F2: self.parent.nextForm})
        self.popup.add_handlers({curses.KEY_F3: self.parent.openMessageView})
        self.popup.add_handlers({curses.KEY_F4: self.parent.openNewsView})
        self.popup.add_handlers({curses.KEY_F5: self.parent.openFileView})
        self.popup.add_handlers({curses.KEY_F6: self.close})
        self.popup.add_handlers({'^D': self.close})

        i, pos = (0, 1)
        for transferobj in self.parent.transfers:
            trtype = ['Upload', 'Download']
            atransfer = transfergroupindicator(self, transferobj, i, 1, pos, self.popup.max_x-5, trtype[transferobj.type])
            atransfer.build()
            atransfer.refresh()
            atransfer.label.editable = 1
            atransfer.label.entry_widget.add_handlers({curses.ascii.NL: atransfer.transferSelected})
            atransfer.label.entry_widget.add_handlers({curses.ascii.SP: atransfer.transferSelected})
            self.transfers.append(atransfer)
            pos += 3
            i += 1
            if pos >= self.max_y - 5:
                self.popup.add_page()
                pos = 1

        self.closebutton = self.popup.add(npyscreen.ButtonPress, relx=2, rely=self.max_y-6, name="Close")
        self.closebutton.whenPressed = self.close
        self.popup.switch_page(0)
        return self.popup

    def refresh(self):
        for atransfer in self.transfers:
            atransfer.refresh()
            self.popup.display()
        if self.refreshtimer:
            self.refreshtimer = Timer(2, self.refresh)
            self.refreshtimer.start()

    def beforeEditing(self):
        if not self.refreshtimer:
            self.refreshtimer = Timer(2, self.refresh)
            self.refreshtimer.start()

    def afterEditing(self):
        if self.refreshtimer:
            self.refreshtimer.cancel()
            self.refreshtimer.join(1)
            self.refreshtimer = 0

    def transferSelected(self, wid):
        return 1
        options = ['Cancel', 'Start', 'Stop', 'Pause', 'Resume']
        menu = npyscreen.Popup(name="Select action:", framed=True, lines=len(options) + 4, columns=25)
        menu.show_atx = 2
        menu.show_aty = self.transfers[wid].rely
        selector = menu.add_widget(npyscreen.MultiLine, values=options, value=None, color="CURSOR",
                                   widgets_inherit_color=True,  slow_scroll=True, return_exit=True,
                                   select_exit=True, width=20)
        menu.display()
        action = selector.edit()
        if action:
            curses.beep()
        return 1

    def close(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
        self.parent.transferview = 0


class transfergroupindicator(userinfoView.transferIndicator):
    def __init__(self, parent, transfer, wid, relx, rely, width, label="Transfer:", filename="Null"):
        self.transferview = parent
        self.transferobj = transfer
        self.trtype = label
        self.wid = wid
        super(transfergroupindicator, self).__init__(parent.popup, relx, rely, width, label, filename)

    def transferSelected(self, *args, **kwargs):
        self.transferview.transferSelected(self.wid)

    def refresh(self):
        status = self.transferobj.status()
        active = self.transferobj.getActiveTransfer()
        if status['complete']:
            label = "Finished %s out of %s files" % (status['done'], status['totalfiles'])
            self.update(self.trtype, label, status['bytes'], status['bytesdone'], status['rate'])
            return 1
        if active:
            label = label = "(%s out of %s files) %s" % (status['done'], status['totalfiles'], active[0])
            self.update(self.trtype, label, status['bytes'], status['bytesdone'], active[1])
            return 1
        label = "Queued %s out of %s files" % (status['done'], status['totalfiles'])
        self.update(self.trtype, label, status['bytes'], status['bytesdone'], status['rate'])

        return 1
