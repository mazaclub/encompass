import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _
from chainkey import chainparams

from util import HelpButton, ok_cancel_buttons

import operator

class ChangeCurrencyDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(_('Change Currency'))

        main_layout = QVBoxLayout()
        change_info = QLabel(_("Select a currency to start using it. The key below explains the columns in the currency table."))
        change_info.setWordWrap(True)
        main_layout.addWidget(change_info)

        change_sep = QFrame()
        change_sep.setFrameShape(QFrame.HLine)
        change_sep.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(change_sep)

        # Explanation of table columns
        key_layout = QGridLayout()
        key_layout.setSpacing(0)
        key_layout.setColumnMinimumWidth(0, 75)
        key_layout.setColumnStretch(1, 1)

        key_layout.addWidget(QLabel(_('Initialized:')), 0, 0)
        key_layout.addWidget(QLabel(_('Whether this currency has been activated before.')), 0, 1)
        key_layout.addWidget(HelpButton(_('The first time you use a currency, you must enter your password to initialize it.')), 0, 2)

        key_layout.addWidget(QLabel(_('PoW:')), 1, 0)
        key_layout.addWidget(QLabel(_('Whether this wallet verifies proof-of-work.')), 1, 1)
        key_layout.addWidget(HelpButton(_('Verifying proof-of-work helps ensure that data the wallet receives is legitimate.')), 1, 2)

        key_layout.addWidget(QLabel(_('Servers:')), 2, 0)
        key_layout.addWidget(QLabel(_('Number of default servers this currency has.')), 2, 1)
        key_layout.addWidget(HelpButton(_('The more servers there are, the less trust has to be placed in one party.')), 2, 2)

        main_layout.addLayout(key_layout)

        self.chains_view = chains_view = QTreeWidget()
        chains_view.setColumnCount(4)
        chains_view.setHeaderLabels([ _('Code'), _('Currency'), _('Initialized'), _('PoW'), _('Servers') ])
        chains_view.setColumnWidth(0, 90)
        chains_view.setColumnWidth(1, 150)
        chains_view.setColumnWidth(2, 80)
        chains_view.setColumnWidth(3, 60)
        chains_view.setColumnWidth(4, 50)
        chains_view.setMinimumWidth(500)
        chains = chainparams._known_chains
        # Yes or No
        y_or_n = lambda x: 'Yes' if x==True else 'No'
        for ch in sorted(chains, key=operator.attrgetter('code')):

            is_initialized = True
            dummy_key = self.parent.wallet.storage.get_chain_value(ch.code, 'accounts')
            if dummy_key is None:
                is_initialized = False

            server_trust = chainparams.get_server_trust(ch.code)
            uses_pow = server_trust['pow']
            num_servers = server_trust['servers']
            item = QTreeWidgetItem([ch.code, ch.coin_name, y_or_n(is_initialized), y_or_n(uses_pow), str(num_servers)])
            chains_view.addTopLevelItem(item)
        chains_view.setCurrentItem(chains_view.topLevelItem(0))
        main_layout.addWidget(chains_view)

        main_layout.addLayout(ok_cancel_buttons(self))

        self.setLayout(main_layout)

    def refresh_chains(self):
        chains_view = self.chains_view
        chains_view.clear()

        chains = chainparams._known_chains
        # Yes or No
        y_or_n = lambda x: 'Yes' if x==True else 'No'
        for ch in sorted(chains, key=operator.attrgetter('code')):

            is_initialized = True
            dummy_key = self.parent.wallet.storage.get_chain_value(ch.code, 'accounts')
            if dummy_key is None:
                is_initialized = False

            server_trust = chainparams.get_server_trust(ch.code)
            uses_pow = server_trust['pow']
            num_servers = server_trust['servers']
            item = QTreeWidgetItem([ch.code, ch.coin_name, y_or_n(is_initialized), y_or_n(uses_pow), str(num_servers)])
            chains_view.addTopLevelItem(item)
        chains_view.setCurrentItem(chains_view.topLevelItem(0))
