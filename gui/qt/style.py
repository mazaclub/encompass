from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qt import Qt
import PyQt4.QtCore as QtCore

import os

from chainkey import util
from util import *

import theme_icons_rc

def IconButton(filename, parent=None):
    pixmap = QPixmap(filename)
    icon = QIcon(pixmap)
    return QPushButton(icon, "", parent)


def resize_line_edit_width(line_edit, text_input):
    metrics = QFontMetrics(qApp.font())
    # Create an extra character to add some space on the end
    text_input += "A"
    line_edit.setMinimumWidth(metrics.width(text_input))

def load_theme_name(theme_path):
    try:
        with open(os.path.join(theme_path, "name.cfg")) as name_cfg_file:
            return name_cfg_file.read().rstrip("\n").strip()
    except IOError:
        return None

def theme_dirs_from_prefix(prefix):
    if not os.path.exists(prefix):
        return []
    theme_paths = {}
    for potential_theme in os.listdir(prefix):
        theme_full_path = os.path.join(prefix, potential_theme)
        theme_css = os.path.join(theme_full_path, "style.css")
        if not os.path.exists(theme_css):
            continue
        theme_name = load_theme_name(theme_full_path)
        if theme_name is None:
            continue
        theme_paths[theme_name] = prefix, potential_theme
    return theme_paths

def load_theme_paths():
    theme_paths = {}
    theme_dir = os.path.join(util.data_dir(), 'themes')
    theme_paths.update(theme_dirs_from_prefix(theme_dir))
    return theme_paths

class Item(QWidget):
    """Allows stylesheets to affect items in views.

    See docs/theming.md for detailed information."""
    def __init__(self, role=None):
        super(Item, self).__init__()
        self.setProperty("role", role)

