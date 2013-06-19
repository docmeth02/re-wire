re-wire
=======
re:wire - a python clone of zanka wire using lib:rewired

=======
Requirements: python > 2.6, npyscreen, python curses bindings

=======
Keyboard Shortcuts:
	F1		-	switch view to previous window
	F2		-	switch view to next window
	F3		-	open message view for parent windows server connection
	ctrl + d	-	disconnect from server
	tab key	-	autocomplete commands or nicknames in chat input field

=======
Config File:
    the default config file is called rewire.conf and will be loaded or created in the same directory the rewire app lives.

	[defaults]
	server = localhost			<-	server ip or fqd name
	port = 2000				<-	port to connect to
	user = guest				<-	your username
	password =				<-	your password in clear text
	pwhash =				<-	unused atm. will allow you to enter only your password hash
	autoreconnect = 0			<-	should re:wire reconnect atomatically
	nick = re:wire				<-	the nick re:wire should give itself upon connection
	status = Another re:wi...		<-	the default status (can be left blank)
	icon = data/default.png		<-	the default icon to load (can also be left blank)
	connectonstart = 0			<-	connect to this server as soon as re:wire starts

    The default entry in the config file does override the default server and client settings when you open rewire.
    Copy the default block and rename [defaults] to your servers name and edit the values accordingly to add your server to the bookmarks
