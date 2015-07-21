from contextlib import closing

import sqlite3
from flask import Flask, g, render_template, request, redirect

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
    with closing(connect_db()) as db:
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
    return render_template("HomePage.html")


@CAS.route('/AboutPage')
def about_page():
    return render_template("AboutPage.html")


@CAS.route('/ContactPage')
def contact_page():
    return render_template("ContactPage.html")


@CAS.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    return redirect(ANTENNA.get_OAuth_URL('player'))


@CAS.route('/authorize_callback')
def authorize_user():
    OAuth_code = request.args.get('code')
    access_info = ANTENNA.connect_to_reddit(OAuth_code)
    username = ANTENNA.account_info
    g.db
    return render_template("HomePage.html")

if __name__ == '__main__':
    CAS.run(host='127.0.0.1')
