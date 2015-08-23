import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import functools

from chainkey.i18n import _

import amountedit
from amountedit import BTCAmountEdit
import paytoedit
from paytoedit import PayToEdit
from util import HelpButton

class SendEdit(QObject):

    shortcut = pyqtSignal()
    textChanged = pyqtSignal()

    def __init__(self, parent):
        super(SendEdit, self).__init__(parent)
        self.parent = parent
        # list of 2-tuples: (widget, PayToEdit)
        self.payto_widgets = []

        self.shortcut_paytoedit = None
        self.shortcut_addr = ''

        self.payto_help = HelpButton(_('Recipient of the funds.') + '\n\n' + _('You may enter a coin address, a label from your list of contacts (a list of completions will be proposed), or an alias (email-like address that forwards to a coin address)'))

        self.amount_help = HelpButton(_('Amount to be sent.') + '\n\n' \
                                      + _('The amount will be displayed in red if you do not have enough funds in your wallet. Note that if you have frozen some of your addresses, the available funds will be lower than your total balance.') \
                                      + '\n\n' + _('Keyboard shortcut: type "!" to send all your coins.'))

        self.scroller = QScrollArea()
        self.scroller.setEnabled(True)
        self.scroller.setWidgetResizable(True)
        self.scroller.setMinimumSize(100, 125)
        self.scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_widget = QWidget()
        self.scroll_widget.setProperty("scrollArea", True)
        self.vbox = QVBoxLayout()
        self.scrolling_layout = QVBoxLayout()

        self.num_paytoedits = 10

        # scroll area
        self.scroll_widget.setLayout(self.vbox)
        self.scroller.setWidget(self.scroll_widget)
        self.scrolling_layout.addWidget(self.scroller)

        self.create_paytoedits()
        self.active_paytoedit = self.payto_widgets[0][1]
        self.vbox.addStretch(1)

    def create_paytoedits(self):
        for i in range(self.num_paytoedits):
            w = self.add_paytoedit()
        self.set_visible_outputs(1)

    def add_paytoedit(self):
        w = QWidget()
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnMinimumWidth(1,300)
        grid.setColumnStretch(1,2)

        pay_edit = PayToEdit(self.parent, BTCAmountEdit(self.parent.get_decimal_point))

        self.payto_widgets.append( (w, pay_edit) )
        current_widget_index = len(self.payto_widgets) - 1

        completer = QCompleter()
        completer.setCaseSensitivity(False)
        pay_edit.setCompleter(completer)
        completer.setModel(self.parent.completions)

        if current_widget_index == 0:
            grid.addWidget(QLabel(_('Pay to')), 0, 0, 1, 1)
            grid.addWidget(QLabel(_('Amount')), 0, 3, 1, 1)

            grid.addWidget(self.payto_help, 0, 1)
            grid.addWidget(self.amount_help, 0, 4)

        grid.addWidget(pay_edit, 1, 0, 1, 3)

        grid.addWidget(pay_edit.amount_edit, 1, 3, 1, 3)

        w.setLayout(grid)
        self.vbox.addWidget(w)

        pay_edit.amount_edit.shortcut.connect( functools.partial(self.on_shortcut, current_widget_index) )
        pay_edit.textChanged.connect( functools.partial(self.on_textChanged, current_widget_index) )
        pay_edit.amount_edit.textEdited.connect( functools.partial(self.on_textChanged, current_widget_index) )

        return w

    def set_visible_outputs(self, num):
        for i, (w, pay_edit) in enumerate(self.payto_widgets):
            if i < num:
                w.show()
                # QR button is hidden for now
                pay_edit.button.hide()
            else:
                w.hide()
                self.clear_paytoedit(i)

    def set_not_enough_funds(self, enough):
        for w, pay_edit in self.payto_widgets:
            pay_edit.amount_edit.setProperty('notEnoughFunds', enough)
            self.parent.recompute_style(pay_edit.amount_edit)

    def get_layout(self):
        return self.scrolling_layout

    def on_shortcut(self, index):
        pay_edit = self.payto_widgets[index][1]
        self.shortcut_paytoedit = pay_edit
        self.shortcut_addr = pay_edit.payto_address
        self.shortcut.emit()

    def on_textChanged(self, index):
        pay_edit = self.payto_widgets[index][1]
        self.active_paytoedit = pay_edit
        self.textChanged.emit()

    def get_errors(self):
        errors = []
        for w, pay_edit in self.payto_widgets:
            errors.extend(pay_edit.get_errors())
        return errors

    def get_outputs(self):
        outputs = []
        for w, pay_edit in self.payto_widgets:
            outputs.extend(pay_edit.get_outputs())
        outputs = filter(lambda x: x[2] is not None, outputs)
        return outputs

    def get_amount_sum(self):
        amounts = []
        for w, pay_edit in self.payto_widgets:
            a = pay_edit.getAmount()
            if a is not None:
                amounts.append(a)
        return sum(amounts)

    def setFrozen(self, isFrozen, index=None):
        # freeze the active one
        if index == -1:
            pay_edit = self.active_paytoedit
            pay_edit.setFrozen(isFrozen)
            pay_edit.amount_edit.setFrozen(isFrozen)
        # freeze all of them
        elif index is None:
            for w, pay_edit in self.payto_widgets:
                pay_edit.setFrozen(isFrozen)
                pay_edit.amount_edit.setFrozen(isFrozen)
        else:
            w, pay_edit = self.payto_widgets[index]
            pay_edit.setFrozen(isFrozen)
            pay_edit.amount_edit.setFrozen(isFrozen)

    def setText(self, text, index=None):
        # set the active PayToEdit's text
        if index is None:
            self.active_paytoedit.setText(text)
        else:
            w, pay_edit = self.payto_widgets[index]
            pay_edit.setText(text)

    def setAmount(self, text, index=None):
        # set the active PayToEdit's amount edit text
        if index is None:
            self.active_paytoedit.amount_edit.setText(text)
        else:
            w, pay_edit = self.payto_widgets[index]
            pay_edit.amount_edit.setText(text)

    def set_is_pr(self, is_pr, index=None):
        if index is None:
            self.active_paytoedit.is_pr = is_pr
        else:
            w, pay_edit = self.payto_widgets[index]
            pay_edit.is_pr = is_pr


    def clear(self):
        for i in range(len(self.payto_widgets)):
            self.clear_paytoedit(i)

    def clear_paytoedit(self, index):
        if index >= len(self.payto_widgets):
            return
        pay_edit = self.payto_widgets[index][1]
        pay_edit.is_pr = False
        for e in [pay_edit, pay_edit.amount_edit]:
            e.setText('')
            e.setFrozen(False)
        pay_edit.button.hide()
