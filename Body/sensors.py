from Mind import memory
from Utilities import CASexcepts as excs
from Utilities.loggingSetup import create_logger
"""
Module for letting the Chroma Automation Suite sense users both signing up
to receive alerts from their generals and to sense which side players are on.
"""
LOG = create_logger(__name__)


def recruit_getter(cfg, db, antenna, side):
    """
    Get all of the new recruits from the proper side's recruitment thread
    and return them in a list. Note that this will only return new
    recruits.

    :param cfg: Global configuration information to be used
    :param db: Database to be used
    :param antenna: Antenna connection to Reddit
    :param side: Side to gather recruits from
    :return: A list of new recruits.
    """
    # retrieve majors from DB
    majors = memory.get_players_with(db, side=side, recruited=True)

    # retrieve sign up thread from reddit
    if side == 0:
        signup_thread = antenna.get_submission(
            submission_id=cfg['OR_RECRUIT_THREAD'],
            comment_limit=None,
            comment_sort='new')
    elif side == 1:
        signup_thread = antenna.get_submission(
            submission_id=cfg['PW_RECRUIT_THREAD'],
            comment_limit=None,
            comment_sort='new')
    else:
        raise excs.InvalidSideError(__name__, side)
    LOG.debug('Got signup thread for side {} from {}'.format(
        side,
        signup_thread.id))
    # and replace more comments
    signup_thread.replace_more_comments()
    LOG.debug('Replaced more comments')

    # list comment authors from comment generator
    all_recruits = [cmnt.author for cmnt in signup_thread.comments]

    # filter out already registered recruits
    new_recruits = [recr for recr in all_recruits if recr not in majors]

    return new_recruits

def checkForGo(self):
    """Checks Prime's inbox for messages to send out."""
    r = self.r
    troopList = self.getUsers()
    troopList = [user for user in troopList]# if (not self.detect_ORed(user)) and (not user in self.cfg.blacklist)]
    PMs = [pm for pm in r.get_unread(True, True)]
    if len(PMs) != 0:
        self.log.log_status("{}: New messages!".format(self.name))
        print("{}: New messages!".format(self.name))
        for PM in PMs:
            PM.mark_as_read()
            sLine = PM.subject.strip().upper()
            print("{}: PM subject line is {}".format(self.name, sLine))
            print("{}: generals: {}".format(self.name, self.cfg.generals))
            if (sLine == "SEND MESSAGE") and (PM.author.__str__().lower() in self.cfg.generals):
                print("{}: Found a new send message!".format(self.name))
                sent_to = ''
                for troops in troopList:
                    try:
                        r.send_message(troops,"Battle Reminder",PM.body)
                        sent_to += troops+'\n\n'
                        self.log.log_status("{}: Message: {} sent to {}".format(self.name, PM.body, troops))
                    except:
                        self.log.log_status("Error with " + troops)
                self.log.log_status("{}: Message sent to {}!".format(self.name, sent_to))
                PM.reply("Message sent to "+sent_to+"!")
    else:
        self.log.log_status("No new messages!")

def replyToSignup(self,signUp,PW=True):
    if not PW:
        # signUp.reply("""    ORANGERED SCUM DETECTED
        #     LETHAL FORCE ACTIVATED""")
        pass
    else:
        message = 'AFFIRMATIVE. USER ' + str(signUp.author).upper() + " HAS BEEN ENTERED INTO THE DATABASE."
        keys = self.keywords(signUp.body)
        if 'h' in keys:
            message = "GREETINGS USER " + str(signUp.author).upper() + ". YOU HAVE BEEN ENTERED INTO THE DATABASE."
        if ('s' in keys) or ('w' in keys):
            message = message.replace('. ', '. AS DESIRED, ',1)
        # if 'a' in keys:
        #     message += ' I AGREE, PERIWINKLE IS THE SUPERIOR RACE.'
        # if 'b' in keys:
        #     message += ' INDEED, ORANGREDS ARE A MENACE!'
        # if 'p' in keys:
        #     message += ' YOU HAVE BEEN DETECTED AS A TRUE PERIWINKLE PATRIOT!'
        signUp.reply(message)

def keywords(self,text):
    positiveAdj = [u'fantastic', u'grand', u'howling', u'marvelous', u'marvellous', u'rattling', u'terrific', u'tremendous', u'wonderful', u'wondrous', u'excellent', u'first-class', u'fantabulous', u'splendid', u'amazing', u'awe-inspiring', u'awesome', u'awful', u'awing', u'good', u'estimable', u'good', u'honorable', u'respectable','best','better']
    negativeAdj = ['bad','unfit','unsound','evil','immoral','wicked','vicious','malefic','malevolent','malignant','menance','threat','trash','scum','villain','scoundrel']
    positiveVbs = []
    negativeVbs = []
    periWords = ['periwinkle','periwinkles','pw','pws','peri','peris','prime']
    orWords = ['orangered','orangereds','or','ors','ored','oreds']
    positivePeris = [adj+" "+peri for adj in positiveAdj for peri in periWords]+[peri+" is "+adj for adj in positiveAdj for peri in periWords]
    badORed = [adj+" "+ored for adj in negativeAdj for ored in orWords]+[ored+" is "+adj for adj in negativeAdj for ored in orWords]
    sents = [k.lower() for i in text.split('.') for j in i.split('!') for k in j.split('?')]
    keys = ''
    for sent in sents:
        if ('sign up' in sent) or ('sign me up' in sent):
            keys += 's'
        if ('hi' in sent) or ('hello' in sent) or ('greetings' in sent):
            keys += 'h'
        if ('better dead than orangered' in sent):
            keys += "p"
        if ('want' in sent) or ('wish' in sent) or ("i'd like" in sent):
            keys += "w"
        for positive in positivePeris:
            if positive in sent:
                keys += "a"
        for bad in badORed:
            if bad in sent:
                keys += "b"
    return keys

def cleanse_list(self):
    for user in self.cfg.majors:
        if user in self.cfg.orangereds:
            self.cfg.confData['majors'].remove(user)
            self.cfg.save_cfg()

def detect_ORed(self,user):
    if str(user) in self.cfg.orangereds:
        return True
    return False
