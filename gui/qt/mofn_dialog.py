from PyQt4.QtGui import *
from PyQt4.QtCore import *
from chainkey.i18n import _
from chainkey.bitcoin import is_standard_mofn, get_max_n

from util import ok_cancel_buttons2

class Select_MN_Dialog(QDialog):
    '''Dialog for selecting M and N for multisig wallets'''

    def __init__(self):
        QDialog.__init__(self)
        self.setMinimumSize(200, 100)
        self.setWindowTitle('M-of-N Wallet')
        self.main_layout = vb = QVBoxLayout(self)
        mofn_explanation = QLabel(_("Select M (minimum number of cosigner signatures) and N (total cosigners)"))
        vb.addWidget(mofn_explanation)

        # choices
        self.m_list = map(lambda x: QString(str(x)), [1,2,3,4])
        self.n_list = []
        mnbox = QHBoxLayout()
        self.combobox_m = cb_m = QComboBox()
        self.combobox_n = cb_n = QComboBox()
        cb_m.addItems(self.m_list)
        cb_n.setEnabled(False)
        # add choices to layout
        mnbox.addWidget(cb_m)
        mnbox.addWidget(QLabel(_("of")))
        mnbox.addWidget(cb_n)
        vb.addLayout(mnbox)
        # connect choice combo box
        cb_m.currentIndexChanged.connect(self.on_m_changed)
        cb_n.currentIndexChanged.connect(self.on_n_changed)

        # ok and cancel buttons
        self.ok_cancel, self.accept_button = okc, accept_b = ok_cancel_buttons2(self)
        accept_b.setEnabled(False)

        vb.addLayout(okc)

    def on_m_changed(self):
        self.combobox_n.clear()
        m = self.combobox_m.currentText()
        m, ok = m.toInt()
        if not ok: return
        # create n list
        max_n = get_max_n(m)
        # If m is 1, we can't have n being 1 because that's 1-of-1
        # This only affects the range of the n_list, not the m_list
        if m == 1: m = 2
        self.n_list = map(lambda x: QString(str(x)), range(m, max_n+1))
        self.combobox_n.addItems(self.n_list)
        self.combobox_n.setEnabled(True)

    def on_n_changed(self):
        m = self.combobox_m.currentText()
        m, ok = m.toInt()
        if not ok: return
        n = self.combobox_n.currentText()
        n, ok = n.toInt()
        if not ok: return
        if is_standard_mofn(m, n):
            self.accept_button.setEnabled(True)

def run_select_mn_dialog():
    self = Select_MN_Dialog()
    self.combobox_m.currentIndexChanged.emit(0)
    if not self.exec_():
        return None, None
    m = self.combobox_m.currentText()
    m, ok = m.toInt()
    if not ok: return None, None
    n = self.combobox_n.currentText()
    n, ok = n.toInt()
    if not ok: return None, None

    return m, n
