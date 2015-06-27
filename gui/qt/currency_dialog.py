import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _
from chainkey import chainparams

from util import HelpButton, ok_cancel_buttons

import operator

class ChangeCurrencyDialog(QDialog):

    def __init__(self, parent, verbose_view=False):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.verbose_view = verbose_view
        self.setWindowTitle(_('Change Currency'))

        self.main_layout = main_layout = QVBoxLayout()

        self.create_chains_info()
        self.create_chains_view()
        self.refresh_chains()

        chains_view = self.chains_view
        # Sort by favorite chains, then by code
        chains_view.sortItems(0, Qt.AscendingOrder)
        chains_view.sortItems(3, Qt.AscendingOrder)
        main_layout.addWidget(chains_view)

        main_layout.addLayout(ok_cancel_buttons(self))

        self.setLayout(main_layout)

    def create_chains_view(self):
        self.chains_view = chains_view = QTreeWidget()
        if self.verbose_view:
            chains_view.setColumnCount(6)
            chains_view.setHeaderLabels([ _('Code'), _('Currency'), _('Initialized'), _('Favorite'), _('PoW'), _('Servers') ])
            chains_view.setColumnWidth(0, 90)
            chains_view.setColumnWidth(1, 150)
            chains_view.setColumnWidth(2, 80)
            chains_view.setColumnWidth(3, 80)
            chains_view.setColumnWidth(4, 60)
            chains_view.setColumnWidth(5, 50)
            chains_view.setMinimumWidth(540)
        else:
            chains_view.setColumnCount(4)
            chains_view.setHeaderLabels([ _('Code'), _('Currency'), _('Initialized'), _('Favorite') ])
            chains_view.setColumnWidth(0, 90)
            chains_view.setColumnWidth(1, 150)
            chains_view.setColumnWidth(2, 80)
            chains_view.setColumnWidth(3, 80)
            chains_view.setMinimumWidth(430)

    def refresh_chains(self):
        chains_view = self.chains_view
        chains_view.clear()

        chains = chainparams.known_chains
        favorites = self.parent.config.get_above_chain('favorite_chains', [])
        # Yes or No
        y_or_n = lambda x: 'Yes' if x==True else 'No'
        for ch in sorted(chains, key=operator.attrgetter('code')):

            is_initialized = True
            dummy_key = self.parent.wallet.storage.get_chain_value(ch.code, 'accounts')
            if dummy_key is None:
                is_initialized = False

            is_favorite = ch.code in favorites
            server_trust = chainparams.get_server_trust(ch.code)
            uses_pow = server_trust['pow']
            num_servers = server_trust['servers']
            if self.verbose_view:
                item = QTreeWidgetItem([ch.code, ch.coin_name, y_or_n(is_initialized), y_or_n(is_favorite), y_or_n(uses_pow), str(num_servers)])
            else:
                item = QTreeWidgetItem([ch.code, ch.coin_name, y_or_n(is_initialized), y_or_n(is_favorite)])
            chains_view.addTopLevelItem(item)
        chains_view.setCurrentItem(chains_view.topLevelItem(0))
        chains_view.setSortingEnabled(True)

    def create_chains_info(self):
        main_layout = self.main_layout
        change_info = QLabel(_("Select a currency to start using it. The key below explains the column(s) in the currency table."))
        change_info.setWordWrap(True)
        main_layout.addWidget(change_info)

        change_sep = QFrame()
        change_sep.setFrameShape(QFrame.HLine)
        change_sep.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(change_sep)

        # Explanation of table columns
        self.key_layout = key_layout = QGridLayout()
        key_layout.setSpacing(0)
        key_layout.setColumnMinimumWidth(0, 75)
        key_layout.setColumnStretch(1, 1)

        key_layout.addWidget(QLabel(_('Initialized:')), 0, 0)
        key_layout.addWidget(QLabel(_('Whether this currency has been activated before.')), 0, 1)
        key_layout.addWidget(HelpButton(_('The first time you use a currency, you must enter your password to initialize it.')), 0, 2)

        key_layout.addWidget(QLabel(_('Favorite:')), 1, 0)
        key_layout.addWidget(QLabel(_('Whether this currency is in your favorites.')), 1, 1)
        key_layout.addWidget(HelpButton(_('Favorite chains are specified in Preferences.')), 1, 2)

        if self.verbose_view:
            key_layout.addWidget(QLabel(_('PoW:')), 2, 0)
            key_layout.addWidget(QLabel(_('Whether this wallet verifies proof-of-work.')), 2, 1)
            key_layout.addWidget(HelpButton(_('Verifying proof-of-work helps ensure that data the wallet receives is legitimate.')), 2, 2)

            key_layout.addWidget(QLabel(_('Servers:')), 3, 0)
            key_layout.addWidget(QLabel(_('Number of default servers this currency has.')), 3, 1)
            key_layout.addWidget(HelpButton(_('The more servers there are, the less trust has to be placed in one party.')), 3, 2)

        main_layout.addLayout(key_layout)
