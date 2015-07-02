from PyQt4.QtGui import *

import os

from chainkey.plugins import BasePlugin, hook
from chainkey.i18n import _
from chainkey.util import format_satoshis

from chainkey_gui.qt.util import EnterButton, ok_cancel_buttons, filename_field

class Plugin(BasePlugin):

    def __init__(self, config, name):
        BasePlugin.__init__(self, config, name)
        self.file_path = None
        self.csv = False

    def requires_settings(self):
        return True

    def settings_widget(self, window):
        return EnterButton(_('Settings'), self.settings_dialog)

    def settings_dialog(self):
        d = QDialog(self.window)
        d.setWindowTitle("Auto History Export")
        d.setMinimumWidth(500)
        vbox = QVBoxLayout(d)

        select_msg = _("Select the file that wallet history will be exported to.")
        hbox, filename_e, csv_button = filename_field(d, self.window.config, self.file_path, select_msg, False)
        vbox.addLayout(hbox)

        vbox.addLayout(ok_cancel_buttons(d))

        if not d.exec_():
            return

        self.csv = csv_button.isChecked()
        self.file_path = str(filename_e.text())
        if not self.file_path:
            file_suffix = ".csv" if self.csv else ".json"
            filename = ''.join(["~/encompass-history", file_suffix])
            self.file_path = os.path.expanduser(filename)

        self.save_config()

    def save_config(self):
        options = {
            'export_filename': str(self.file_path),
            'csv_format': self.csv
        }
        self.print_error('Saving config: {}'.format(options))
        self.wallet.storage.config.set_key_above_chain('auto_history_export', options, True)

    @hook
    def load_wallet(self, wallet, window):
        self.wallet = wallet
        self.window = window
        options = wallet.storage.config.get_above_chain('auto_history_export', {})
        self.file_path = options.get('export_filename', os.path.expanduser('~/encompass-history.json'))
        self.csv = options.get('csv_format', False)

    @hook
    def receive_tx_callback(self, tx_hash, tx, tx_height):
        if not self.window or not self.wallet: return
        lines = self.window.create_export_history(self.wallet, self.csv)
        self.window.do_export_history(lines, self.file_path, self.csv, self.wallet.active_chain)
        self.print_error('Saved wallet history')
