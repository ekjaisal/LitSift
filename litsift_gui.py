import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog,
                               QLabel, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QScrollArea, QAbstractItemView, QDialog, QTextBrowser,
                               QCheckBox, QMenu, QTableView, QMessageBox)
from PySide6.QtGui import (QIcon, QFont, QColor, QPalette, QDesktopServices, QFontDatabase,
                           QAction, QTextCursor)
from PySide6.QtCore import (Qt, QThread, Signal, QUrl, QTimer, QSortFilterProxyModel, QAbstractTableModel, QItemSelection, QItemSelectionModel)
import asyncio
from litsift_core import search_semantic_scholar, save_to_file, check_internet_connection
from functools import reduce
from functools import cmp_to_key
import re
import os
import json

def load_custom_fonts():
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    for font_file in os.listdir(font_dir):
        if font_file.endswith('.ttf'):
            font_path = os.path.join(font_dir, font_file)
            QFontDatabase.addApplicationFont(font_path)

LIGHT_THEME = {
    "Window": "#f5f3ef",
    "WindowText": "#141414",
    "Button": "#f5f3ef",
    "ButtonText": "#141414",
    "Base": "#ffffff",
    "AlternateBase": "#e0e0e0",
    "ToolTipBase": "#ffffff",
    "ToolTipText": "#141414",
    "Text": "#141414",
    "PlaceholderText": "#808080",
    "Highlight": "#4a90e2",
    "HighlightedText": "#ffffff"
}

DARK_THEME = {
    "Window": "#000000",
    "WindowText": "#ffffff",
    "Button": "#1a1a1a",
    "ButtonText": "#ffffff",
    "Base": "#121212",
    "AlternateBase": "#1f1f1f",
    "ToolTipBase": "#1a1a1a",
    "ToolTipText": "#ffffff",
    "Text": "#ffffff",
    "PlaceholderText": "#A0A0A0",
    "Highlight": "#4a90e2",
    "HighlightedText": "#ffffff"
}
  
class SearchWorker(QThread):
    finished = Signal(list)
    progress = Signal(int, str)
    error = Signal(str)

    def __init__(self, query, max_results):
        super().__init__()
        self.query = query
        self.max_results = max_results

    def run(self):
        try:
            if not check_internet_connection():
                self.error.emit("No internet connection. Please check your network and try again.")
                return
            papers = asyncio.run(search_semantic_scholar(self.query, self.max_results, self.update_progress))
            self.progress.emit(100, "Search completed")
            self.finished.emit(papers)
        except Exception as e:
            self.error.emit(str(e))

    def update_progress(self, value, message):
        self.progress.emit(value, message)

