import sys
import time
import sqlite3
from multiprocessing import Process

import memory
from Body import sensors
from Utilities.loggingSetup import create_logger

class Mind(Process):
    """
    A class for the mind of Prime or ORHQ. Lets them do their "thinking" i.e.
    get new users from the sign-ups, figure out which side a user is on, and
    in the future maybe do some battle-related things.
    """

    def __init__(self, name, config, antenna, nerves):
        Process.__init__(self)
        self.name=name
        self.antenna = antenna
        self.cfg = config
        self.nerves = nerves
        self.log = create_logger(__name__)
        self.db = sqlite3.connect(config['DATABASE'])

    def run(self):
        while True:
            try:
                self.log.debug("Began MIND process")
                self.think()
            except:
                exctype, value = sys.exc_info()[:2]
                self.log.error("Error in thinking: {}: {}".format(exctype, value))


    def think(self):
        user = None
        self.log.info("Began thinking")
        signal_received = self.nerves.poll(None)
        while signal_received:
            # choose which side to work with
            # use sensors.get_recruit_commenters to get top-level comment authors
            # pass list of new top-level commenters to self.register_recruits
            # scan Chromabot's battle history with sensors.retrieve_combatants and receive a list of users and their side
            # pass this list through memory.handle_player_memory to store user sides
            # TODO See if I can keep track of user troop counts and battle counts too
            # TODO Aggregate lore from Chromalore and battles and store it in the DB

            #set antenna to correct side
            user = ('Orangered_HQ' if user == 'Periwinkle_Prime_3' else 'Periwinkle_Prime_3')
            self.antenna.set_user(user)
            self.log.info("Set antenna to {}".format(user))
            sensors.recruit_getter(self.cfg, self.antenna, self.db)
            time.sleep(2)

            # sensors.get_recruit_commenters(side)