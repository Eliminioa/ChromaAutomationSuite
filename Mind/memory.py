import json
import sqlite3

from Utilities import CASexcepts as excs

HOME_DIRECTORY = '/home/jboggs/Documents/Coding/ChromaAutomationSuite'

"""Just some functions to help with database and group access/management."""

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
    else:
        learn_new_player(db, username, **kwargs)
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
                db.execute('update players set {} = ? where username = ?'.format(attrib), (value, username))
            except KeyError:
                raise excs.UserAttribError(__name__, attrib, username)
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
        side = '-2'

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
    db.execute('insert or replace into players (username, side, recruited, usertype, accessInfo)' +
               'values (?, ?, ?, ?, ?)', (username, side, recruited, usertype, accessInfo))
    db.commit()
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
        return db.execute('select {} from players where username = ?'.format(attrib),
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
    except KeyError:
        raise excs.InvalidUserError(__name__, username)
    except:
        raise

# GROUP MANAGEMENT FUNCTIONS

# get group jsons for both sides
with open(HOME_DIRECTORY + '/Mind/groups.json', 'r') as gf:
    groups = json.load(gf)
OR_groups = groups['OR_groups']
PW_groups = groups['PW_groups']


def get_lists_of(side):
    """
    Returns the various lists of users the specified army has made.

    :param side: Which army's lists to retrieve
    :return: A list of the different lists an army has made (OR=0,PW=1)
    """
    if side == 0:
        return OR_groups
    elif side == 1:
        return PW_groups
    else:
        return {}


def add_player(side, list_name, player_name):
    """
    As the label says, adds a player to a list.

    :param side: Which army's list to modify (OR=0,PW=1)
    :param list_name: The name of the list to add to
    :param player_name: Name of the player to add
    :return: True if successful, false otherwise
    """
    if side == 0:
        if list_name not in OR_groups:
            return False
        OR_groups[list_name].append(player_name)
    elif side == 1:
        if list_name not in PW_groups:
            return False
        if player_name not in PW_groups[list_name]:
            PW_groups[list_name].append(player_name)
    else:
        return False
    save_groups()


def remove_player(side, list_name, player_name):
    """
    As the label says, adds a player to a list.

    :param side: Which army's list to modify (OR=0,PW=1)
    :param list_name: The name of the list to remove from to
    :param player_name: Name of the player to remove
    :return: True if successful, false otherwise
    """
    if side == 0:
        if list_name not in OR_groups:
            return False
        OR_groups[list_name].remove(player_name)
    elif side == 1:
        if list_name not in PW_groups:
            return False
        if player_name in PW_groups[list_name]:
            PW_groups[list_name].remove(player_name)
    else:
        return False
    save_groups()
    return True


def create_list(side, list_name):
    """
    Creates a new list with the given name

    :param side: Which army to make the list for (OR=0, PW=1)
    :param list_name: Name of the new list
    :return: True if successful, false otherwise
    """
    if side == 0:
        if list_name in OR_groups:
            return False
        OR_groups[list_name] = []
    elif side == 1:
        if list_name in PW_groups:
            return False
        PW_groups[list_name] = []
    else:
        return False
    save_groups()
    return True


def save_groups():
    groups = {'OR_groups':OR_groups,
              'PW_groups':PW_groups}
    with open(HOME_DIRECTORY + '/Mind/groups.json', 'w') as gf:
        json.dump(groups, gf)
