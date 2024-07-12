import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QTextEdit, QProgressBar, QFileDialog, 
                               QLabel, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QScrollArea, QAbstractItemView, QDialog, QTextBrowser, QCheckBox)
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QDesktopServices, QFontDatabase
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer, QSortFilterProxyModel
import asyncio
from litsift_core import search_semantic_scholar, save_to_file
from functools import reduce
import re
import os

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
            papers = asyncio.run(search_semantic_scholar(self.query, self.max_results, self.update_progress))
            self.progress.emit(100, "Search completed")
            self.finished.emit(papers)
        except Exception as e:
            self.error.emit(str(e))

    def update_progress(self, value, message):
        self.progress.emit(value, message)

class ClickableURLItem(QTableWidgetItem):
    def __init__(self, url):
        super().__init__(url)
        self.url = url

class IntegerTableWidgetItem(QTableWidgetItem):
    def __init__(self, value):
        super().__init__(str(value))
        self.value = value

    def __lt__(self, other):
        if isinstance(other, IntegerTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)

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
        <p><strong><i>DOI</i>:</strong> {paper['DOI'] or "Not Available"}</p>
        <p><strong><i>Open Access PDF</i>:</strong> <a href="{paper['PDF URL']}">{paper['PDF URL'] or "Not Available"}</a></p>
        """

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(details)
        layout.addWidget(text_browser)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class LitSiftGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        app.setFont(QFont("Roboto", 10))
        self.setWindowTitle("LitSift")
        self.setWindowIcon(QIcon("LitSift.ico"))
        self.resize(950, 600)

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
        self.query_input.returnPressed.connect(self.start_search)
        querylayout.addWidget(self.query_input)

        self.maxresults_input = QSpinBox()
        self.maxresults_input.setRange(1, 1000)
        self.maxresults_input.setValue(100)
        self.maxresults_input.setFont(QFont("Roboto", 10))
        querylayout.addWidget(QLabel("Max. results (up to 1000):"))
        querylayout.addWidget(self.maxresults_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_search)
        self.search_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.search_button)

        self.save_button = QPushButton("Save All Results")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        self.save_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.save_button)

        self.save_selected_button = QPushButton("Save Selected")
        self.save_selected_button.clicked.connect(self.save_selected_results)
        self.save_selected_button.setEnabled(False)
        self.save_selected_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.save_selected_button)

        self.reset_button = QPushButton("Reset LitSift")
        self.reset_button.clicked.connect(self.reset_litsift)
        self.reset_button.setFont(QFont("Roboto", 10))
        querylayout.addWidget(self.reset_button)
        
        layout.addLayout(querylayout)

        self.progressbar = QProgressBar()
        self.progressbar.setVisible(False)
        layout.addWidget(self.progressbar)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Roboto", 10))

        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setFont(QFont("Roboto", 10))
        self.tabs.addTab(self.results_display, "Log")

        previewwidget = QWidget()
        previewlayout = QVBoxLayout(previewwidget)

        searchwithinlayout = QHBoxLayout()
        searchwithinlabel = QLabel("Search within results:")
        searchwithinlabel.setFont(QFont("Roboto", 10))
        searchwithinlayout.addWidget(searchwithinlabel)
        self.searchwithininput = QLineEdit()
        self.searchwithininput.setPlaceholderText("Enter terms to filter results (see tips for better sifting)")
        self.searchwithininput.setFont(QFont("Roboto", 10))
        self.searchwithininput.textChanged.connect(self.filter_results)
        searchwithinlayout.addWidget(self.searchwithininput)
        previewlayout.addLayout(searchwithinlayout)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(9)
        self.preview_table.setHorizontalHeaderLabels(["Title", "Authors", "Year", "Citations", "Influential Citations", "S2 TLDR", "Abstract", "DOI", "PDF URL"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.preview_table.setFont(QFont("Roboto", 10))
        self.preview_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.itemSelectionChanged.connect(self.handle_selection_change)
        self.preview_table.setSortingEnabled(True)
        previewlayout.addWidget(self.preview_table)

        self.tabs.addTab(previewwidget, "Preview Results")
        layout.addWidget(self.tabs)
        
        self.show_selected_checkbox = QCheckBox("Show only selected")
        self.show_selected_checkbox.setFont(QFont("Roboto", 10))
        self.show_selected_checkbox.stateChanged.connect(self.filter_results)
        searchwithinlayout.addWidget(self.show_selected_checkbox)

        self.countslabel = QLabel("Filtered: 0/0 • Selected: 0")
        self.countslabel.setAlignment(Qt.AlignRight)
        layout.addWidget(self.countslabel)
        
        self.selected_rows = set()

        self.papers = []
        self.isurlopening = False
        self.preview_table.cellDoubleClicked.connect(self.cellDoubleClicked)
        
        self.setup_menu_bar()
        
        self.current_theme = "light"
        self.apply_theme(LIGHT_THEME)
    
    def toggle_theme(self):
        if self.current_theme == "light":
            self.apply_theme(DARK_THEME)
            self.current_theme = "dark"
            self.themeAction.setText("Toggle Light Mode")
        else:
            self.apply_theme(LIGHT_THEME)
            self.current_theme = "light"
            self.themeAction.setText("Toggle Dark Mode")
            
    def start_search(self):
        query = self.query_input.text()
        max_results = self.maxresults_input.value()
        if not query:
            self.results_display.setText("Query cannot be empty. Please try again.")
            return
        self.search_button.setEnabled(False)
        self.progressbar.setVisible(True)
        self.progressbar.setValue(0)
        self.results_display.clear()
        self.preview_table.setRowCount(0)
        self.worker = SearchWorker(query, max_results)
        self.worker.finished.connect(self.search_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.error.connect(self.search_error)
        self.worker.start()

    def update_progress(self, value, message):
        self.progressbar.setValue(value)
        self.results_display.append(message)

    def search_finished(self, papers):
        self.papers = papers
        self.results_display.append(f"Search completed successfully. Found {len(papers)} results.")
        self.save_button.setEnabled(True)
        self.save_selected_button.setEnabled(True)
        self.progressbar.setVisible(False)
        self.progressbar.setValue(0)
        self.update_preview_table()
        self.tabs.setCurrentIndex(1)

    def update_progress(self, value):
        self.progressbar.setValue(value)

    def search_error(self, errormsg):
        self.results_display.append(f"Error: {errormsg}")
        self.search_button.setEnabled(True)
        self.progressbar.setVisible(False)

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
                filename += f'.{file_format}'
            
            try:
                sorted_papers = self.get_sorted_papers()
                save_to_file(sorted_papers, filename, file_format)
                self.results_display.append(f"Results saved to {filename}")
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
                            
    def reset_litsift(self):
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.terminate()
            self.worker.wait()
        self.worker = None
        self.query_input.clear()
        self.maxresults_input.setValue(100)
        self.searchwithininput.clear()
        self.results_display.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.clearContents()
        self.progressbar.setVisible(False)
        self.progressbar.setValue(0)
        self.papers = []
        self.save_button.setEnabled(False)
        self.save_selected_button.setEnabled(False)
        self.search_button.setEnabled(True)
        self.countslabel.setText("Filtered: 0/0 Selected: 0")
        self.tabs.setCurrentIndex(0)
        self.searchwithininput.clear()
        self.filter_results()
        self.preview_table.clearSelection()
        self.preview_table.setSortingEnabled(False)
        self.preview_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.preview_table.setSortingEnabled(True)
        self.selected_rows.clear()
        self.update_visual_selection()
        self.update_selection_count()
        self.show_selected_checkbox.setChecked(False)
        self.results_display.append("LitSift has been reset. Ready for a new search.")

    def update_preview_table(self):
        self.preview_table.setRowCount(0)
        self.preview_table.setRowCount(len(self.papers))
        for row, paper in enumerate(self.papers):
            for col in range(self.preview_table.columnCount()):
                if col in [2, 3, 4]:
                    value = paper.get(["Year", "Citations", "Influential Citations"][col - 2])
                    try:
                        item = IntegerTableWidgetItem(int(value))
                    except (ValueError, TypeError):
                        item = QTableWidgetItem(str(value))
                elif col == 8:
                    item = ClickableURLItem(paper.get("PDF URL"))
                else:
                    item = QTableWidgetItem()
                item.setData(Qt.UserRole, row)
                if col == 0:
                    item.setText(paper.get("Title"))
                elif col == 1:
                    item.setText(paper.get("Authors"))
                elif col == 5:
                    item.setText(paper.get("S2 TLDR"))
                elif col == 6:
                    item.setText(paper.get("Abstract"))
                elif col == 7:
                    item.setText(paper.get("DOI"))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, col, item)
                total_count = len(self.papers)

    def cellDoubleClicked(self, row, column):
        if column == 8 and not self.isurlopening:
            item = self.preview_table.item(row, column)
            if item and isinstance(item, ClickableURLItem) and item.url:
                self.isurlopening = True
                QDesktopServices.openUrl(QUrl(item.url))
                QTimer.singleShot(1000, self.reset_url_opening)
        else:
            self.show_paper_details(row)

    def show_paper_details(self, row):
        original_index = self.preview_table.item(row, 0).data(Qt.UserRole)
        if original_index is not None:
            paper = self.papers[original_index]
            dialog = PaperDetailsDialog(paper, self)
            dialog.exec()

    def reset_url_opening(self):
        self.isurlopening = False
    
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
        """

        dialog = QDialog(self)
        dialog.setWindowTitle("Sift Tips")
        dialog_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        instructions_label = QTextBrowser()
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
        dialog.exec()

    def update_selection_count(self):
        filtered_count = sum(1 for row in range(self.preview_table.rowCount()) if not self.preview_table.isRowHidden(row))
        total_count = self.preview_table.rowCount()
        selected_count = len(self.selected_rows)
        self.countslabel.setText(f"Filtered: {filtered_count}/{total_count} Selected: {selected_count}")
    
    def handle_selection_change(self):
        selected_indexes = self.preview_table.selectionModel().selectedRows()
        newly_selected = set(index.row() for index in selected_indexes) 

        visible_rows = set(row for row in range(self.preview_table.rowCount()) 
                           if not self.preview_table.isRowHidden(row))
        self.selected_rows.update(newly_selected.intersection(visible_rows)) 
        self.selected_rows.difference_update(set(range(self.preview_table.rowCount())) - newly_selected)

        self.update_visual_selection()
        self.update_selection_count()
        if self.show_selected_checkbox.isChecked():
            self.filter_results()
    
    def update_visual_selection(self):
        for row in range(self.preview_table.rowCount()):
            item = self.preview_table.item(row, 0)
            if item:
                item.setSelected(row in self.selected_rows)
    
    def tokenize_search(self, search_text):
        field_pattern = r'(\w+):("(?:[^"\\]|\\.)*"|[^\s]+)'
        term_pattern = r'"([^"]*)"|\S+'
        tokens = []
        while search_text:
            field_match = re.match(field_pattern, search_text)
            if field_match:
                field, phrase_or_term = field_match.groups()
                tokens.append((field.lower(), phrase_or_term.strip('"')))
                search_text = search_text[field_match.end():].strip()
            else:
                term_match = re.match(term_pattern, search_text)
                if term_match:
                    tokens.append(term_match.group(1) or term_match.group())
                    search_text = search_text[term_match.end():].strip()
                else:
                    search_text = search_text[1:].strip()
        return tokens

    def match_row(self, row, tokens):
        row_data = {
            'title': self.preview_table.item(row, 0).text().lower(),
            'authors': self.preview_table.item(row, 1).text().lower(),
            'year': self.preview_table.item(row, 2).text().lower(),
            'citations': self.preview_table.item(row, 3).text().lower(),
            'influential_citations': self.preview_table.item(row, 4).text().lower(),
            's2_tldr': self.preview_table.item(row, 5).text().lower(),
            'abstract': self.preview_table.item(row, 6).text().lower(),
            'doi': self.preview_table.item(row, 7).text().lower(),
            'pdf_url': self.preview_table.item(row, 8).text().lower()
        }
        return self.evaluate_boolean_expression(tokens, row_data)

    def evaluate_boolean_expression(self, tokens, row_data):
        stack = []
        for token in tokens:
            if isinstance(token, tuple):
                field, term = token
                if field == 'any':
                    result = any(self.match_term(term, value) for value in row_data.values())
                else:
                    result = self.match_term(term, row_data.get(field, ''))
                stack.append(result)
            elif token.upper() in ('AND', 'OR', 'NOT'):
                stack.append(token.upper())
            elif token == '(':
                stack.append(token)
            elif token == ')':
                subexpr = []
                while stack and stack[-1] != '(':
                    subexpr.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()
                stack.append(self.evaluate_subexpression(subexpr[::-1]))
            else:
                stack.append(self.match_term(token, ' '.join(row_data.values())))
        return self.evaluate_subexpression(stack)

    def evaluate_subexpression(self, expr):
        result = True
        operator = 'AND'
        for token in expr:
            if token in ('AND', 'OR', 'NOT'):
                operator = token
            elif isinstance(token, bool):
                if operator == 'AND':
                    result = result and token
                elif operator == 'OR':
                    result = result or token
                elif operator == 'NOT':
                    result = result and not token
        return result

    def match_term(self, term, text):
        if term.startswith('"') and term.endswith('"'):
            return term.strip('"').lower() in text
        elif '*' in term or '?' in term:
            pattern = term.replace('*', '.*').replace('?', '.').lower()
            return bool(re.search(pattern, text))
        else:
            return re.search(r'\b' + re.escape(term.lower()) + r'\b', text.lower()) is not None
    
    def filter_results(self):
        search_text = self.searchwithininput.text()
        tokens = self.tokenize_search(search_text)
        show_only_selected = self.show_selected_checkbox.isChecked()
        filtered_count = 0
        total_count = self.preview_table.rowCount()
        for row in range(total_count):
            match = self.match_row(row, tokens)
            if show_only_selected:
                match = match and (row in self.selected_rows)
            self.preview_table.setRowHidden(row, not match)
            if match:
                filtered_count += 1
            item = self.preview_table.item(row, 0)
            if item:
                item.setSelected(row in self.selected_rows)
        self.update_visual_selection()
        self.update_selection_count()

    def get_sorted_papers(self):
        sorted_papers = []
        for row in range(self.preview_table.rowCount()):
            if not self.preview_table.isRowHidden(row):
                item = self.preview_table.item(row, 0)
                if item:
                    original_index = item.data(Qt.UserRole)
                    if original_index is not None:
                        sorted_papers.append(self.papers[original_index])
        return sorted_papers

    def get_selected_papers(self):
        selected_papers = []
        for row in self.selected_rows:
            original_index = self.preview_table.item(row, 0).data(Qt.UserRole)
            if original_index is not None:
                selected_papers.append(self.papers[original_index])
        return selected_papers

    def show_about(self):
        about_text = """
        <h2>LitSift <small>v1.0.0</small></h2>
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
        <p><a href="https://jaisal.in">Jaisal E. K.</a> (2024). LitSift: Seamlessly search, sift, and export results from Semantic Scholar to BibTeX/CSV. Available at <a href="https://github.com/ekjaisal/litsift">https://github.com/ekjaisal/litsift</a>.</p>
        <hr>
        <h3>Acknowledgements</h3>
        <p>LitSift has benefitted significantly from some of the many ideas and suggestions of <a href="https://github.com/sarathkurmana">Sarath Kurmana</a>, the assistance of Anthropic's <a href="https://www.anthropic.com/news/claude-3-5-sonnet">Claude 3.5 Sonnet</a>, <a href="https://github.com/muhammedrashidx">Muhammed Rashid's</a> encouragement, and <a href="https://vishnurajagopal.in">Vishnu Rajagopal's</a> support.</p>
        """
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About LitSift")
        layout = QVBoxLayout(about_dialog)
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(about_text)
        layout.addWidget(text_browser)
        close_button = QPushButton("Close")
        close_button.clicked.connect(about_dialog.close)
        layout.addWidget(close_button)
        about_dialog.setLayout(layout)
        about_dialog.setMinimumSize(730, 430)
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
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    load_custom_fonts()
    window = LitSiftGUI()
    window.show()
    sys.exit(app.exec())
