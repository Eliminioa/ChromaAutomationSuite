import os
import re
from pickle import dumps
from multiprocessing import Process
import sqlite3

from flask import Flask, g, render_template, request, redirect, session

from Body import botIO
from Mind import memory
from Utilities.loggingSetup import create_logger
from Utilities import CASexcepts as excs
from Utilities import configReader


# Global vars
CAS = Flask(__name__, template_folder='Chassis')
SECRET_KEY = os.environ.get('SECRETKEY')
CAS.debug = True
CONFIG = {}
ANTENNA = None
NERVES = None
LOG = create_logger(__name__)
LOCK = None


@CAS.before_request
def get_DB():
    LOCK.acquire()
    db = getattr(g, 'db', None)
    if db is None:
        LOG.debug('Connected database to globals!')
        g.db = sqlite3.connect(CONFIG['DATABASE'])


@CAS.after_request
def commit_DB(response):
    g.db.commit()
    g.db.close()
    LOG.debug('Committed changes to DB!')
    LOCK.release()
    return response

# TODO Make a teardown function that gracefully deals with unforeseen errors

# ROUTING METHODS
# noinspection PyUnresolvedReferences,PyUnresolvedReferences
@CAS.route('/')
def home_page():
    # tells the session the bot is online. Might actually make this useful
    # at some point.
    if NERVES.poll():
        signal = NERVES.recv()
        session['status'] = signal
    elif 'status' not in session:
        session['status'] = 'OFFLINE'

    if not session.has_key('logged_in') or not session['logged_in']:
        LOG.debug('Not logged in, displaying standard home page')
        return render_template('HomePage.html',
            groups=None,
            listname=None,
            listview=None,
            majors=None)

    # if the session has an invalid side,
    if not session.has_key('side') or session['side'] < 0:
        session['side'] = 1

    # get the name of the list being managed, if any
    listname = request.args.get('listview')
    listname = (listname if listname is not None else 'all')
    if listname:
        LOG.debug("Listname = {}".format(listname))

    # checks if a new list has been created
    if request.args.get('new_name') is not None:

        new_list_name = request.args.get('new_name')
        listname=new_list_name
        memory.create_list(session['side'], listname)
        LOG.debug('Added a new list {} to memory for side {}'.format(
            listname, session['side']))

    # if a player was removed, deal with that
    if request.args.get('remove') is not None:
        removed_player = request.args.get('remove')
        memory.remove_player(session['side'], listname, removed_player)
        LOG.debug('Removed {} from list {} of side {}'.format(
            removed_player, listname, session['side']))

    # if a player was added, deal with that
    if request.args.get('add') is not None:
        added_player = request.args.get('add')
        memory.add_player(session['side'], listname, added_player)
        LOG.debug('Added {} to list {} for side {}'.format(
            added_player, listname, session['side']))

    groups = memory.get_lists_of(session['side'])
    LOG.debug('Groups for side {} are {}'.format(session['side'], groups))
    try:
         listview = groups[listname]
         LOG.debug('Users in group {}: {}'.format(listname, listview))
    except KeyError:
        listview = ['There\'s nothing here!']
    try:
        majors = memory.get_players_with(g.db, side=session['side'], recruited=True)
    except sqlite3.InterfaceError:
        majors = []

    return render_template('HomePage.html',
                               groups=groups,
                               listname=listname,
                               listview=listview,
                               majors=majors,
                               version=CONFIG['VERSION'])


# noinspection PyUnresolvedReferences
@CAS.route('/AboutPage')
def about_page():
    LOG.debug('Rendering About Page')
    return render_template("AboutPage.html")


# noinspection PyUnresolvedReferences
@CAS.route('/ContactPage')
def contact_page():
    LOG.debug('Rendering Contact Page')
    return render_template("ContactPage.html")


@CAS.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    LOG.debug('Signing a user in')
    return redirect(ANTENNA.get_OAuth_URL('player'))


@CAS.route('/sign-out', methods=['GET','POST'])
def sign_out():
    LOG.info('{} is signing out'.format(session['username']))
    session["logged_in"] = False
    return redirect('/')