class MyTreeWidget(QTreeWidget):
    def __init__(self, parent):
        QTreeWidget.__init__(self, parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemActivated.connect(self.on_activated)

    def on_activated(self, item):
        if not item: return
        for i in range(0,self.viewport().height()/5):
            if self.itemAt(QPoint(0,i*5)) == item:
                break
        else:
            return
        for j in range(0,30):
            if self.itemAt(QPoint(0,i*5 + j)) != item:
                break
        self.emit(SIGNAL('customContextMenuRequested(const QPoint&)'), QPoint(50, i*5 + j - 1))

# See docs/theming.html
class MyStyleDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, role=None):
        """Initialize the delegate.

        role can be a string, or an int representing the number
        of columns the table has."""
        # roles define which view we're displaying (e.g. history, addresses)
        if role == 'history':
            self.column_types = ['', 'date', 'label', 'amount', 'balance']
        elif role == 'receive':
            self.column_types = ['address', 'message', 'amount']
        elif role == 'addresses':
            self.column_types = ['address', 'label', 'balance', 'tx_count']
        elif role == 'contacts':
            self.column_types = ['address', 'label', 'tx_count']
        elif role == 'invoices':
            self.column_types = ['requestor', 'memo', 'date', 'amount', 'status']
        elif role == 'chains':
            self.column_types = ['text_item', 'text_item', 'boolean', 'boolean']
        elif role == 'chains_verbose':
            self.column_types = ['text_item', 'text_item', 'boolean', 'boolean', 'boolean', 'text_item']
        # If an int is given, use the generic color for all columns.
        elif isinstance(role, int):
            self.column_types = ['text_item' for i in range(role)]
        else:
            self.column_types = []
        super(MyStyleDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        applied = self.apply_style(option, index, index.column())
        if applied:
            painter.save()

            # background
            painter.setPen(QPen(Qt.NoPen))
            if option.state & QStyle.State_Selected:
                painter.setBrush(option.palette.brush(QPalette.Highlight))
            else:
                painter.setBrush(option.palette.background())
            painter.drawRect(option.rect)

            # foreground
            if option.state & QStyle.State_Selected:
                painter.setPen(option.palette.brush(QPalette.HighlightedText).color())
            else:
                painter.setPen(QPen(option.palette.text().color()))
            painter.setFont(option.font)
            value = index.data(Qt.DisplayRole)
            if value.isValid():
                text = value.toString()
                painter.drawText(option.rect, Qt.AlignLeft, text)

            painter.restore()
        else:
            super(MyStyleDelegate, self).paint(painter, option, index)

    def apply_style(self, option, index, column):
        style_applied = False
        if self.column_types:
            col_type = self.column_types[column]
        data = index.data()

        # icon goes in this column
        if col_type == '':
            return style_applied

        if col_type in ['address', 'tx_count', 'date', 'balance', 'text_item']:
            txt = Item(col_type)
        elif col_type == 'amount':
            # There are two different rules for positive and negative amounts
            data, _ = data.toFloat()
            if data < 0:
                txt = Item('amount_negative')
            else:
                txt = Item('amount')
        elif col_type == 'label':
            # There are two different rules for default labels and labels
            default_label = False
            for prefix in ['<', '>', '(internal)']:
                if str(data.toString()).startswith(prefix):
                    default_label = True

            if default_label:
                txt = Item('label_default')
            else:
                txt = Item('label')
        elif col_type == 'boolean':
            if data in [True, False]:
                data = 'yes' if data == True else 'no'
            # "Yes" or "No"
            else:
                data = str(data.toString()).lower()
            txt = Item(data)
        else:
            txt = Item('text_item')

        # monospace columns
        if col_type in ['label', 'amount', 'balance', 'address', 'requestor']:
            txt.setFont(QFont(MONOSPACE_FONT))

        qApp.style().polish(txt)

        # http://pyqt.sourceforge.net/Docs/PyQt4/qpalette.html#ColorRole-enum

        # Text color
        if txt.palette().isBrushSet(QPalette.Active, QPalette.Text):
            style_applied = True
            option.palette.setBrush(QPalette.Text, txt.palette().foreground())

        # A general foreground color
        if txt.palette().isBrushSet(QPalette.Active, QPalette.WindowText):
            style_applied = True
            option.palette.setBrush(QPalette.WindowText, txt.palette().windowText())

        # A general background color
        if txt.palette().isBrushSet(QPalette.Active, QPalette.Window):
            style_applied = True
            option.palette.setBrush(QPalette.Window, txt.palette().window())

        # A background color
        if txt.palette().isBrushSet(QPalette.Active, QPalette.Base):
            style_applied = True
            option.palette.setBrush(QPalette.Base, txt.palette().base())

        option.font = txt.font()

        return style_applied



class Actuator:
    """Initialize the definitions relating to themes."""

    def __init__(self, main_window, is_lite=False):
        self.g = main_window
        self.gui_type = 'maingui_theme'
        self.is_lite = is_lite
        self.default_gui_theme = 'Default'
        self.theme_name = self.g.config.get_above_chain(self.gui_type, self.default_gui_theme)
        self.themes = load_theme_paths()
        self.load_theme()

    def load_theme(self):
        """Load theme retrieved from wallet file."""
        # No lite window stylesheets
        if self.is_lite: return
        try:
            theme_prefix, theme_path = self.themes[self.theme_name]
        except KeyError:
            util.print_error("Theme not found!", self.theme_name)
            return
        full_theme_path = "%s/%s/style.css" % (theme_prefix, theme_path)
        with open(full_theme_path) as style_file:
            qApp.setStyleSheet(style_file.read())

    def get_icon(self, name):
        use_backup = False
        current_theme = self.selected_theme()
        theme_dir = QDir(":theme/" + current_theme)
        if not theme_dir.exists(): use_backup = True
        if not theme_dir.exists(name): use_backup = True

        # Use default theme image if not found
        if use_backup:
            theme_dir = QDir(":theme/Default")
        return QIcon(theme_dir.filePath(name))

    def get_coin_icon(self, chaincode='BTC'):
        coin_icon_name = ''.join([ ":icons/coin_", chaincode.lower(), ".png" ])
        if not QFile(coin_icon_name).exists():
            coin_icon_name = ":icons/coin_btc.png"
        return QIcon(coin_icon_name)

    def theme_names(self):
        """Sort themes."""
        return sorted(self.themes.keys())

    def selected_theme(self):
        """Select theme."""
        return self.theme_name

    def change_theme(self, theme_name):
        """Change theme."""
        self.theme_name = theme_name
        self.g.config.set_key_above_chain(self.gui_type, theme_name)
        self.load_theme()
        self.g.main_window.theme_changed()

class ThemeDialog(QDialog):

    def __init__(self, parent):
        super(ThemeDialog, self).__init__(parent)
        self.parent = parent
        self.actuator = parent.actuator
        self.main_layout = vbox = QVBoxLayout()
        self.radio_group = radio_group = QButtonGroup()
        for theme_name in self.actuator.theme_names():
            radio = QRadioButton(theme_name)
            if theme_name == self.actuator.selected_theme():
                radio.setChecked(True)
            radio.toggled.connect(self.change_theme)
            radio_group.addButton(radio)
            vbox.addWidget(radio)
        vbox.addLayout(close_button(self))
        self.setLayout(vbox)

    def change_theme(self):
        radio = self.radio_group.checkedButton()
        theme_name = str(radio.text())
        self.actuator.change_theme(theme_name)