class PapersModel(QAbstractTableModel):
    def __init__(self, papers=None):
        super().__init__()
        self.papers = papers or []
        self.headers = ["Title", "Authors", "Year", "Citations", "Influential Citations", "S2 TLDR", "Abstract", "Publication", "DOI", "PDF URL"]
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder

    def rowCount(self, parent=None):
        return len(self.papers)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            paper = self.papers[index.row()]
            column = index.column()
            if column == 0:
                return paper.get("Title", "")
            elif column == 1:
                return paper.get("Authors", "")
            elif column == 2:
                return str(paper.get("Year") or "")
            elif column == 3:
                return str(paper.get("Citations") or "")
            elif column == 4:
                return str(paper.get("Influential Citations") or "")
            elif column == 5:
                return paper.get("S2 TLDR", "")
            elif column == 6:
                return paper.get("Abstract", "")
            elif column == 7:
                return paper.get("Publication", "")
            elif column == 8:
                return paper.get("DOI", "")
            elif column == 9:
                return paper.get("PDF URL", "")
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def setPapers(self, papers):
        self.beginResetModel()
        self.papers = papers
        self.endResetModel()

    def clear_data(self):
        self.beginResetModel()
        self.papers = []
        self.endResetModel()

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self.sort_column = column
        self.sort_order = order

        def compare_items(item1, item2):
            value1 = self.get_sort_value(item1, column)
            value2 = self.get_sort_value(item2, column)
            
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return (value1 > value2) - (value1 < value2)
            elif isinstance(value1, str) and isinstance(value2, str):
                return (value1.lower() > value2.lower()) - (value1.lower() < value2.lower())
            else:
                return 0

        self.papers.sort(key=cmp_to_key(compare_items), reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def get_sort_value(self, item, column):
        if column == 0:
            return item.get("Title", "")
        elif column == 1:
            return item.get("Authors", "")
        elif column == 2:
            return int(item.get("Year") or 0)
        elif column == 3:
            return int(item.get("Citations") or 0)
        elif column == 4:
            return int(item.get("Influential Citations") or 0)
        elif column == 5:
            return item.get("S2 TLDR", "")
        elif column == 6:
            return item.get("Abstract", "")
        elif column == 7:
            return item.get("Publication", "")
        elif column == 8:
            return item.get("DOI", "")
        elif column == 9:
            return item.get("PDF URL", "")
        return ""

class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_selected = False

    def selectionCommand(self, index, event):
        if self.isRowHidden(index.row()):
            return QItemSelectionModel.NoUpdate
        return super().selectionCommand(index, event)

    def setSelection(self, rect, command):
        selection = QItemSelection()
        top_left = self.indexAt(rect.topLeft())
        bottom_right = self.indexAt(rect.bottomRight())
        
        start_row = min(top_left.row(), bottom_right.row())
        end_row = max(top_left.row(), bottom_right.row())
        
        for row in range(start_row, end_row + 1):
            if not self.isRowHidden(row):
                left = self.model().index(row, 0)
                right = self.model().index(row, self.model().columnCount() - 1)
                selection.select(left, right)
        
        self.selectionModel().select(selection, command)

    def selectAll(self):
        selection = QItemSelection()
        for row in range(self.model().rowCount()):
            if not self.isRowHidden(row):
                left = self.model().index(row, 0)
                right = self.model().index(row, self.model().columnCount() - 1)
                selection.select(left, right)
        self.selectionModel().select(selection, QItemSelectionModel.Select)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            if self.all_selected:
                self.clearSelection()
                self.all_selected = False
            else:
                self.selectAll()
                self.all_selected = True
            event.accept()
        else:
            super().keyPressEvent(event)

class BooleanExpression:
    def __init__(self, type, value=None, left=None, right=None):
        self.type = type
        self.value = value
        self.left = left
        self.right = right
        
class BooleanExpressionParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        if not self.tokens:
            return BooleanExpression('TERM', value='')
        return self.parse_expression()

    def parse_expression(self):
        expr = self.parse_term()
        while self.current < len(self.tokens) and self.tokens[self.current].upper() in ('AND', 'OR'):
            op = self.tokens[self.current].upper()
            self.current += 1
            right = self.parse_term()
            expr = BooleanExpression(op, left=expr, right=right)
        return expr

    def parse_term(self):
        if self.current >= len(self.tokens):
            return BooleanExpression('TERM', value='')

        token = self.tokens[self.current]
        self.current += 1

        if isinstance(token, tuple):
            return BooleanExpression('FIELD', value=token)
        elif token.upper() == 'NOT':
            expr = self.parse_term()
            return BooleanExpression('NOT', right=expr)
        elif token == '(':
            expr = self.parse_expression()
            if self.current < len(self.tokens) and self.tokens[self.current] == ')':
                self.current += 1
                return expr
            else:
                return BooleanExpression('TERM', value='')
        else:
            return BooleanExpression('TERM', value=token)

class CustomTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu(event.pos())
        cursor = self.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            search_action = QAction("Search on Web", self)
            search_action.triggered.connect(lambda: self.search_on_web(selected_text))
            menu.addSeparator()
            menu.addAction(search_action)
        
        menu.exec(event.globalPos())

    def search_on_web(self, text):
        url = QUrl(f"https://www.google.com/search?q={text}")
        QDesktopServices.openUrl(url)

class PaperDetailsDialog(QDialog):
    def __init__(self, paper, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Document Details")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        details = f"""
        <h3>{paper['Title']}</h3>
        <p><strong><i>Authors</i>:</strong> {paper['Authors'] or "Not Available"}</p>
        <p><strong><i>Year</i>:</strong> {paper['Year'] or "Not Available"}</p>
        <p><strong><i>Citations</i>:</strong> {paper['Citations']}</p>
        <p><strong><i>Influential Citations</i>:</strong> {paper['Influential Citations']}</p>
        <p><strong><i>TL;DR</i>:</strong> {paper['S2 TLDR'] or "Not Available"}</p>
        <p><strong><i>Abstract</i>:</strong> {paper['Abstract'] or "Not Available"}</p>
        <p><strong><i>Publication</i>:</strong> {paper['Publication'] or "Not Available"}</p>
        <p><strong><i>DOI</i>:</strong> {paper['DOI'] or "Not Available"}</p>
        <p><strong><i>Open Access PDF</i>:</strong> <a href="{paper['PDF URL']}">{paper['PDF URL'] or "Not Available"}</a></p>
        """
        text_browser = CustomTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(details)
        layout.addWidget(text_browser)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        if isinstance(parent, LitSiftGUI):
            parent.apply_dialog_theme(self)

class ClickableURLItem(QTableWidgetItem):
    def __init__(self, url):
        super().__init__(url)
        self.url = url
            
class LitSiftGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        app.setFont(QFont("Roboto", 10))
        self.setWindowTitle("LitSift")
        self.setWindowIcon(QIcon("LitSift.ico"))
        self.setWindowState(Qt.WindowMaximized)
        self.resize(1200, 600)

        QApplication.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f5f3ef"))
        palette.setColor(QPalette.WindowText, QColor("#141414"))
        palette.setColor(QPalette.Button, QColor("#f5f3ef"))
        palette.setColor(QPalette.ButtonText, QColor("#141414"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#e0e0e0"))
        palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
        palette.setColor(QPalette.ToolTipText, QColor("#141414"))
        palette.setColor(QPalette.Text, QColor("#141414"))
        palette.setColor(QPalette.Highlight, QColor("#4a90e2"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        self.setPalette(palette)

        mainwidget = QWidget(self)
        self.setCentralWidget(mainwidget)
        layout = QVBoxLayout(mainwidget)

        welcomelabel = QLabel("LitSift")
        welcomelabel.setAlignment(Qt.AlignCenter)
        welcomelabel.setFont(QFont("Roboto", 24, QFont.Bold))
        layout.addWidget(welcomelabel)

        subtitlelabel = QLabel("Seamlessly search, sift, and export results from Semantic Scholar to BibTeX/CSV")
        subtitlelabel.setAlignment(Qt.AlignCenter)
        subtitlelabel.setFont(QFont("Roboto", 10))
        layout.addWidget(subtitlelabel)

        querylayout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query")
        self.query_input.setFont(QFont("Roboto", 10))
        self.query_input.returnPressed.connect(self.handle_return_pressed)
        querylayout.addWidget(self.query_input)

        self.max_results_input = QSpinBox()
        self.max_results_input.setRange(1, 1000)
        self.max_results_input.setValue(100)
        self.max_results_input.setFont(QFont("Roboto", 10))
        querylayout.addWidget(QLabel("Max. results (up to 1000):"))
        querylayout.addWidget(self.max_results_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_search)
        self.search_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.search_button)

        self.save_button = QPushButton("Save Preview")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        self.save_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.save_button)

        self.save_selected_button = QPushButton("Save Selected")
        self.save_selected_button.clicked.connect(self.save_selected_results)
        self.save_selected_button.setEnabled(False)
        self.save_selected_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.save_selected_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_litsift)
        self.reset_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.reset_button)
        
        layout.addLayout(querylayout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Roboto", 10))

        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setFont(QFont("Roboto", 10))
        self.tabs.addTab(self.results_display, "Log")

        previewwidget = QWidget()
        previewlayout = QVBoxLayout(previewwidget)

        search_within_layout = QHBoxLayout()
        searchwithinlabel = QLabel("Search within results:")
        searchwithinlabel.setFont(QFont("Roboto", 10))
        search_within_layout.addWidget(searchwithinlabel)
        self.search_within_input = QLineEdit()
        self.search_within_input.setPlaceholderText("Enter terms to filter results (see tips for better sifting)")
        self.search_within_input.setFont(QFont("Roboto", 10))
        self.search_within_input.textChanged.connect(self.filter_results)
        search_within_layout.addWidget(self.search_within_input)
        previewlayout.addLayout(search_within_layout)

        self.preview_table = CustomTableView()
        self.preview_table.setFont(QFont("Roboto", 10))
        self.papers_model = PapersModel()
        self.preview_table.setModel(self.papers_model)

        self.preview_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.preview_table.setColumnWidth(0, 280)
        self.preview_table.setColumnWidth(1, 130)
        self.preview_table.setColumnWidth(2, 50)
        self.preview_table.setColumnWidth(3, 70)
        self.preview_table.setColumnWidth(4, 130)
        self.preview_table.setColumnWidth(5, 130)
        self.preview_table.setColumnWidth(6, 130)
        self.preview_table.setColumnWidth(7, 130)
        self.preview_table.setColumnWidth(8, 95)
        self.preview_table.setColumnWidth(9, 95)

        self.preview_table.selectionModel().selectionChanged.connect(self.handle_selection_change)
        self.preview_table.setSortingEnabled(True)
        previewlayout.addWidget(self.preview_table)

        self.tabs.addTab(previewwidget, "Preview and Sift Results")
        layout.addWidget(self.tabs)
        
        self.show_selected_checkbox = QCheckBox("Show only selected")
        self.show_selected_checkbox.setFont(QFont("Roboto", 10))
        self.show_selected_checkbox.stateChanged.connect(self.filter_results)
        search_within_layout.addWidget(self.show_selected_checkbox)

        self.countslabel = QLabel("Fetched: 0  »  Filtered: 0  »  Selected: 0")
        self.countslabel.setAlignment(Qt.AlignRight)
        self.countslabel.setFont(QFont("Roboto", 10))
        layout.addWidget(self.countslabel)
        
        self.selected_rows = set()

        self.papers = []
        self.is_url_opening = False
        self.preview_table.doubleClicked.connect(self.cellDoubleClicked)
        
        self.setup_menu_bar()
                
        self.current_theme = self.load_theme_preference()
        if self.current_theme == 'dark':
            self.apply_theme(DARK_THEME)
            self.themeAction.setText("Toggle Light Mode")
        else:
            self.apply_theme(LIGHT_THEME)
            self.themeAction.setText("Toggle Dark Mode")
    
    def toggle_theme(self):
        if self.current_theme == "light":
            self.apply_theme(DARK_THEME)
            self.current_theme = "dark"
            self.themeAction.setText("Toggle Light Mode")
        else:
            self.apply_theme(LIGHT_THEME)
            self.current_theme = "light"
            self.themeAction.setText("Toggle Dark Mode")
        self.save_theme_preference()
            
    def save_theme_preference(self):
        with open('theme_preference.json', 'w') as f:
            json.dump({'theme': self.current_theme}, f)
            
    def load_theme_preference(self):
        try:
            with open('theme_preference.json', 'r') as f:
                data = json.load(f)
                return data.get('theme', 'light')
        except FileNotFoundError:
            return 'light'

    def start_search(self):
        if not self.search_button.isEnabled():
            return
        query = self.query_input.text()
        max_results = self.max_results_input.value()
        if not query:
            self.results_display.setText("Query cannot be empty. Please try again.")
            return
        
        try:
            if not check_internet_connection():
                QMessageBox.warning(self, "No Internet Connection", "Please check your internet connection and try again.")
                return
        except Exception as e:
            QMessageBox.warning(self, "Error Checking Internet", f"An error occurred while checking internet connection: {str(e)}")
            return
        self.search_button.setEnabled(False)
        self.query_input.setReadOnly(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_display.clear()
        self.papers_model.clear_data()
        self.worker = SearchWorker(query, max_results)
        self.worker.finished.connect(self.search_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.error.connect(self.search_error)
        self.worker.start()

    def handle_return_pressed(self):
        if self.search_button.isEnabled():
            self.start_search()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.results_display.append(message)

    def search_finished(self, papers):
        self.papers = papers
        self.results_display.append(f"Search completed successfully. Found {len(papers)} results.")
        self.save_button.setEnabled(True)
        self.save_selected_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.update_preview_table()
        self.update_counts_label()
        if len(papers) > 0:
            self.tabs.setCurrentIndex(1)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def search_error(self, errormsg):
        self.results_display.append(f"Error: {errormsg}")
        self.search_button.setEnabled(True)
        self.query_input.setReadOnly(False)
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "Search Error", errormsg)

    def updatelog(self, message):
        self.results_display.append(message)

    def save_results(self):
        if not self.papers:
            return
        file_filter = "CSV Files (*.csv);;BibTeX Files (*.bib)"
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Save Results", "", file_filter)
        if filename:
            file_format = 'csv' if selected_filter == "CSV Files (*.csv)" else 'bib'
            if not filename.lower().endswith(f'.{file_format}'):
                filename = f'{filename}.{file_format}'
            try:
                sorted_papers = self.get_sorted_papers()
                save_to_file(sorted_papers, filename, file_format)
                self.results_display.append(f"Preview saved to {filename}")
            except Exception as e:
                self.results_display.append(f"Error saving file: {str(e)}")

    def save_selected_results(self):
        selected_papers = self.get_selected_papers()
        if not selected_papers:
            self.results_display.append("No results selected. Please select results to save.")
            return
        file_filter = "CSV Files (*.csv);;BibTeX Files (*.bib)"
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Save Selected Results", "", file_filter)
        if filename:
            file_format = 'csv' if selected_filter == "CSV Files (*.csv)" else 'bib'
            if not filename.lower().endswith(f'.{file_format}'):
                filename += f'.{file_format}'
            try:
                save_to_file(selected_papers, filename, file_format)
                self.results_display.append(f"Selected results saved to {filename}")
            except Exception as e:
                self.results_display.append(f"Error saving file: {str(e)}")

    def update_preview_table(self):
        self.papers_model.setPapers(self.papers)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.horizontalHeader().sortIndicatorChanged.connect(self.papers_model.sort)

    def cellDoubleClicked(self, index):
        if index.column() == 9:
            url = self.papers_model.papers[index.row()].get('PDF URL', '')
            if url and not self.is_url_opening:
                self.is_url_opening = True
                QDesktopServices.openUrl(QUrl(url))
                QTimer.singleShot(1000, self.reset_url_opening)
        else:
            self.show_paper_details(index.row())

    def apply_dialog_theme(self, dialog):
        dialog_palette = QPalette(self.palette())
        dialog.setPalette(dialog_palette)

        if self.current_theme == "dark":
            text_color = "#F5F3EF"
            bg_color = "#141414"
            link_color = "#4A90E2"
            button_bg = "#2C2C2C"
            button_text = "#F5F3EF"
            button_hover = "#3A3A3A"
            button_pressed = "#1E1E1E"
        else:
            text_color = "#141414"
            bg_color = "#F5F3EF"
            link_color = "#71A6D2"
            button_bg = "#E0E0E0"
            button_text = "#141414"
            button_hover = "#D0D0D0"
            button_pressed = "#C0C0C0"

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QTextBrowser {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
            }}
            QTextBrowser a {{
                color: {link_color};
            }}
            QPushButton {{
                background-color: {button_bg};
                color: {button_text};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
        """)

    def show_paper_details(self, row):
        paper = self.papers_model.papers[row]
        dialog = PaperDetailsDialog(paper, self)
        self.apply_dialog_theme(dialog)
        dialog.exec()

    def reset_url_opening(self):
        self.is_url_opening = False
    
    def setup_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: transparent;
                color: #333333;
                padding: 5px;
                font-size: 14px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
                margin-right: 5px;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenuBar::item:pressed {
                background-color: #d0d0d0;
            }
        """)

        self.themeAction = menubar.addAction("Toggle Dark Mode")
        self.themeAction.triggered.connect(self.toggle_theme)

        self.tipsAction = menubar.addAction("Tips")
        self.tipsAction.triggered.connect(self.show_instructions)

        self.aboutAction = menubar.addAction("About")
        self.aboutAction.triggered.connect(self.show_about)

    def show_instructions(self):
        instructions = """
        <h2>Tips for Better Sifting</h2>
        <hr>
        <h3>Search within Fields</h3>
        <p>Search within specific fields using <i>field:term</i> syntax.</p>
        <ul>
        <li><strong>title:</strong> Search within the title field
        <br><i>Example: title:discourse</i></li>
        <li><strong>authors:</strong> Search for specific authors
        <br><i>Example: authors:Baker</i></li>
        <li><strong>year:</strong> Search by publication year
        <br><i>Example: year:2008</i></li>
        <li><strong>abstract:</strong> Search within the abstract
        <br><i>Example: abstract:methods </i></li>
        </ul>
        
        <h3>Phrase Matching</h3>
        <ul>
        <li>Use quotation marks to match exact phrases.
        <br><i>Example: "critical discourse studies"</i></li>
        </ul>

        <h3>Boolean Operators</h3>
        <ul>
        <li>Use <strong>AND</strong> to match records containing all specified terms.
        <br><i>Example: "critical discourse analysis" AND corpus</i></li>
        <li>Use <strong>OR</strong> to match records containing any of the specified terms.
        <br><i>Example: analysis OR studies</i></li>
        <li>Use <strong>NOT</strong> to exclude records containing specific terms.
        <br><i>Example: "discourse analysis" NOT critical</i></li>
        </ul>
        
        <h3>Wildcard Matching</h3>
        <ul>
        <li>Use asterisk (*) to represent any number of characters.
        <br><i>Example: disc* matches discourse, discursive, etc.</i></li>
        <li>Use ? to represent a single character.
        <br><i>Example: polari?ation matches polarisation and polarization</i></li>
        </ul>
        
        <h3>Complex Matching</h3>
        <ul>
        <li>Use parenthesis () to define precedence and nesting.
        <br><i>Example: ((title:"critical discourse" OR (abstract:critical OR abstract:discourse)) AND (authors:Baker OR authors:Wodak OR authors:Dijk)) AND year:200?</i></li>
        </ul>
        """

        dialog = QDialog(self)
        dialog.setWindowTitle("Sift Tips")
        dialog_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        instructions_label = CustomTextBrowser()
        instructions_label.setOpenExternalLinks(True)
        instructions_label.setHtml(instructions)
        instructions_label.setFont(QFont("Roboto", 10))

        scroll_area.setWidget(instructions_label)
        dialog_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        dialog_layout.addWidget(close_button)

        dialog.setLayout(dialog_layout)
        dialog.setMinimumSize(600, 500)
        self.apply_dialog_theme(dialog)
        dialog.exec()

    def update_counts_label(self):
        fetched_count = len(self.papers_model.papers)
        filtered_count = sum(1 for row in range(self.preview_table.model().rowCount()) 
                             if not self.preview_table.isRowHidden(row))
        selected_count = len(self.preview_table.selectionModel().selectedRows())
        self.countslabel.setText(f"Fetched: {fetched_count} » Filtered: {filtered_count} » Selected: {selected_count}")
    
    def handle_selection_change(self, selected, deselected):
            self.selected_rows = set(index.row() for index in self.preview_table.selectionModel().selectedRows())
            self.update_counts_label()
            self.preview_table.all_selected = len(self.selected_rows) == self.preview_table.model().rowCount()

    def update_visual_selection(self):
        model = self.preview_table.model()
        if model:
            for row in range(model.rowCount()):
                index = model.index(row, 0)
                if index.isValid():
                    self.preview_table.setRowHidden(row, row not in self.selected_rows)

    def tokenize_search(self, search_text):
        if not search_text.strip():
            return []
        
        field_pattern = r'(\w+):("(?:[^"\\]|\\.)*"|[^\s()]+)'
        term_pattern = r'"([^"]*)"|\S+'
        tokens = []
        while search_text:
            field_match = re.match(field_pattern, search_text)
            if field_match:
                field, phrase_or_term = field_match.groups()
                tokens.append((field.lower(), phrase_or_term.strip('"')))
                search_text = search_text[field_match.end():].strip()
            elif search_text[0] in '()':
                tokens.append(search_text[0])
                search_text = search_text[1:].strip()
            else:
                term_match = re.match(term_pattern, search_text)
                if term_match:
                    tokens.append(term_match.group(1) or term_match.group())
                    search_text = search_text[term_match.end():].strip()
                else:
                    search_text = search_text[1:].strip()
        return tokens

    def match_row(self, row, tokens):
        paper = self.papers_model.papers[row]
        row_data = {
            'title': (paper.get("Title") or "").lower(),
            'authors': (paper.get("Authors") or "").lower(),
            'year': str(paper.get("Year", "")).lower(),
            'citations': str(paper.get("Citations", "")).lower(),
            'influential_citations': str(paper.get("Influential Citations", "")).lower(),
            's2_tldr': (paper.get("S2 TLDR") or "").lower(),
            'abstract': (paper.get("Abstract") or "").lower(),
            'publication': (paper.get("Publication") or "").lower(),
            'doi': (paper.get("DOI") or "").lower(),
            'pdf_url': (paper.get("PDF URL") or "").lower()
        }
        return self.evaluate_boolean_expression(tokens, row_data)

    def evaluate_boolean_expression(self, tokens, row_data):
        if not tokens:
            return True
        parser = BooleanExpressionParser(tokens)
        expression = parser.parse()
        return self.evaluate_expression(expression, row_data)

    def evaluate_expression(self, expr, row_data):
        if expr.type == 'AND':
            return self.evaluate_expression(expr.left, row_data) and self.evaluate_expression(expr.right, row_data)
        elif expr.type == 'OR':
            return self.evaluate_expression(expr.left, row_data) or self.evaluate_expression(expr.right, row_data)
        elif expr.type == 'NOT':
            return not self.evaluate_expression(expr.right, row_data)
        elif expr.type == 'TERM':
            return self.match_term(expr.value, ' '.join(row_data.values()))
        elif expr.type == 'FIELD':
            field, term = expr.value
            if field == 'any':
                return any(self.match_term(term, value) for value in row_data.values())
            else:
                return self.match_term(term, row_data.get(field, ''))
        else:
            raise ValueError(f"Unknown expression type: {expr.type}")

    def match_term(self, term, text):
        if term.startswith('"') and term.endswith('"'):
            return term.strip('"').lower() in text
        elif '*' in term or '?' in term:
            pattern = term.replace('*', '.*').replace('?', '.').lower()
            return bool(re.search(pattern, text))
        else:
            return re.search(r'\b' + re.escape(term.lower()) + r'\b', text.lower()) is not None

    def filter_results(self):
        search_text = self.search_within_input.text()
        tokens = self.tokenize_search(search_text)
        show_only_selected = self.show_selected_checkbox.isChecked()
        model = self.preview_table.model()
        if model:
            for row in range(model.rowCount()):
                match = self.evaluate_boolean_expression(tokens, self.get_row_data(row))
                if show_only_selected:
                    match = match and (row in self.selected_rows)
                self.preview_table.setRowHidden(row, not match)
        self.update_counts_label()

    def get_row_data(self, row):
        paper = self.papers_model.papers[row]
        return {
            'title': (paper.get("Title") or "").lower(),
            'authors': (paper.get("Authors") or "").lower(),
            'year': str(paper.get("Year", "")).lower(),
            'citations': str(paper.get("Citations", "")).lower(),
            'influential_citations': str(paper.get("Influential Citations", "")).lower(),
            's2_tldr': (paper.get("S2 TLDR") or "").lower(),
            'abstract': (paper.get("Abstract") or "").lower(),
            'publication': (paper.get("Publication") or "").lower(),
            'doi': (paper.get("DOI") or "").lower(),
            'pdf_url': (paper.get("PDF URL") or "").lower()
        }

    def get_sorted_papers(self):
        return [self.papers_model.papers[self.preview_table.model().index(row, 0).row()]
                for row in range(self.preview_table.model().rowCount())
                if not self.preview_table.isRowHidden(row)]

    def get_selected_papers(self):
        return [self.papers_model.papers[index.row()]
                for index in self.preview_table.selectionModel().selectedRows()]

    def show_about(self):
        about_text = """
        <h2>LitSift <small>v1.0.1</small></h2>
        <p>Seamlessly search, sift, and export results from Semantic Scholar to BibTeX/CSV</p>
        <hr>
        <h3>License</h3>
        <p>LitSift is licensed under the MIT License</p>

        <p>Copyright &copy; 2024 Jaisal E. K.</p>

        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>

        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>

        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        <hr>
        <h3>Third-Party Libraries and Services</h3>
        <p>LitSift uses the following third-party libraries and services:</p>
        <ul>
        <li>Semantic Scholar Academic Graph API (<a href="https://www.semanticscholar.org/product/api/license">License Agreement</a>)</li>
        <li>PySide6 (<a href="https://pypi.org/project/PySide6">LGPL License</a>)</li>
        <li>aiohttp (<a href="https://github.com/aio-libs/aiohttp">Apache License, Version 2.0</a>)</li>
        <li>asyncio (<a href="https://pypi.org/project/asyncio">PSF License</a>)</li>
        <li>Roboto Font (<a href="https://fonts.google.com/specimen/Roboto/about">Apache License, Version 2.0</a>)</li>
        </ul>
        <p>Full license details can be found at the links provided.</p>
        <hr>
        <h3>Citation</h3>
        <p><a href="https://jaisal.in">Jaisal, E. K.</a> (2024). LitSift: Seamlessly search, sift, and export results from Semantic Scholar to BibTeX/CSV. Available at: <a href="https://github.com/ekjaisal/litsift">https://github.com/ekjaisal/litsift</a>.</p>
        <hr>
        <h3>Acknowledgements</h3>
        <p>LitSift has benefitted significantly from some of the many ideas and suggestions of <a href="https://github.com/sarathkurmana">Sarath Kurmana</a>, the assistance of Anthropic's <a href="https://www.anthropic.com/news/claude-3-5-sonnet">Claude 3.5 Sonnet</a> with all the heavy lifting, feedback from <a href="https://in.linkedin.com/in/dhananjayan-ashok-geology">Dhananjayan T. Ashok</a> and <a href="https://www.linkedin.com/in/jayakrishnan-s-s-342416181">Jayakrishnan S. S.</a>, <a href="https://github.com/muhammedrashidx">Muhammed Rashid's</a> encouragement, and <a href="https://vishnurajagopal.in">Vishnu Rajagopal's</a> support.</p>
        """
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About LitSift")
        layout = QVBoxLayout(about_dialog)
        
        text_browser = CustomTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(about_text)
        layout.addWidget(text_browser)
        close_button = QPushButton("Close")
        close_button.clicked.connect(about_dialog.close)
        layout.addWidget(close_button)
        about_dialog.setLayout(layout)
        about_dialog.setMinimumSize(730, 430)
        self.apply_dialog_theme(about_dialog)
        about_dialog.exec()

    def apply_theme(self, theme):
        palette = QPalette()
        for role, color in theme.items():
            palette.setColor(getattr(QPalette, role), QColor(color))
        palette.setColor(QPalette.PlaceholderText, QColor(theme['PlaceholderText']))
        self.setPalette(palette)
        
        button_style = f"""
        QPushButton {{
            font-family: Roboto;
            background-color: {theme['Button']};
            color: {theme['ButtonText']};
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {QColor(theme['Button']).lighter(110).name()};
        }}
        QPushButton:pressed {{
            background-color: {QColor(theme['Button']).darker(110).name()};
        }}
        QPushButton:disabled {{
            background-color: {QColor(theme['Button']).lighter(150).name()};
            color: {QColor(theme['ButtonText']).lighter(150).name()};
        }}
        """

        constant_button_style = f"""
        QPushButton {{
            font-family: Roboto;
            background-color: #71A6D2;
            color: {theme['ButtonText']};
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {QColor("#71A6D2").lighter(110).name()};
        }}
        QPushButton:pressed {{
            background-color: {QColor("#71A6D2").darker(110).name()};
        }}
        QPushButton:disabled {{
            background-color: {QColor("#71A6D2").lighter(135).name()};
            color: {QColor(theme['ButtonText']).lighter(100).name()};
        }}
        QPushButton:focus {{
            outline: none;
            border: none;
        }}
        """
        self.search_button.setStyleSheet(constant_button_style)
        self.save_button.setStyleSheet(constant_button_style)
        self.save_selected_button.setStyleSheet(constant_button_style)
        
        reset_button_style = f"""
        QPushButton {{
            font-family: Roboto;
            background-color: #DC5349;
            color: {theme['ButtonText']};
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {QColor('#DC5349').lighter(110).name()};
        }}
        QPushButton:pressed {{
            background-color: {QColor('#DC5349').darker(110).name()};
        }}
        QPushButton:disabled {{
            background-color: {QColor('#DC5349').lighter(130).name()};
            color: {QColor(theme['ButtonText']).lighter(150).name()};
        }}
        QPushButton:focus {{
            outline: none;
            border: none;
        }}
        """
        self.reset_button.setStyleSheet(reset_button_style)
    
        menubar_style = f"""
            QMenuBar {{
                font-family: Roboto;
                background-color: {theme['Window']};
                color: {theme['WindowText']};
                padding: 5px;
                font-size: 12px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 3px 6px;
                margin-right: 5px;
                border: 1px solid {QColor(theme['WindowText']).lighter(200).name()};
                border-radius: 0px;
            }}
            QMenuBar::item:selected {{
                background-color: {QColor("#76798B").darker(125).name()};
            }}
            QMenuBar::item:pressed {{
                background-color: {QColor("#76798B").darker(140).name()};
            }}
        """
        self.menuBar().setStyleSheet(menubar_style)
        
                                
    def reset_litsift(self):
        
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.terminate()
            self.worker.wait()
            self.worker = None

        self.papers = []
        self.selected_rows.clear()

        self.query_input.clear()
        self.max_results_input.setValue(100)
        self.search_within_input.clear()
        self.results_display.clear()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.save_button.setEnabled(False)
        self.save_selected_button.setEnabled(False)
        self.search_button.setEnabled(True)
        self.query_input.setReadOnly(False)
        self.show_selected_checkbox.setChecked(False)

        self.papers_model.clear_data()
        self.preview_table.clearSelection()
        self.preview_table.setSortingEnabled(False)
        self.preview_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.papers_model.sort_column = 0
        self.papers_model.sort_order = Qt.AscendingOrder
        self.preview_table.setSortingEnabled(True)

        self.is_url_opening = False

        self.countslabel.setText("Fetched: 0 » Filtered: 0 » Selected: 0")
        self.tabs.setCurrentIndex(0)

        self.filter_results()
        self.update_visual_selection()
        self.update_counts_label()

        self.search_within_input.clear()
        self.preview_table.setSortingEnabled(True)

        self.results_display.append("LitSift has been reset. Ready for a new search.")
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    load_custom_fonts()
    window = LitSiftGUI()
    window.showMaximized()
    sys.exit(app.exec())
