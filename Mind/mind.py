import sys
import time
import sqlite3
from multiprocessing import Process

import praw

import memory
from Body import botIO
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
                self.log.debug("Began MIND process")
                self.listen()
            except:
                exctype, value = sys.exc_info()[:2]
                self.log.error("Error in thinking: {}: {}".format(
                    exctype,
                    value))
                raise

    def listen(self):
        """
        The actual workflow of monitoring sign ups and user involvement.
        Right now that means getting recruits from the sign up thread
        and figuring out which side people are on.

        :return: Nothing as of now
        """
        user = None
        side = None

        # wait for signal to begin
        signal_received = self.nerves.poll(None)
        self.log.info("Began thinking")

        # once it gets the signal to go
        while signal_received:
            # TODO Keep track of user troop counts and battle counts too
            # TODO Aggregate lore from Chromalore and battles and store it

            #set antenna to correct side
            user = ('Orangered_HQ' if user == 'Periwinkle_Prime_3'
                    else 'Periwinkle_Prime_3')
            side = (0 if side == 1 else 1)
            self.antenna.set_user(user)
            self.log.info("Set antenna to {}".format(user))

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
                                            str(recruit.author),
                                            side=side,
                                            recruited=True)
                memory.add_player(side, 'all', str(recruit.author))
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

            # scan battle history with sensors.retrieve_combatants and
            # receive a dict of users and their side
            self.lock.acquire()
            combatant_dict = botIO.retrieve_combatants(self.antenna)
            self.lock.release()

            # handle combatants
            for combatant in combatant_dict:
                self.lock.acquire()
                memory.handle_player_memory(self.db,
                                            combatant,
                                            side=combatant_dict[combatant])
                self.lock.release()

            # refresh bot's token

            print("Done with {}'s cycle".format(user))
            time.sleep(30)
