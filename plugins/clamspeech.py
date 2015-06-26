from PyQt4.QtGui import *

from chainkey.plugins import BasePlugin, hook
from chainkey.i18n import _


class Plugin(BasePlugin):

    @hook
    def transaction_dialog(self, d):
        clamspeech = getattr(d.tx, 'clamspeech', None)
        if not clamspeech:
            return
        form = d.layout()
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(_("ClamSpeech:")))
        speech_text = QTextEdit()
        speech_text.setReadOnly(True)
        speech_text.setMaximumHeight(100)
        speech_text.setText(clamspeech)
        speech_text.setFixedHeight(50)
        vbox.addWidget(speech_text)
        form.insertRow(form.rowCount() - 1, vbox)
