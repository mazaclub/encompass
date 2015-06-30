from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qt import Qt
import PyQt4.QtCore as QtCore

import os

from chainkey import util
from util import *

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
    gui_name = 'main_gui'
    theme_dir = os.path.join(util.data_dir(), gui_name)
    theme_paths.update(theme_dirs_from_prefix(theme_dir))
    return theme_paths


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

