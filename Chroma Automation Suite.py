from contextlib import closing

import sqlite3
from flask import Flask, g, render_template, request, redirect

from Utilities import loggingSetup, connector

CAS = Flask(__name__)
CAS.config.from_pyfile('Config/CASConfig.cfg')
CAS.debug = True
ANTENNA = connector.antenna


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


@CAS.route('/sign_in')
def sign_in():
    return redirect(ANTENNA.get_OAuth_URL('player'))


@CAS.route('/authorize_callback')
def authorize_user():
    print request.args.get('code')


# DB METHODS
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


if __name__ == '__main__':
    CAS.run(host='0.0.0.0')