@CAS.route('/authorize_callback')
def authorize_user():
    #get authorization
    OAuth_code = request.args.get('code')
    access_info = ANTENNA.connect_to_reddit(OAuth_code)

    #establish player in DB
    username = ANTENNA.account_info.name
    memory.handle_player_memory(g.db, username, accessInfo=dumps(access_info))
    LOG.info("Received OAuth for {}".format(username))

    #handle session info
    if memory.get_attrib_of_player(g.db, username, 'usertype') == -1:
        return redirect('/')
    session["usertype"] = memory.get_attrib_of_player(g.db,
                                                      username,
                                                      'usertype')
    session["username"] = username
    session["logged_in"] = True
    session["side"] = memory.get_attrib_of_player(g.db, username, 'side')
    return redirect('/')


@CAS.route('/auth_bot')
def authorize_bot():
    """
    Allow me to authorize a bot
    """

    # make sure no one else can do it
    if session['usertype'] != 2:
        return redirect('/')
    bot_name = request.args.get('bot_name')
    bot_side = int(request.args.get('bot_side'))
    LOG.debug("Attempting to authorize {} bot for side {}".format(bot_name,
                                                                  bot_side))
    if len(memory.get_players_with(g.db, side=bot_side, usertype=-1)) > 0:
        LOG.warning("{} is already registered with side {}!".format(bot_name,
                                                                    bot_side))
        LOG.warning("List returned by memory: {}".format(
            memory.get_players_with(g.db,
                                    side=bot_side,
                                    usertype=-1).__str__()))
        return redirect('/')
    memory.handle_player_memory(g.db, bot_name, side=bot_side, usertype=-1)
    LOG.info("Authorized {} bot for side {}".format(bot_name, bot_side))
    return redirect(ANTENNA.get_OAuth_URL('bot'))


@CAS.route('/reset_bots')
def reset_bots():
    """
    Lets me destroy the bots in the DB so I can reauthorize them.
    """
    # make sure no one else can do it
    if session['usertype'] != 2:
        return redirect('/')
    bot_list = memory.get_players_with(g.db, usertype=-1)
    for bot in bot_list:
        memory.remove_player_from_DB(g.db, bot)
    return redirect('/')


@CAS.route('/run_bot')
def run_bots():
    """
    Start the bots running
    """
    # make sure no one else can do it
    if session['usertype'] != 2:
        return redirect('/')
    NERVES.send('THINK')
    LOG.debug("Sent signal to run bots")
    return redirect('/')


@CAS.route('/reset_groups')
def reset_groups():
    """
    Clear both sides' groups to default."
    """
    if session['usertype'] != 2:
        return redirect('/')
    memory.clear_groups()
    LOG.debug('Cleared groups')
    return redirect('/')


@CAS.route('/change_side')
def change_side():
    """
    Change the effective side of myself, so I can test both sides.
    """
    if session['usertype'] != 2:
        return redirect('/')
    session['side'] = abs(1-session['side'])
    LOG.debug("Changed side to {}".format(session['side']))
    return redirect('/')


@CAS.route('/set_thread')
def set_thread():
    """
    Set the recruitment thread of a side.
    """
    if session['usertype'] == 0:
        return redirect('/')
    thread_link = request.args.get('link')
    thread_side = int(request.args.get('side'))
    thread_id = re.search("(?<=/)([1-z]{6})(?=/)", thread_link).group(0)
    if thread_side == 0:
        CONFIG["OR_RECRUIT_THREAD"] = thread_id
    elif thread_side == 1:
        CONFIG["PW_RECRUIT_THREAD"] = thread_id
    else:
        raise excs.InvalidSideError(__name__, thread_side)
    configReader.save(CONFIG)
    return redirect('/')


@CAS.route('/send_message', methods=['POST'])
def send_message():
    """
    Send message from the side's bot.
    """
    subject = request.form['subject']
    content = request.form['content']
    list = request.form['list']
    try:
        recipients = memory.get_lists_of(session['side'])[list]
    except:
        recipients = memory.get_lists_of(session['side'])['all']
    bot_name = 'Periwinkle_Prime_3' if session['side']==1 else 'Orangered_HQ'
    botIO.send_message(ANTENNA, subject, content, recipients, bot_name)
    return redirect('/')

class Body(Process):
    """
    The process which will run the Chroma Automation Suite's interactions
    with the rest of the world. This is most of the stuff people will see.
    """
    def __init__(self, name, config, antenna, nerves, lock):
        Process.__init__(self)
        self.name = name
        self.daemon = True
        global CONFIG
        CONFIG = config
        global ANTENNA
        ANTENNA = antenna
        global NERVES
        NERVES = nerves
        global LOCK
        LOCK = lock

    def run(self):
        print("BODY PID: {}".format(self.pid))
        CAS.run(host='127.0.0.1', port=5000, use_reloader=False)