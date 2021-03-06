from itertools import chain
from errbot import botcmd, BotPlugin

#config keys
ALL_USERS = 'ALL_USERS'

# err persisted settings keys
CONFIRMED = 'confirmed'
OPTED_OUT = 'opted_out'

class TCS(BotPlugin):
    CONFIG_TEMPLATE = {
        ALL_USERS: ','.join([
            'alexs',
        ]),
    }
    
    def activate(self):
        """
        Initialization on plugin load
        """
        super().activate()

        # init persistent storage, chance to set things up the first time the plugin is activated
        self._setup_store()

        self.link = ""

    def _setup_store(self):
        if CONFIRMED not in self:
            self[CONFIRMED] = []
        if OPTED_OUT not in self:
            self[OPTED_OUT] = []

    def _reset_store(self):
        self[CONFIRMED] = []
        self[OPTED_OUT] = []

    @property
    def all_users(self):
        if self.config and ALL_USERS in self.config:
            return self.config[ALL_USERS].split(',')
        else:
            return []

    def get_missing_rsvps(self):
        return [
            user for user in self.all_users
            if (user not in self[CONFIRMED]) and (user not in self[OPTED_OUT])
        ]
            
    @botcmd
    def food_ask(self, msg, args):
        self._reset_store()
        self.link = args
        users = self.get_missing_rsvps()
        for user in users:
            self._ask_user_to_confirm(user, self.link)

        return "Asked {} to confirm.".format(", ".join(users))

    @botcmd
    def food_nag(self, msg, args):
        users = self.get_missing_rsvps()
        for user in users:
            self._ask_user_to_confirm(user, self.link)

        return "Asked {} missing people to confirm.".format(", ".join(users))

    def _ask_user_to_confirm(self, user, sheet_link):
        user_id = self._build_id(user)
        message = """It's time for Team Lunch! If your order is correct please reply with `!food_in`, if you would like to opt-out this week reply with `!food_out`.
Order sheet: {}""".format(sheet_link)
        self.send(user_id, message)

    @botcmd
    def food_in(self, msg, args):
        user = msg.frm.nick
        self._add_to_list(user, CONFIRMED)
        self._remove_from_list(user, OPTED_OUT)
        return "Thank you for confirming!"

    @botcmd
    def food_out(self, msg, args):
        user = msg.frm.nick
        self._add_to_list(user, OPTED_OUT)
        self._remove_from_list(user, CONFIRMED)
        return "Got it, we'll opt you out if it's not too late."

    @botcmd
    def food_status(self, msg, args):
        output = ""
        if self[CONFIRMED]:
            output += "\n* Confirmed orders from: {}".format(", ".join(self[CONFIRMED]))
        if self[OPTED_OUT]:
            output += "\n* People opting-out: {}".format(", ".join(self[OPTED_OUT]))
        if self.get_missing_rsvps():
            output += "\n* Haven't heard from: {}".format(", ".join(self.get_missing_rsvps()))

        return output

    def get_configuration_template(self):
        return self.CONFIG_TEMPLATE

    def configure(self, configuration):
        """
            This will setup a default config, called before activate or when user sets config options
        """
        if configuration is not None and configuration != {}:
            config = dict(chain(self.CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = self.CONFIG_TEMPLATE
        super(TCS, self).configure(config)

    def _build_id(self, user):
        return self.build_identifier("@{}".format(user))

    def _add_to_list(self, item, list_key):
        """
        helper util because errbot persistence is awkward
        """
        with self.mutable(list_key) as l:
            l.append(item)

    def _remove_from_list(self, item, list_key):
        """
        helper util because errbot persistence is awkward
        """
        with self.mutable(list_key) as l:
            if item in l:
                l.remove(item)

