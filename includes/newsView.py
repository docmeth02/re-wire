import npyscreen
import curses
from includes import rewireFunctions
from time import strftime, localtime, time


class newsview():
    def __init__(self, parent, formid):
        self.parent = parent
        self.formid = formid
        self.value = False
        self.max_y = self.parent.max_y
        self.max_x = self.parent.max_x
        self.displayKey = 0

    def build(self):
        self.popup = npyscreen.FormBaseNew(name="News @%s" % self.parent.host, framed=True, relx=0, rely=0,
                                           lines=self.max_y - 3, columns=self.max_x - 4)
        self.popup.show_atx = 1
        self.popup.show_aty = 1
        self.popup.add_handlers({curses.KEY_F1: self.parent.prevForm})
        self.popup.add_handlers({curses.KEY_F2: self.parent.nextForm})
        self.popup.add_handlers({curses.KEY_F3: self.parent.openMessageView})
        self.popup.add_handlers({curses.KEY_F4: self.closeview})
        self.popup.add_handlers({curses.KEY_F5: self.parent.openFileView})
        self.popup.add_handlers({curses.KEY_F6: self.parent.openTransferView})
        self.box = self.popup.add_widget(npyscreen.Pager, values="", relx=2, rely=1, hidden=0, editable=1,
                                         width=self.max_x - 10, max_width=self.max_x - 10, color="CURSOR",
                                         height=self.max_y-7,  widgets_inherit_color=True, autowrap=True)
        self.close = self.popup.add(npyscreen.ButtonPress, relx=2, rely=self.max_y-6, name="Close")
        self.close.whenPressed = self.closeview
        if self.parent.librewired.privileges['postNews']:
            self.post = self.popup.add(npyscreen.ButtonPress, relx=10, rely=self.max_y-6, name="Post News")
            self.post.whenPressed = self.postNews
        if self.parent.librewired.privileges['clearNews']:
            self.clear = self.popup.add(npyscreen.ButtonPress, relx=22, rely=self.max_y-6, name="Clear News")
            self.clear.whenPressed = self.clearNews
        self.populate()
        self.popup.editw = 1
        return self.popup

    def populate(self):
        if not self.parent.librewired.newsdone:
            return 0
        self.box.values = []
        self.parent.removeNotification('NEWS', -1, -1)
        for anews in self.parent.librewired.news:
            #strftime("%m/%d/%Y %H:%M:%S", localtime(anews.date
            post = rewireFunctions.checkssWiredImage(anews.post)
            if not post:
                continue
            title = "From %s (%s ago):" % (anews.nick, rewireFunctions.formatTime(time() - anews.date))
            self.box.values.append(title)
            self.box.values.append(post)
            self.box.values.append("")
        self.box.display()

    def closeview(self, *args, **kwargs):
        self.editable = False
        self.editing = False
        self.parent.closeForm(self.formid)
        self.parent.newsview = 0

    def postNews(self, *args, **kwargs):
        news = rewireFunctions.textDialog("Post News", "Enter Post Text:", "Post")
        if news:
            if type(news) is str:
                if news.strip():
                    if not self.parent.librewired.privileges['postNews']:
                        npyscreen.notify_confirm("Not allowed to post news!", "Post News")
                        return 0
                    self.parent.librewired.postNews(news)
                    self.popup.editw = 1
                    return 1
                npyscreen.notify_confirm("Can't post empty news!", "Post News")
            return 0
        return 0

    def clearNews(self, *args, **kwargs):
        action = npyscreen.notify_ok_cancel("Are you sure you want to clear the news?", "Clear news")
        if action:
            if not self.parent.librewired.privileges['clearNews']:
                npyscreen.notify_confirm("Not allowed to clear news!", "Clear News")
                return 0
            self.parent.librewired.clearNews()
            self.box.values = []
            self.box.display()
            self.populate()
            return 1
        return 0
