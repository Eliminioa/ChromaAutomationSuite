"""Just some functions to help with database and group access/management."""

import json
import sqlite3

from Utilities import CASexcepts as excs
from Utilities.loggingSetup import create_logger

HOME_DIRECTORY = '/home/jboggs/Documents/Coding/ChromaAutomationSuite'
LOG = create_logger(__name__)

# DATABASE FUNCTIONS

def handle_player_memory(db, username, **kwargs):
    """
    Takes accessinfo for a player, decides if it already knows the player,
    then sends the info to the appropriate helping function.

    :type db: sqlite3.Connection
    :param db: Database object to use
    :param username: username of the player
    :param kwargs: the info about the player to handle
    :return: True if a new player
    """

    player_names = db.execute('select username from players').fetchall()
    if username in [name[0] for name in player_names]:
        update_player_knowledge(db, username, **kwargs)
        LOG.debug("Handled updating player {}".format(username))
    else:
        learn_new_player(db, username, **kwargs)
        LOG.debug("Handled new player {}".format(username))
        return True
    return False


def update_player_knowledge(db, username, **kwargs):
    """
    Updates the bot's knowledge of a player

    :param db: Database object to use
    :param username: username of the player
    :param kwargs: the info about the player to update
    :return: The number of attributes updated
    """
    #for every kwarg passed, update that info in the database
    errors = []
    if kwargs is not None:
        for attrib, value in kwargs.iteritems():
            try:
                db.execute(
                    'update players set {} = ? where username = ?'.format(
                        attrib),
                    (value, username))
            except KeyError:
                raise excs.UserAttribError(__name__, attrib, username)
            LOG.debug("Updated {} of {} to {}".format(attrib, username, value))
    db.commit()
    return len(kwargs), errors


def learn_new_player(db, username, **kwargs):
    """
    Informs the bot about a new player.

    :param db: Database object to use
    :param username: username of new player
    :param kwargs: info known about player
    :return: True if successful
    """
    #fill in all the values
    attribs = kwargs.keys()
    if 'side' in attribs:
        side = kwargs['side']
    else:
        side = '1'

    if 'recruited' in attribs:
        recruited = kwargs['recruited']
    else:
        recruited = False

    if 'usertype' in attribs:
        usertype = kwargs['usertype']
    else:
        usertype = ''

    if 'accessInfo' in attribs:
        accessInfo = kwargs['accessInfo']
    else:
        accessInfo = ''
    #remember the player
    db.execute('insert or replace into players ('
               'username, side, recruited, usertype, accessInfo)' +
               'values (?, ?, ?, ?, ?)', (username, side, recruited,
                                          usertype, accessInfo))
    db.commit()
    LOG.debug("Added {} to side {} with usertype {}".format(username,
                                                            side, usertype))
    return True

def get_players_with(db, **kwargs):
    """
    Retrieves all the players in the database with the given attributes

    :param db: Database to look at
    :param kwargs: attributes the players should have
    :return: a list of players matching the search
    """
    # find the lists of players that match each value. So put every user
    # with the given username in one list, every user with the given side
    # in a second, etc. Then intersect the lists to give the final result.
    # This is done since you can't wildcard values through the ? parameter,
    # and maybe could be done faster (but not safer) through string
    # construction.
    attribs = kwargs.keys()
    if 'username' in attribs:
        username = kwargs['username']
        by_user = db.execute ('select username from players where username = ?',
                              [username]).fetchall()
        by_user =set([user[0] for user in by_user])
    else:
        by_user = None

    if 'side' in attribs:
        side = kwargs['side']
        by_side = db.execute ('select username from players where side = ?',
                              [side]).fetchall()
        by_side = set([user[0] for user in by_side])
    else:
        by_side = None

    if 'recruited' in attribs:
        recruited = kwargs['recruited']
        by_recr = db.execute ('select username from players where recruited = ?',
                              [recruited]).fetchall()
        by_recr = set([user[0] for user in by_recr])
    else:
        by_recr = None

    if 'usertype' in attribs:
        usertype = kwargs['usertype']
        by_type = db.execute ('select username from players where usertype = ?',
                              [usertype]).fetchall()
        by_type = set([user[0] for user in by_type])
    else:
        by_type = None

    # intersect lists and return players
    query_result = set()
    if by_user is not None:
        query_result = query_result.union(by_user)
    if by_side is not None:
        query_result = query_result.union(by_side)
    if by_recr is not None:
        query_result = query_result.union(by_recr)
    if by_type is not None:
        query_result = query_result.union(by_type)

    if by_user is not None:
        query_result = query_result.intersection(by_user)
    if by_side is not None:
        query_result = query_result.intersection(by_side)
    if by_recr is not None:
        query_result = query_result.intersection(by_recr)
    if by_type is not None:
        query_result = query_result.intersection(by_type)
    LOG.debug('Results for search {}\n{}'.format(kwargs, query_result))
    return query_result

def get_attrib_of_player(db, username, attrib):
    """
    Gets the specified attribute of the specified player from the DB

    :param db: DB to look in
    :param username: Name of target user
    :param attrib: Attribute to find
    :return: the attribute, or 'error'
    """
    try:
        return db.execute(
            'select {} from players where username = ?'.format(attrib),
            [username]).fetchone()[0]
    except:
        raise excs.UserAttribError(__name__, attrib, username)


