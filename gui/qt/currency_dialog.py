import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _
from chainkey import chainparams
from chainkey.util import print_error

from util import HelpButton, ok_cancel_buttons

import functools
import operator

class FavoriteCurrenciesDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(_('Favorite Coins'))
        known_chains = chainparams.known_chain_codes
        self.favorites = self.parent.config.get_above_chain('favorite_chains', [])
        # sanity check, just in case. Main window should have already done this
        if len(self.favorites) > 3: self.favorites = self.favorites[:3]

        self.main_layout = vbox = QVBoxLayout()
        limit_label = QLabel(_('Up to three coins may be selected as "favorites."\nThey will be listed before other coins in the currency selection dialog.'))
        vbox.addWidget(limit_label)

        self.coin_checkboxes = []
        for coin in known_chains:
            checkbox = QCheckBox(coin)
            checkbox.setChecked(coin in self.favorites)
            checkbox.stateChanged.connect(functools.partial(self.change_coin_state, checkbox))
            self.coin_checkboxes.append(checkbox)
            vbox.addWidget(checkbox)

        vbox.addLayout(ok_cancel_buttons(self, ok_label=_('Save')))
        self.accepted.connect(self.save_favorites)
        self.setLayout(vbox)
        self.enforce_limit()

    def enforce_limit(self):
        """Enforce limit on list of favorite chains."""
        if not self.coin_checkboxes: return
        if len(self.favorites) < 3:
            for box in self.coin_checkboxes:
                box.setEnabled(True)
        else:
            for box in self.coin_checkboxes:
                if not box.isChecked():
                    box.setEnabled(False)

    def change_coin_state(self, checkbox):
        code = str(checkbox.text())
        is_favorite = checkbox.isChecked()
        if is_favorite and code not in self.favorites:
            self.favorites.append(code)
        elif not is_favorite and code in self.favorites:
            self.favorites.remove(code)
        self.enforce_limit()

    def save_favorites(self):
        print_error("Saving new favorite chains: {}".format(map(lambda x: x.encode('ascii', 'ignore'), self.favorites)))
        self.parent.config.set_key_above_chain('favorite_chains', self.favorites, True)

def append_currency_key(grid, label, key, helpbutton):
    """Add an explanation of a column to grid."""
    row = grid.rowCount()
    grid.addWidget(QLabel(label), row, 0)
    key_label = QLabel(key)
    key_label.setWordWrap(True)
    grid.addWidget(key_label, row, 1)
    grid.addWidget(HelpButton(helpbutton), row, 2)

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

        main_layout.addWidget(self.chains_view)

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
        # Sort by favorite chains, then by code
        chains_view.sortItems(0, Qt.AscendingOrder)
        chains_view.sortItems(3, Qt.DescendingOrder)

    def create_chains_info(self):
        main_layout = self.main_layout
        change_info = QLabel(_("Select a currency to start using it. The key below explains the columns in the currency table."))
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
        key_layout.setVerticalSpacing(6)

        append_currency_key(key_layout, _('Initialized:'),
                _('Whether this currency has been activated before.'),
                _('The first time you use a currency, you must enter your password to initialize it.'))

        append_currency_key(key_layout, _('Favorite:'),
                _('Whether this currency is in your favorites.'),
                _('Favorite coins are specified in Preferences.'))

        if self.verbose_view:
            append_currency_key(key_layout, _('PoW:'),
                    _('Whether this wallet verifies proof-of-work.'),
                    _('Verifying proof-of-work helps ensure that data the wallet receives is legitimate.'))

            append_currency_key(key_layout, _('Servers:'),
                    _('Number of default servers this currency has.'),
                    _('The more servers there are, the less trust has to be placed in one party.'))

        main_layout.addLayout(key_layout)
