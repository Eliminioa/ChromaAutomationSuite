import sys
import time
from pickle import dumps

import praw

import memory
from Body import botIO
from Utilities import configReader, connector
from Utilities.loggingSetup import create_logger


class Mind(Process):
    """
    A class for the mind of Prime or ORHQ. Lets them do their "thinking"
    i.e. get new users from the sign-ups, figure out which side a user is
    on, and in the future maybe do some battle-related things.
    """

    def __init__(self, name, config, antenna, nerves, lock):
        Process.__init__(self)
        self.name = name
        self.daemon = True
        self.lock = lock
        self.antenna = antenna
        self.cfg = config
        self.nerves = nerves
        self.log = create_logger(__name__)
        self.db = sqlite3.connect(config['DATABASE'])

    def run(self):
        print("MIND PID: {}".format(self.pid))
        while True:
            try:
                signal_received = self.nerves.recv()
                if signal_received == 'THINK':
                    self.log.debug("Began MIND process")
                    self.nerves.send('ONLINE')
                    self.listen()
            except:
                exctype, value = sys.exc_info()[:2]
                self.log.error("Error in thinking: {}: {}".format(
                    exctype,
                    value))
            finally:
                self.nerves.send('OFFLINE')

    def listen(self):
        """
        The actual workflow of monitoring sign ups and user involvement.
        Right now that means getting recruits from the sign up thread
        and figuring out which side people are on.

        :return: Nothing as of now
        """
        user = None
        side = None
        self.log.info("Began thinking")

        while True:
            # TODO Aggregate lore from Chromalore and battles and store it

            #set antenna to correct side
            user = ('Orangered_HQ' if user == 'Periwinkle_Prime_3'
                    else 'Periwinkle_Prime_3')
            side = (0 if side == 1 else 1)
            self.antenna.set_user(user)
            self.log.info("Set antenna to {}".format(user))

            self.get_recruits(user, side)

            self.get_combatants()

            self.update_all_group(side)

            # refresh bot's token
            new_access_info = self.antenna.refresh_token_user()
            memory.handle_player_memory(self.db,
                                        user,
                                        accessInfo=dumps(new_access_info))

            print("Done with {}'s cycle".format(user))
            time.sleep(30)

    def get_recruits(self, user, side):
        """
        Get and handle new recruits from sign up theads.

        :param user: username of active bot
        :param side: side of active bot
        :return: list of new recruits
        """
        # use sensors.get_recruit_commenters to get new top-level comments
        # lock stuff down while handling the DB
        self.lock.acquire()
        new_recruits = botIO.recruit_getter(self.cfg,
                                            self.db,
                                            self.antenna,
                                            side)
        self.lock.release()
        self.log.info("Retrieved {} new recruits".format(
            len(new_recruits)))

        # handle the recruits
        for recruit in new_recruits:
            self.lock.acquire()
            memory.handle_player_memory(self.db,
                                        str(recruit.author).lower(),
                                        side=side,
                                        recruited=True)
            self.lock.release()
            self.log.info("Handled player {} of side {}".format(
                str(recruit.author), side))
            print("Handled player {} of side {}".format(
                str(recruit.author), side))

            # if the bot hasn't already replied, then do so
            if user not in [str(rep.author) for rep in recruit.replies
                            if not isinstance(rep,
                                              praw.objects.MoreComments)]:
                botIO.reply_to_signup(recruit, side, self.cfg)
                self.log.debug("Replied to player {}".format(
                    str(recruit.author), side))
        return new_recruits

    def get_combatants(self):
        """
        Retrieve chromabot's post history and examine skirmishes to identify
        players and their side. This is the ultimate arbiter of user side,
        superseding the recruit thread side. Ideally, this will also handle
        attendance and troop count stuff.

        :param user: username of active bot
        :return: dict of combatants and their side
        """
        # scan battle history with sensors.retrieve_combatants and
        # receive a dict of users and their side
        self.lock.acquire()
        combatant_dict = botIO.retrieve_combatants(self.antenna, self.cfg)
        self.lock.release()

        # handle combatants
        for combatant in combatant_dict:
            self.lock.acquire()
            memory.handle_player_memory(self.db,
                                        combatant,
                                        side=combatant_dict[combatant])
            self.lock.release()

        # TODO Keep track of user troop counts and battle counts too
        return combatant_dict

    def update_all_group(self, side):
        """
        Updates the 'all' group of the active side to reflect actual users. In
        other words, this prevents members of the opposite team from receiving
        messages meant for this team.

        :param user: username of active bot
        :param side: side of active bot
        :return: None
        """
        self.lock.acquire()
        allied_users = memory.get_players_with(self.db,
                                               side=side,
                                               recruited=True)
        memory.update_list(side, 'all', allied_users)
        self.lock.release()
        return None
