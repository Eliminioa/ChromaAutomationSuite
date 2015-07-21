from os import path

import sqlite3
from flask import Flask, g, render_template, request, redirect, session, url_for

from Utilities import loggingSetup, connector
from Mind import memory

CAS = Flask(__name__, template_folder='Body/Chassis')
CAS.config.from_pyfile('Config/CASConfig.cfg')
CAS.debug = True
ANTENNA = connector.Connector(CAS.config)


# DB METHODS
@CAS.before_request
def request_initialization():
    g.db = get_consciousness()


@CAS.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def init_db():
    """Initializes the database."""
    db = connect_db()
    with CAS.open_resource('Config/subconscious.sql') as f:
        db.cursor().executescript(f.read())
    db.commit()


def connect_db():
    """Connects to the database."""
    return sqlite3.connect(CAS.config['DATABASE'])


def get_consciousness():
    """Opens a new database connection."""
    if not hasattr(g, 'consciousness'):
        g.consciousness = connect_db()
    return g.consciousness


# ROUTING METHODS
@CAS.route('/')
def home_page():
    return render_template("HomePage.html",groups = CAS.config['GROUPS'])


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
    memory.handle_player_memory(g.db, username, access_info=access_info, usertype='Mod')

    #handle session info
    session["username"] = username
    session["usertype"] = 'Mod'
    session["logged_in"] = True

    return redirect('/')

if __name__ == '__main__':
    CAS.run(host='127.0.0.1')
