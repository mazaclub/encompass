from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chainkey.i18n import _

import style
from util import HelpButton, close_button
from amountedit import BTCAmountEdit
from currency_dialog import HideCurrenciesDialog, FavoriteCurrenciesDialog

class SettingsRow(object):
    """There are roles for each type of option:

    'toggle': Just a CheckBox and HelpButton
    'combobox': A label, a ComboBox (or similar widget), and a HelpButton
    'full': A label, the value, a PushButton, and a HelpButton
    """
    def __init__(self, parent, role, widgets):
        self.role = role
        self.widgets = widgets

    def add_to_layout(self, grid):
        """Add our widgets to grid.

        This handles the alignment of widgets depending on their nature.
        """
        widgets = self.widgets
        row = grid.rowCount()
        # Checkbox text spans 3 columns
        if self.role == 'toggle':
            grid.addWidget(widgets[0], row, 0, 1, 3)
            grid.addWidget(widgets[1], row, 3, 1, 1, alignment=Qt.AlignRight)
        elif self.role == 'combobox':
            grid.addWidget(widgets[0], row, 0, 1, 1, alignment=Qt.AlignLeft)
            grid.addWidget(widgets[1], row, 1, 1, 1)
            grid.addWidget(widgets[2], row, 3, 1, 1, alignment=Qt.AlignRight)
        # 'full' or anything else
        else:
            for i, w in enumerate(widgets):
                if i == len(widgets):
                    grid.addWidget(w, row, i, 1, 1, alignment=Qt.AlignRight)
                else:
                    grid.addWidget(w, row, i, 1, 1)

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        self.gui = gui = parent
        self.config = gui.config
        self.actuator = gui.actuator
        self.active_chain = gui.active_chain

        self.setWindowTitle(_('Encompass Settings'))
        self.setModal(1)
        self.setMinimumWidth(500)
        # There are tabs for each category of settings.
        self.pages_tabs = QTabWidget()

        # Global options
        global_rows = self.create_global_options()
        global_options_grid = QGridLayout()
        for r in global_rows:
            r.add_to_layout(global_options_grid)

        global_description = _("These settings are not limited to any coin.")
        global_widget = self.create_page_widget(global_description, global_options_grid)
        self.pages_tabs.addTab(global_widget, _('Global'))

        # Per-chain options
        chain_rows = self.create_chain_options()
        chain_options_grid = QGridLayout()
        for r in chain_rows:
            r.add_to_layout(chain_options_grid)

        chain_description = _("These settings only affect") + " {}.".format(self.active_chain.coin_name)
        chain_widget = self.create_page_widget(chain_description, chain_options_grid)
        self.pages_tabs.addTab(chain_widget, self.actuator.get_coin_icon(self.active_chain.code), self.active_chain.coin_name)

        pages_explanation = QLabel(_('Select a category of settings below:'))
        pages_explanation.setWordWrap(True)

        vbox = QVBoxLayout()
        vbox.addWidget(pages_explanation)
        vbox.addWidget(self.pages_tabs, stretch=1)
        vbox.addLayout(close_button(self))

        self.setLayout(vbox)

    def create_page_widget(self, description, grid):
        w = QWidget()
        vbox = QVBoxLayout()
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignHCenter)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        vbox.addWidget(desc_label)
        vbox.addWidget(separator)
        vbox.addLayout(grid, stretch=1)
        w.setLayout(vbox)
        return w

    def create_global_options(self):
        rows = []

        # Language #
        lang_label = QLabel(_('Language') + ':')
        lang_help = HelpButton(_('Select which language is used in the GUI (after restart).'))
        lang_combo = QComboBox()
        from chainkey.i18n import languages
        lang_combo.addItems(languages.values())
        try:
            index = languages.keys().index(self.config.get_above_chain("language",''))
        except Exception:
            index = 0
        lang_combo.setCurrentIndex(index)
        if not self.config.is_modifiable('language'):
            for w in [lang_combo, lang_label]: w.setEnabled(False)
        def on_lang(x):
            lang_request = languages.keys()[lang_combo.currentIndex()]
            if lang_request != self.config.get_above_chain('language'):
                self.config.set_key_above_chain("language", lang_request, True)
                self.gui.need_restart = True
        lang_combo.currentIndexChanged.connect(on_lang)
        rows.append(SettingsRow(self,'combobox', (lang_label, lang_combo, lang_help)))

        # Theme #
        current_theme = self.actuator.selected_theme()
        theme_label = QLabel(_('Theme:'))
        theme_value = QLabel(_(current_theme))
        theme_button = QPushButton(_('Change Theme'))
        theme_help = HelpButton(_('Themes change how Encompass looks.'))
        def on_theme_button():
            style.ThemeDialog(self).exec_()
            current_theme = self.actuator.selected_theme()
            theme_value.setText(_(current_theme))
        theme_button.clicked.connect(on_theme_button)
        rows.append(SettingsRow(self,'full', (theme_label, theme_value, theme_button, theme_help)))

        # Favorite chains #
        fav_chains_list = map(lambda x: x.encode('ascii', 'ignore'), self.config.get_above_chain('favorite_chains', []))
        # Maximum of three favorite chains
        if len(fav_chains_list) > 3:
            fav_chains_list = fav_chains_list[:3]
            self.config.set_key_above_chain('favorite_chains', fav_chains_list)
        # Replace an empty list with the string 'None'
        if not fav_chains_list: fav_chains_list = 'None'
        fav_chains_list = str(fav_chains_list).replace("'", "")
        favs_label = QLabel(_( 'Favorite coins:'))
        favs_value = QLabel(fav_chains_list)
        favs_button = QPushButton(_('Change Favorites'))
        favs_help = HelpButton(_('Favorite coins are in the status bar\'s coin menu, and appear before others in the currency selection window.'))
        def do_fav():
            FavoriteCurrenciesDialog(self).exec_()
            fav_chains_list = map(lambda x: x.encode('ascii', 'ignore'), self.config.get_above_chain('favorite_chains', []))
            if not fav_chains_list: fav_chains_list = 'None'
            fav_chains_list = str(fav_chains_list).replace("'", "")
            favs_value.setText(fav_chains_list)
            # update the coin menu
            self.gui.update_status()

        favs_button.clicked.connect(do_fav)
        rows.append(SettingsRow(self,'full', (favs_label, favs_value, favs_button, favs_help)))

        # Hidden Chains #
        hidden_chains_list = self.config.get_above_chain('hide_chains', [])
        hidden_chains_number = len(hidden_chains_list)
        hiddens_label = QLabel(_('Hidden coins:'))
        hiddens_value = QLabel(str(hidden_chains_number))
        hiddens_button = QPushButton(_('Change Hidden Coins'))
        hiddens_help = HelpButton(_('Hidden coins do not appear in the currency selection window.'))
        def do_hiddens():
            HideCurrenciesDialog(self).exec_()
            hidden_chains_list = self.config.get_above_chain('hide_chains', [])
            hiddens_value.setText(str( len(hidden_chains_list) ))
        hiddens_button.clicked.connect(do_hiddens)
        rows.append(SettingsRow(self,'full', (hiddens_label, hiddens_value, hiddens_button, hiddens_help)))

        # QR Device #
        from chainkey import qrscanner
        system_cameras = qrscanner._find_system_cameras()
        qr_combo = QComboBox()
        qr_combo.addItem("Default","default")
        for camera, device in system_cameras.items():
            qr_combo.addItem(camera, device)
        #combo.addItem("Manually specify a device", config.get("video_device"))
        index = qr_combo.findData(self.config.get_above_chain("video_device"))
        qr_combo.setCurrentIndex(index)
        qr_label = QLabel(_('Video Device') + ':')
        qr_combo.setEnabled(qrscanner.zbar is not None)
        qr_help = HelpButton(_("Install the zbar package to enable this.\nOn linux, type: 'apt-get install python-zbar'"))
        on_video_device = lambda x: self.config.set_key_above_chain("video_device", str(qr_combo.itemData(x).toString()), True)
        qr_combo.currentIndexChanged.connect(on_video_device)
        rows.append(SettingsRow(self,'combobox', (qr_label, qr_combo, qr_help)))

        # Currency Dialog Verbosity #
        verbose_currency_dialog = QCheckBox(_('Show verbose info in Change Currency window'))
        verbose_currency_dialog.setChecked(self.config.get_above_chain('verbose_currency_dialog', False))
        verbose_currency_dialog.stateChanged.connect(lambda x: self.config.set_key_above_chain('verbose_currency_dialog', verbose_currency_dialog.isChecked()))
        verbose_currency_dialog_help = HelpButton(_('Show verbose information about currencies, such as the number of default servers.'))
        rows.append(SettingsRow(self,'toggle', (verbose_currency_dialog, verbose_currency_dialog_help)))

        # Open Default Wallet on Launch #
        use_def_wallet_cb = QCheckBox(_('Open default_wallet on wallet start'))
        use_def_wallet_cb.setChecked(self.config.get_above_chain('use_default_wallet', True))
        use_def_wallet_cb.stateChanged.connect(lambda x: self.config.set_key_above_chain('use_default_wallet', use_def_wallet_cb.isChecked()))
        use_def_wallet_help = HelpButton(_('Open default_wallet when Encompass starts. Otherwise, open the last wallet that was open.'))
        rows.append(SettingsRow(self,'toggle', (use_def_wallet_cb, use_def_wallet_help)))

        return rows

    def create_chain_options(self):
        rows = []
        gui = self.gui

        # Number of Zeroes
        nz_label = QLabel(_('Zeros after decimal point') + ':')
        nz_help = HelpButton(_('Number of zeros displayed after the decimal point. For example, if this is set to 2, "1." will be displayed as "1.00"'))
        nz = QSpinBox()
        nz.setMinimum(0)
        nz.setMaximum(gui.decimal_point)
        nz.setValue(gui.num_zeros)
        if not self.config.is_modifiable('num_zeros'):
            for w in [nz, nz_label]: w.setEnabled(False)
        def on_nz():
            value = nz.value()
            if gui.num_zeros != value:
                gui.num_zeros = value
                self.config.set_key('num_zeros', value, True)
                gui.update_history_tab()
                gui.update_address_tab()
        nz.valueChanged.connect(on_nz)
        rows.append(SettingsRow(self,'combobox', (nz_label, nz, nz_help)))

        # Fee #
        fee_label = QLabel(_('Transaction fee per kb') + ':')
        fee_help = HelpButton(_('Fee per kilobyte of transaction.') + '\n' \
                              + _('Recommended value') + ': ' + gui.format_amount(gui.active_chain.RECOMMENDED_FEE) + ' ' + gui.base_unit())

        fee_e = BTCAmountEdit(gui.get_decimal_point)
        fee_e.setAmount(gui.wallet.fee_per_kb)
        if not self.config.is_modifiable('fee_per_kb'):
            for w in [fee_e, fee_label]: w.setEnabled(False)
        def on_fee():
            fee = fee_e.get_amount()
            gui.wallet.set_fee(fee)
        fee_e.editingFinished.connect(on_fee)
        rows.append(SettingsRow(self,'combobox', (fee_label, fee_e, fee_help)))

        # Base Unit #
        units = gui.base_units.keys()
        unit_label = QLabel(_('Base unit') + ':')
        unit_combo = QComboBox()
        unit_combo.addItems(units)
        unit_combo.setCurrentIndex(units.index(gui.base_unit()))
        msg = _('Base unit of your wallet.')\
              + '\n1BTC=1000mBTC.\n' \
              + _(' These settings affects the fields in the Send tab')+' '
        unit_help = HelpButton(msg)
        def on_unit(x):
            unit_result = units[unit_combo.currentIndex()]
            if gui.base_unit() == unit_result:
                return
            gui.decimal_point = gui.base_units[unit_result]
            self.config.set_key('decimal_point', gui.decimal_point, True)
            gui.update_history_tab()
            gui.update_receive_tab()
            gui.update_address_tab()
            gui.update_invoices_tab()
            fee_e.setAmount(gui.wallet.fee_per_kb)
            gui.update_status()
        unit_combo.currentIndexChanged.connect(on_unit)
        rows.append(SettingsRow(self,'combobox', (unit_label, unit_combo, unit_help)))

        # Block Explorers #
        block_explorers = gui.block_explorers.keys()
        block_ex_label = QLabel(_('Online Block Explorer') + ':')
        block_ex_combo = QComboBox()
        block_ex_combo.addItems(block_explorers)
        block_ex_combo.setCurrentIndex(block_explorers.index(self.config.get('block_explorer', block_explorers[0])))
        block_ex_help = HelpButton(_('Choose which online block explorer to use for functions that open a web browser'))
        def on_be(x):
            be_result = block_explorers[block_ex_combo.currentIndex()]
            self.config.set_key('block_explorer', be_result, True)
        block_ex_combo.currentIndexChanged.connect(on_be)
        rows.append(SettingsRow(self,'combobox', (block_ex_label, block_ex_combo, block_ex_help)))

        # Use Change Addresses #
        usechange_cb = QCheckBox(_('Use change addresses'))
        usechange_cb.setChecked(gui.wallet.use_change)
        usechange_help = HelpButton(_('Using change addresses makes it more difficult for other people to track your transactions.'))
        if not self.config.is_modifiable('use_change'): usechange_cb.setEnabled(False)
        def on_usechange(x):
            usechange_result = x == Qt.Checked
            if gui.wallet.use_change != usechange_result:
                gui.wallet.use_change = usechange_result
                gui.wallet.storage.put('use_change', gui.wallet.use_change)
        usechange_cb.stateChanged.connect(on_usechange)
        rows.append(SettingsRow(self,'toggle', (usechange_cb, usechange_help)))

        # Show Tx Before Broadcast #
        showtx_cb = QCheckBox(_('Show transaction before broadcast'))
        showtx_cb.setChecked(self.config.get('show_before_broadcast', False))
        showtx_cb.stateChanged.connect(lambda x: self.config.set_key('show_before_broadcast', showtx_cb.isChecked()))
        showtx_help = HelpButton(_('Display the details of your transactions before broadcasting it.'))
        rows.append(SettingsRow(self,'toggle', (showtx_cb, showtx_help)))

        # Set Fees Manually #
        can_edit_fees_cb = QCheckBox(_('Set transaction fees manually'))
        can_edit_fees_cb.setChecked(self.config.get('can_edit_fees', False))
        def on_editfees(x):
            self.config.set_key('can_edit_fees', x == Qt.Checked)
            gui.update_fee_edit()
        can_edit_fees_cb.stateChanged.connect(on_editfees)
        can_edit_fees_help = HelpButton(_('This option lets you edit fees in the send tab.'))
        rows.append(SettingsRow(self,'toggle', (can_edit_fees_cb, can_edit_fees_help)))

        return rows
