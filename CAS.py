from os import path

import sqlite3
from flask import Flask, g, render_template, request, redirect, session, url_for

from Utilities import loggingSetup, connector
from Mind import memory

CAS = Flask(__name__, template_folder='Body/Chassis')
CAS.config.from_pyfile('CASConfig.cfg')
CAS.debug = True
ANTENNA = connector.Connector(CAS.config)


# DB METHODS
@CAS.before_request
def request_initialization():
    g.consciousness = get_consciousness().cursor()


@CAS.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def init_db():
    """Initializes the database."""
    db = connect_db()
    with CAS.open_resource('Mind/subconscious.sql') as f:
        db.cursor().executescript(f.read())
    db.commit()


def connect_db():
    """Connects to the database."""
    return sqlite3.connect(CAS.config['DATABASE'])


def get_consciousness():
    """Opens a new database connection."""
    if not hasattr(g, 'consciousness'):
        g.db = connect_db()
    return g.db


# ROUTING METHODS
@CAS.route('/')
def home_page():
    # tells the session the bot is online. Might actually make this useful
    # at some point.
    session['status'] = 'ONLINE'

    # get the name of the list being managed, if any
    listname = request.args.get('listview')
    listname = (listname if listname!=None else 'all')

    # checks if a new list has been created
    if request.args.get('new_name') is not None:
        new_list_name = request.args.get('new_name')
        listname=new_list_name
        memory.create_list(session['side'], listname)

    # if a player was removed, deal with that
    if request.args.get('remove') is not None:
        removed_player = request.args.get('remove')
        memory.remove_player(session['side'], listname, removed_player)

    # if a player was added, deal with that
    if request.args.get('add') is not None:
        added_player = request.args.get('add')
        memory.add_player(session['side'], listname, added_player)

    # set template variables
    logged_in = session['logged_in']
    if logged_in:
        groups = memory.get_lists_of(session['side'])
        try:
            listview = groups[listname]
        except KeyError:
            listview = ['There\'s nothing here!']
        try:
            majors = memory.get_players_with(g.db, side=session['side'])
        except sqlite3.InterfaceError:
            majors = []


    # finally, render the page
    if logged_in:
        return render_template("HomePage.html",
                               groups=groups,
                               listname=listname,
                               listview=listview,
                               majors=majors)
    else:
        return render_template("HomePage.html",
                               groups=None,
                               listname=None,
                               listview=None,
                               majors=None)

@CAS.route('/AboutPage')
def about_page():
    return render_template("AboutPage.html")


@CAS.route('/ContactPage')
def contact_page():
    return render_template("ContactPage.html")


@CAS.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    return redirect(ANTENNA.get_OAuth_URL('player'))

@CAS.route('/sign-out', methods=['GET','POST'])
def sign_out():
    session["logged_in"] = False
    return redirect('/')


@CAS.route('/authorize_callback')
def authorize_user():
    #get authorization
    OAuth_code = request.args.get('code')
    access_info = ANTENNA.connect_to_reddit(OAuth_code)

    #establish player in DB
    username = ANTENNA.account_info.name
    memory.handle_player_memory(g.db, username, accessToken=access_info['access_token'])

    #handle session info
    session["username"] = username
    session["usertype"] = 'Mod'
    session["logged_in"] = True
    session["side"] = memory.get_attrib_of_player(g.db, username, 'side')
    return redirect('/')

if __name__ == '__main__':
    init_db()
    CAS.run(host='127.0.0.1')
