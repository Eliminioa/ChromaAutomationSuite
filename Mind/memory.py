import sqlite3

"""Just some functions to help with database access/management. You've
gotta pass the db object to each of these functions, but they don't
require anything else."""

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

    player_names = db.execute('select username from players')
    if username in player_names:
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
        try:
            for attrib, value in kwargs.iteritems():
                db.execute('update players set ? = ? where username = ?', (attrib, value, username))
        except KeyError as e:
            errors.append((e, 'Key error on {}'.format(attrib)))
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
        side = 'Unknown'

    if 'recruited' in attribs:
        recruited = kwargs['recruited']
    else:
        recruited = False

    if 'usertype' in attribs:
        usertype = kwargs['usertype']
    else:
        usertype = ''

    if 'accesstoken' in attribs:
        accesstoken = kwargs['accesstoken']
    else:
        accesstoken = ''
    #remember the player
    db.execute('insert into players (username, side, recruited, usertype, accesstoken)' +
               'values (?, ?, ?, ?, ?)', (username, side, recruited, usertype, accesstoken))
    return True

def get_players_with(db, **kwargs):
    #fill in all the values
    attribs = kwargs.keys()
    if 'username' in attribs:
        username = kwargs['username']
    else:
        username = '*'

    if 'side' in attribs:
        side = kwargs['side']
    else:
        side = '*'

    if 'recruited' in attribs:
        recruited = kwargs['recruited']
    else:
        recruited = '*'

    if 'usertype' in attribs:
        usertype = kwargs['usertype']
    else:
        usertype = '*'

    #get players
    query_response = db.execute('select * from players where '
                                'username = ? and side = ? and '
                                'recruited = ? and usertype = ?;', [username,
                                                                    side,
                                                                    recruited,
                                                                    usertype]
                                )
    return query_response