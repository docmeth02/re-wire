from ConfigParser import ConfigParser
from os import path
import npyscreen


def load_config(fullpath, filename=False):
    config = ConfigParser()
    conffile = 'rewire.conf'
    if filename:
        conffile = filename
    if not path.exists(path.join(fullpath, conffile)):
        ## Create default config file
        config.add_section("defaults")
        config.set("defaults", 'server', 're-wired.info')
        config.set("defaults", 'port', '2000')
        config.set("defaults", 'user', 'guest')
        config.set("defaults", 'password', '')
        config.set("defaults", 'pwhash', '')
        config.set("defaults", 'autoreconnect', '0')
        config.set("defaults", 'nick', 're:wire')
        config.set("defaults", 'status', 'Another re:wire client')
        config.set("defaults", 'icon', 'data/default.png')
        config.set("defaults", 'connectonstart', '0')

        with open(path.join(fullpath, conffile), 'w') as newfile:
            config.write(newfile)
    else:
        try:
            config.read(path.join(fullpath, conffile))
        except Exception as e:
            return 0
    config.set("DEFAULT", 'server', 're-wired.info')
    config.set("DEFAULT", 'port', '2000')
    config.set("DEFAULT", 'user', 'guest')
    config.set("DEFAULT", 'password', '')
    config.set("DEFAULT", 'pwhash', '')
    config.set("DEFAULT", 'autoreconnect', '0')
    config.set("DEFAULT", 'nick', 're:wire')
    config.set("DEFAULT", 'status', 'Another re:wire client')
    config.set("DEFAULT", 'icon', 'data/default.png')
    config.set("DEFAULT", 'connectonstart', '0')
    return config


def on_ok():
    return 1


def on_cancel():
    return 0


def composeMessage(userid):
    reply = npyscreen.ActionPopup(name="Compose Message")
    reply.OK_BUTTON_TEXT = "Send"
    reply.on_ok = on_ok
    reply.on_cancel = on_cancel
    label = reply.add_widget(npyscreen.FixedText, value="Message text:", editable=0, rely=1)
    text = reply.add_widget(npyscreen.MultiLineEdit, name="Text:", value="", begin_entry_at=8, rely=2)
    action = reply.edit()
    if action and text.value:
        return text.value
    return 0


def textDialog(title, inputlabel="Enter text:", oklabel="OK"):
    form = npyscreen.ActionPopup(name=title)
    form.OK_BUTTON_TEXT = oklabel
    form.on_ok = on_ok
    form.on_cancel = on_cancel
    label = form.add_widget(npyscreen.FixedText, value=inputlabel, editable=0, rely=1)
    text = form.add_widget(npyscreen.MultiLineEdit, value="", begin_entry_at=8, rely=2)
    action = form.edit()
    if action and text.value:
        return text.value
    return action