def remove_player_from_DB(db, username):
    """
    Removes the record of a player from the database

    :param db: Database to remove from
    :param username: User to remove
    :return: True if successful
    """
    try:
        db.execute('delete from players where username=?', [username])
        LOG.debug("Removed {} from database".format(username))
    except KeyError:
        raise excs.InvalidUserError(__name__, username)
    except:
        raise

# GROUP MANAGEMENT FUNCTIONS

OR_GROUPS = {}
PW_GROUPS = {}

def refresh_groups(funct):
    def new_funct(*args, **kwargs):
        # get group jsons for both sides
        with open(HOME_DIRECTORY + '/Mind/groups.json', 'r') as gf:
            groups = json.load(gf)
        global OR_GROUPS
        OR_GROUPS = groups['OR_groups']
        global PW_GROUPS
        PW_GROUPS = groups['PW_groups']
        return funct(*args, **kwargs)
    return new_funct

def save_groups(funct):
    def new_funct(*args, **kwargs):
        tmp_OR_GROUPS, tmp_PW_GROUPS = funct(*args, **kwargs)
        global OR_GROUPS
        global PW_GROUPS
        OR_GROUPS = tmp_OR_GROUPS
        PW_GROUPS = tmp_PW_GROUPS
        groups = {'OR_groups': OR_GROUPS,
              'PW_groups': PW_GROUPS}
        with open(HOME_DIRECTORY + '/Mind/groups.json', 'w') as gf:
            json.dump(groups, gf)
        return tmp_OR_GROUPS, tmp_PW_GROUPS
    return new_funct



@refresh_groups
def get_lists_of(side):
    """
    Returns the various lists of users the specified army has made.

    :param side: Which army's lists to retrieve
    :return: A list of the different lists an army has made (OR=0,PW=1)
    """
    if side == 0:
        return OR_GROUPS
    elif side == 1:
        return PW_GROUPS
    else:
        raise excs.InvalidSideError(__name__, side)


@refresh_groups
@save_groups
def add_player(side, list_name, player_name):
    """
    As the label says, adds a player to a list.

    :param side: Which army's list to modify (OR=0,PW=1)
    :param list_name: The name of the list to add to
    :param player_name: Name of the player to add
    :return: Updated OR_ and PW_GROUPS
    """
    global PW_GROUPS
    global OR_GROUPS
    if side == 0:
        if list_name not in OR_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        OR_GROUPS[list_name].append(player_name)
    elif side == 1:
        if list_name not in PW_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        if player_name not in PW_GROUPS[list_name]:
            PW_GROUPS[list_name].append(player_name)
    else:
        raise excs.InvalidSideError(__name__, side)
    return OR_GROUPS, PW_GROUPS


@refresh_groups
@save_groups
def remove_player(side, list_name, player_name):
    """
    As the label says, adds a player to a list.

    :param side: Which army's list to modify (OR=0,PW=1)
    :param list_name: The name of the list to remove from to
    :param player_name: Name of the player to remove
    :return: Updated OR_ and PW_GROUPS
    """
    global PW_GROUPS
    global OR_GROUPS
    if side == 0:
        if list_name not in OR_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        OR_GROUPS[list_name].remove(player_name)
    elif side == 1:
        if list_name not in PW_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        if player_name in PW_GROUPS[list_name]:
            PW_GROUPS[list_name].remove(player_name)
    else:
        raise excs.InvalidSideError(__name__, side)
    return OR_GROUPS, PW_GROUPS


@refresh_groups
@save_groups
def create_list(side, list_name):
    """
    Creates a new list with the given name

    :param side: Which army to make the list for (OR=0, PW=1)
    :param list_name: Name of the new list
    :return: Updated OR_ and PW_GROUPS
    """
    global OR_GROUPS
    global PW_GROUPS
    if side == 0:
        if list_name in OR_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        OR_GROUPS[list_name] = []
    elif side == 1:
        if list_name in PW_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        PW_GROUPS[list_name] = []
    else:
        raise excs.InvalidSideError(__name__, side)
    return OR_GROUPS, PW_GROUPS


@refresh_groups
@save_groups
def update_list(side, list_name, users):
    """
    Update an existing user list with a list of users. This means add users
    who aren't in the existing list, remove users who aren't in the new list,
    and make sure a user is only on the list once.

    :param side: side of the target list
    :param list_name: name of the target list
    :param users: list of new users
    :return: Updated OR_ and PW_GROUPS
    """
    global PW_GROUPS
    global OR_GROUPS
    # get old list
    if side == 0:
        if list_name not in OR_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        old_list = OR_GROUPS[list_name]
    elif side == 1:
        if list_name not in PW_GROUPS:
            raise excs.InvalidListError(__name__, list_name, side)
        old_list = PW_GROUPS[list_name]
    else:
        raise excs.InvalidSideError(__name__, side)

    # add new users
    for user in users:
        if user not in old_list:
            old_list.append(user)

    # eliminate ones to be removed
    for user in old_list:
        if user not in users:
            while user in old_list:
                old_list.remove(user)

    # ensure each user appears only once
    new_list = list(set(old_list))

    #save new list
    if side == 0:
        OR_GROUPS[list_name] = new_list
    elif side == 1:
        PW_GROUPS[list_name] = new_list
    else:
        raise excs.InvalidSideError(__name__, side)
    return OR_GROUPS, PW_GROUPS

@save_groups
def clear_groups():
    """
    As labeled, clear all the groups, essentially reseting the groups.
    """
    global OR_GROUPS
    global PW_GROUPS
    OR_GROUPS = {'all': []}
    PW_GROUPS = {'all': []}
    return OR_GROUPS, PW_GROUPS