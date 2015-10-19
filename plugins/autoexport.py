from PyQt4.QtGui import *

import os

from chainkey.plugins import BasePlugin, hook
from chainkey.i18n import _
from chainkey.util import format_satoshis
from chainkey.base58 import is_address

from chainkey_gui.qt.util import EnterButton, close_button, filename_field, HelpButton

class Plugin(BasePlugin):

    def __init__(self, config, name):
        BasePlugin.__init__(self, config, name)
        self.file_path = None
        self.csv = False
        self.full_labels = True

    def requires_settings(self):
        return True

    def settings_widget(self, window):
        return EnterButton(_('Settings'), self.settings_dialog)

    def settings_dialog(self):
        d = QDialog(self.window)
        d.setWindowTitle("Auto History Export")
        d.setMinimumWidth(500)
        vbox = QVBoxLayout(d)

        format_layout = QVBoxLayout()
        format_widget = QWidget()
        format_layout.addWidget(format_widget)

        def change_use_full_labels(checked):
            checked = bool(checked)
            self.full_labels = checked
            self.save_config()

        use_full_labels = QCheckBox('Export full transaction labels.')
        use_full_labels.setChecked(self.full_labels)
        use_full_labels.stateChanged.connect(change_use_full_labels)
        full_labels_layout = QHBoxLayout()
        full_labels_layout.addWidget(use_full_labels)
        full_labels_layout.addWidget(HelpButton('If unchecked, only the address involved in a transaction will be in the exported "label" field.'))
        full_labels_layout.addStretch(1)
        vbox.addLayout(full_labels_layout)

        vbox.addWidget(QLabel(_("Wallet history will be exported to the file below.\n")))
        select_msg = _("Select the file that wallet history will be exported to.")
        file_vbox, filename_e, csv_button = filename_field(format_widget, self.window.config, self.file_path, select_msg, self.csv)
        vbox.addLayout(file_vbox)
        vbox.addStretch(1)

        def do_save_now():
            # save config in case the user has changed options before clicking the button
            self.csv = csv_button.isChecked()
            self.file_path = str(filename_e.text())
            self.save_config()
            self.save_history()
        save_now_button = QPushButton(_("Save history now"))
        save_now_button.clicked.connect(do_save_now)

        buttons_layout = close_button(d, 'OK')
        buttons_layout.addWidget(save_now_button)
        vbox.addLayout(buttons_layout)

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
            'csv_format': self.csv,
            'full_labels': self.full_labels
        }
        self.print_error('Saving config: {}'.format(options))
        self.wallet.storage.config.set_key_above_chain('auto_history_export', options, True)

    def save_history(self):
        if not self.window or not self.wallet: return
        lines = self.window.create_export_history(self.wallet, self.csv)

        # For stripping labels when full_labels is False.
        def minimize_label(label_text):
            if label_text[-4:] == '...]' and label_text[-13] == '[':
                label_text = label_text[:-14]
            if label_text.startswith(('>','<')) and is_address(label_text[1:]):
                label_text = label_text[1:]
            return label_text

        if not self.full_labels:
            # Strip labels.
            if self.csv:
                for line in lines:
                    line[2] = minimize_label(line[2])
            else:
                for d in lines[self.wallet.active_chain.code]:
                    d['label'] = minimize_label(d['label'])
        self.window.do_export_history(lines, self.file_path, self.csv, self.wallet.active_chain)
        self.print_error('Saved wallet history')

    @hook
    def load_wallet(self, wallet, window):
        self.wallet = wallet
        self.window = window
        options = wallet.storage.config.get_above_chain('auto_history_export', {})
        self.file_path = options.get('export_filename', os.path.expanduser('~/encompass-history.json'))
        self.csv = options.get('csv_format', False)
        self.full_labels = options.get('full_labels', True)

    @hook
    def receive_tx_callback(self, tx_hash, tx, tx_height):
        self.save_history()
