import npyscreen
import curses


class autocompleter(npyscreen.Autocomplete):

    def hookParent(self, parent):
        self.parent = parent
        self.lastcomplete = 0
        self.laststr = 0

    def backspace(self, *args):
        self.lastcomplete = 0
        self.laststr = 0
        if len(self.value):
            self.value = self.value[:len(self.value)-1]
            self.update()

    def auto_complete(self, input):
        self.options = self.parent.validCommands + self.parent.userlist.yieldnicks()
        if not len(self.value):
            curses.beep()
            return 0
        if self.lastcomplete == self.value and self.laststr:
            search = self.laststr
        else:
            search = self.value
        results = []
        for aoption in self.options:
            if aoption[:len(search)].upper() == search.upper():
                results.append(aoption)
        if not results:
            curses.beep()
            return 0
        if not self.lastcomplete:
            self.laststr = self.value
        index = 0
        if self.lastcomplete and self.laststr:
            try:
                pos = results.index(self.lastcomplete)
            except ValueError:
                return 0
            if pos < len(results):
                index = pos + 1
        try:
            results[index]
        except IndexError:
            index = 0
        self.value = ""
        self.display()
        self.value = results[index]
        if len(results) == 1 and not "/" in self.value[:1]:
            self.value += ": "
        self.cursor_position += len(self.value)
        self.update()
        self.lastcomplete = results[index]
        return 1
