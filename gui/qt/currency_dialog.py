import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _
from chainkey import chainparams
from chainkey.util import print_error

from util import HelpButton, ok_cancel_buttons, close_button
from style import MyTreeWidget, MyStyleDelegate

import functools
import operator
import copy

class CurrenciesCheckboxDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.parent = parent
        known_chains = chainparams.known_chains

        self.scroll_area = scroll = QScrollArea()
        scroll.setEnabled(True)
        scroll.setWidgetResizable(True)
        scroll.setMinimumSize(25, 100)

        self.coin_scroll_widget = scroll_widget = QWidget()
        scroll_widget.setMinimumHeight(len(known_chains) * 35)
        scroll_widget.setObjectName("chains_area")

        # layout containing the checkboxes
        self.coin_boxes_layout = coin_vbox = QVBoxLayout()
        # Contains the scrollarea, including coin_boxes_layout
        self.scroll_layout = scroll_layout = QVBoxLayout()

        self.coin_checkboxes = []
        for coin in sorted(known_chains, key=operator.attrgetter('code')):
            box_label = ''.join([ coin.code, " (", coin.coin_name, ")" ])
            checkbox = QCheckBox(box_label)
            checkbox.stateChanged.connect(functools.partial(self.change_coin_state, checkbox))
            self.coin_checkboxes.append(checkbox)
            coin_vbox.addWidget(checkbox)

        scroll_widget.setLayout(coin_vbox)
        scroll.setWidget(scroll_widget)
        scroll_layout.addWidget(scroll)

    def change_coin_state(self, checkbox):
        pass

class HideCurrenciesDialog(CurrenciesCheckboxDialog):
    def __init__(self, parent):
        CurrenciesCheckboxDialog.__init__(self, parent)
        self.setWindowTitle(_('Hide Coins'))
        self.hide_chains = self.parent.config.get_above_chain('hide_chains', [])

        # sanity checking
        active_chain_code = self.parent.active_chain.code
        if active_chain_code in self.hide_chains:
            self.hide_chains.remove(active_chain_code)

        self.main_layout = vbox = QVBoxLayout()
        hide_label = QLabel(_('You can select chains here that will be hidden from view in the currency selection dialog.'))
        vbox.addWidget(hide_label)

        for cbox in self.coin_checkboxes:
            code = str(cbox.text()).split()[0]
            if code == active_chain_code:
                cbox.setChecked(False)
                cbox.setEnabled(False)
                continue
            cbox.setChecked(code in self.hide_chains)
        vbox.addLayout(self.scroll_layout)

        vbox.addLayout(close_button(self))
        self.finished.connect(self.save_hide_chains)
        self.setLayout(vbox)

    def change_coin_state(self, checkbox):
        code = str(checkbox.text()).split()[0]
        is_hiding = checkbox.isChecked()
        if is_hiding and code not in self.hide_chains:
            self.hide_chains.append(code)
        elif not is_hiding and code in self.hide_chains:
            self.hide_chains.remove(code)

    def save_hide_chains(self):
        self.parent.config.set_key_above_chain('hide_chains', self.hide_chains, True)

class FavoriteCurrenciesDialog(CurrenciesCheckboxDialog):
    def __init__(self, parent):
        CurrenciesCheckboxDialog.__init__(self, parent)
        self.setWindowTitle(_('Favorite Coins'))
        self.favorites = copy.deepcopy(self.parent.config.get_above_chain('favorite_chains', []))
        # sanity check, just in case. Main window should have already done this
        if len(self.favorites) > 3: self.favorites = self.favorites[:3]

        self.main_layout = vbox = QVBoxLayout()
        limit_label = QLabel(_('\n'.join([
            'Up to three coins may be selected as "favorites."',
            '\nHolding down the coin icon in the wallet status bar will show you your favorite coins and allow you to quickly switch between them.',
            'They will also be listed before other coins in the currency selection dialog.'])))
        limit_label.setWordWrap(True)
        vbox.addWidget(limit_label)

        for cbox in self.coin_checkboxes:
            cbox.setChecked(str(cbox.text()).split()[0] in self.favorites)
        vbox.addLayout(self.scroll_layout)

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
        code = str(checkbox.text()).split()[0]
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
        self.chains_view = chains_view = MyTreeWidget(self)
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

        role_name = 'chains_verbose' if self.verbose_view else 'chains'
        chains_view.setItemDelegate(MyStyleDelegate(self, role_name))

    def refresh_chains(self):
        chains_view = self.chains_view
        chains_view.clear()

        chains = chainparams.known_chains
        favorites = self.parent.config.get_above_chain('favorite_chains', [])
        hidden_chains = self.parent.config.get_above_chain('hide_chains', [])
        # Yes or No
        y_or_n = lambda x: 'Yes' if x==True else 'No'
        for ch in sorted(chains, key=operator.attrgetter('code')):
            if ch.code in hidden_chains:
                continue

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
