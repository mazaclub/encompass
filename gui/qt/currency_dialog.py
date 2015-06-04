import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _
from chainkey import chainparams

from util import ok_cancel_buttons

import operator

class ChangeCurrencyDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(_('Change Currency'))

        main_layout = QVBoxLayout()
        change_info = QLabel(_("Note that you will need to enter your password the first time you use a new currency.\n"))
        change_info.setWordWrap(True)
        main_layout.addWidget(change_info)

        key_info = QLabel(_("PoW: Whether this wallet verifies proof-of-work.\nServers: Number of default servers to get data from."))
        key_info.setWordWrap(True)
        main_layout.addWidget(key_info)

        self.chains_view = chains_view = QTreeWidget()
        chains_view.setColumnCount(4)
        chains_view.setHeaderLabels([ _('Code'), _('Currency'), _('PoW'), _('Servers') ])
        chains_view.setColumnWidth(0, 75)
        chains_view.setColumnWidth(1, 125)
        chains_view.setColumnWidth(2, 60)
        chains_view.setColumnWidth(3, 50)
        chains_view.setMinimumWidth(325)
        chains = chainparams._known_chains
        # Yes or No
        y_or_n = lambda x: 'Yes' if x==True else 'No'
        for ch in sorted(chains, key=operator.attrgetter('code')):
            server_trust = chainparams.get_server_trust(ch.code)
            uses_pow = server_trust['pow']
            num_servers = server_trust['servers']
            item = QTreeWidgetItem([ch.code, ch.coin_name, y_or_n(uses_pow), str(num_servers)])
            chains_view.addTopLevelItem(item)
        chains_view.setCurrentItem(chains_view.topLevelItem(0))
        main_layout.addWidget(chains_view)

        main_layout.addLayout(ok_cancel_buttons(self))

        self.setLayout(main_layout)

