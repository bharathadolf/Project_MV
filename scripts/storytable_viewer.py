import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, 
                               QPushButton, QLabel, QHeaderView, QFrame,
                               QFileDialog, QMessageBox, QInputDialog, QProgressBar,
                               QDialog, QCheckBox, QDialogButtonBox, QScrollArea,
                               QMenu, QToolBar, QTabWidget, QFormLayout, QLineEdit, 
                               QSpinBox, QAbstractItemView)
from PySide6.QtCore import Qt, QSize
from convert_to_storytable import convert_json_to_storytable, convert_md_to_storytable
from PySide6.QtGui import QFont, QIcon, QColor, QAction

class StoryTableParser:
    def __init__(self, filepath=None):
        self.project_name = "Untitled Project"
        self.scenes = []  
        self.columns = []
        self.filepath = None
        if filepath:
            self.parse(filepath)
            
    def parse(self, filepath):
        self.filepath = filepath
        self.scenes = []
        self.columns = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            current_scene = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split('|')
                tag = parts[0]
                
                if tag == "@PROJECT" and len(parts) > 1:
                    self.project_name = parts[1]
                elif tag == "@SCENE" and len(parts) >= 5:
                    current_scene = {
                        "id": parts[1],
                        "name": parts[2],
                        "duration": parts[3],
                        "color": parts[4],
                        "shots": []
                    }
                    self.scenes.append(current_scene)
                elif tag == "@COLUMNS":
                    self.columns = parts[1:]
                elif tag == "@SHOT":
                    if current_scene is not None:
                        shot_data = parts[1:]
                        current_scene["shots"].append(shot_data)
            return True
        except Exception as e:
            print(f"Error parsing file: {e}")
            return False

    def save_to_file(self):
        if not self.filepath:
            return False
            
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(f"@PROJECT|{self.project_name}\n\n")
                
                for scene in self.scenes:
                    f.write(f"@SCENE|{scene['id']}|{scene['name']}|{scene['duration']}|{scene['color']}\n")
                    f.write("@COLUMNS|" + "|".join(self.columns) + "\n")
                    for shot in scene['shots']:
                        f.write("@SHOT|" + "|".join(shot) + "\n")
                    f.write("\n")
            return True
        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

class MultiSelectDialog(QDialog):
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Files to Load")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        label = QLabel("Select among these converted files to load onto the interface:")
        layout.addWidget(label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        self.checkboxes = []
        for file_path in file_list:
            cb = QCheckBox(os.path.basename(file_path))
            cb.setProperty("filepath", file_path)
            cb.setChecked(True)
            self.scroll_layout.addWidget(cb)
            self.checkboxes.append(cb)
            
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_selected_files(self):
        return [cb.property("filepath") for cb in self.checkboxes if cb.isChecked()]

class GenericEditDialog(QDialog):
    def __init__(self, col_name, current_values, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit {col_name}")
        self.resize(400, 300)
        self.current_values = current_values
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Change All
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        self.all_input = QLineEdit()
        if current_values:
            self.all_input.setText(current_values[0])
        all_layout.addWidget(QLabel(f"Set all rows in the {col_name} column to:"))
        all_layout.addWidget(self.all_input)
        all_layout.addStretch()
        self.tabs.addTab(all_tab, "Change All")
        
        # Tab 2: Individual
        indiv_tab = QWidget()
        indiv_layout = QVBoxLayout(indiv_tab)
        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([col_name])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setRowCount(len(current_values))
        for i, val in enumerate(current_values):
            self.table.setItem(i, 0, QTableWidgetItem(str(val)))
            
        indiv_layout.addWidget(self.table)
        self.tabs.addTab(indiv_tab, "Individual Edit")
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_new_values(self):
        new_vals = []
        if self.tabs.currentIndex() == 0:
            val = self.all_input.text().strip()
            new_vals = [val] * len(self.current_values)
        else:
            for i in range(self.table.rowCount()):
                item = self.table.item(i, 0)
                new_vals.append(item.text().strip() if item else "")
        return new_vals

class SceneIdEditDialog(QDialog):
    def __init__(self, current_scene_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Scene ID")
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.scene_id_input = QLineEdit(current_scene_id)
        form.addRow("New Scene_ID:", self.scene_id_input)
        layout.addLayout(form)
        
        info = QLabel("Rules: Only characters (length 3-6) OR numbers (length 2-4).")
        info.setStyleSheet("color: #a0a0a0;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.new_scene_id = current_scene_id
        
    def validate_accept(self):
        val = self.scene_id_input.text().strip()
        if not val:
            QMessageBox.warning(self, "Invalid", "Value cannot be empty.")
            return
            
        if val.isalpha():
            if not (3 <= len(val) <= 6):
                QMessageBox.warning(self, "Invalid Length", "Character length must be between 3 and 6.")
                return
        elif val.isdigit():
            if not (2 <= len(val) <= 4):
                QMessageBox.warning(self, "Invalid Length", "Number length must be between 2 and 4.")
                return
        else:
            QMessageBox.warning(self, "Invalid Format", "Must be either all letters or all numbers.")
            return
            
        self.new_scene_id = val
        self.accept()

class ShotIdEditDialog(QDialog):
    def __init__(self, scene_id_val, current_shots_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Shot_ID")
        self.resize(400, 350)
        self.scene_id_val = scene_id_val
        self.current_shots_ids = current_shots_ids
        
        # Enforce underscore as the prefix separator
        self.prefix = f"{scene_id_val}_"
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: SEQUENCE
        seq_tab = QWidget()
        seq_layout = QFormLayout(seq_tab)
        
        self.prefix_lbl = QLabel(self.prefix)
        seq_layout.addRow("Prefix (Auto):", self.prefix_lbl)
        
        # Extract variables from existing sequences to populate defaults
        default_first = 1
        default_step = 1
        default_pad = 2
        
        extracted_nums = []
        pad_len_guess = None
        for sid in self.current_shots_ids:
            if not sid: continue
            sid_str = str(sid).strip()
            extra = ""
            if "_" in sid_str:
                extra = sid_str.split("_", 1)[1]
            elif "-" in sid_str:
                extra = sid_str.split("-", 1)[1]
            elif sid_str.startswith(str(scene_id_val)):
                extra = sid_str[len(str(scene_id_val)):]
                if extra.startswith(("-", "_")): extra = extra[1:]
            else:
                extra = sid_str
                
            if extra.isdigit():
                extracted_nums.append(int(extra))
                if pad_len_guess is None:
                    pad_len_guess = len(extra)
                    
        if extracted_nums:
            default_first = extracted_nums[0]
            if pad_len_guess is not None:
                default_pad = pad_len_guess
            if len(extracted_nums) > 1:
                default_step = extracted_nums[1] - extracted_nums[0]
                if default_step < 1:
                    default_step = 1
                    
        self.first_num = QSpinBox()
        self.first_num.setRange(0, 999999)
        self.first_num.setValue(default_first)
        seq_layout.addRow("First Number:", self.first_num)
        
        self.step_val = QSpinBox()
        self.step_val.setRange(1, 10000)
        self.step_val.setValue(default_step)
        seq_layout.addRow("Padding Difference (Step):", self.step_val)
        
        self.digit_padding = QSpinBox()
        self.digit_padding.setRange(1, 10)
        self.digit_padding.setValue(default_pad)
        seq_layout.addRow("Digit Padding:", self.digit_padding)
        
        self.tabs.addTab(seq_tab, "Auto-Generate")
        
        # Tab 2: INDIVIDUAL
        indiv_tab = QWidget()
        indiv_layout = QVBoxLayout(indiv_tab)
        
        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Shot_ID"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setRowCount(len(current_shots_ids))
        for i, sid in enumerate(current_shots_ids):
            self.table.setItem(i, 0, QTableWidgetItem(str(sid)))
            
        indiv_layout.addWidget(self.table)
        self.tabs.addTab(indiv_tab, "Individual Edit")
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_new_values(self):
        new_ids = []
        if self.tabs.currentIndex() == 0:
            # Generate
            curr_num = self.first_num.value()
            step = self.step_val.value()
            pad = self.digit_padding.value()
            for _ in range(len(self.current_shots_ids)):
                padded_num = str(curr_num).zfill(pad)
                new_ids.append(f"{self.prefix}{padded_num}")
                curr_num += step
        else:
            # Individual
            for i in range(self.table.rowCount()):
                item = self.table.item(i, 0)
                new_ids.append(item.text().strip() if item else "")
        return new_ids

class StoryTableViewer(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.loaded_projects = []
        self.primary_columns = ["assets", "shot id", "scene id", "camera", "shot_id", "scene_id"]
        self.selected_column_idx = -1
        self.current_selection = None
        
        self.setWindowTitle("Storytable Pipeline Viewer")
        self.resize(1200, 800)
        self.create_menus()
        self.setup_ui()
        self.apply_theme()
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        if initial_file and os.path.exists(initial_file):
            self.load_files([initial_file])

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        convert_menu = file_menu.addMenu("Convert")
        
        indiv_menu = convert_menu.addMenu("Individual")
        indiv_json_action = QAction("JSON", self)
        indiv_json_action.triggered.connect(self.on_import_indiv_json)
        indiv_md_action = QAction("Markdown", self)
        indiv_md_action.triggered.connect(self.on_import_indiv_md)
        indiv_menu.addAction(indiv_json_action)
        indiv_menu.addAction(indiv_md_action)
        
        batch_menu = convert_menu.addMenu("Batch")
        batch_json_action = QAction("JSON", self)
        batch_json_action.triggered.connect(self.on_import_batch_json)
        batch_md_action = QAction("Markdown", self)
        batch_md_action.triggered.connect(self.on_import_batch_md)
        batch_menu.addAction(batch_json_action)
        batch_menu.addAction(batch_md_action)
        
        import_menu = file_menu.addMenu("Import")
        
        import_indiv_menu = import_menu.addMenu("Individual")
        i_indiv_action = QAction(".storytable", self)
        i_indiv_action.triggered.connect(self.on_load_clicked)
        import_indiv_menu.addAction(i_indiv_action)
        
        import_batch_menu = import_menu.addMenu("Batch")
        i_batch_action = QAction(".storytable", self)
        i_batch_action.triggered.connect(self.on_batch_load_clicked)
        import_batch_menu.addAction(i_batch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Toolbar Area
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(30)
        toolbar_frame.setObjectName("toolbarFrame")
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Toggle sidebar button
        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setToolTip("Toggle Sidebar (Scenes)")
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        self.btn_toggle_sidebar.setFixedSize(26, 26)
        
        # Project Label
        self.lbl_project = QLabel("No Project Loaded")
        self.lbl_project.setObjectName("projectLabel")
        font = QFont("Inter", 11)
        font.setBold(True)
        self.lbl_project.setFont(font)
        
        toolbar_layout.addWidget(self.btn_toggle_sidebar)
        toolbar_layout.addWidget(self.lbl_project)
        toolbar_layout.addStretch()
        
        main_layout.addWidget(toolbar_frame)

        # Splitter Layout (Master/Detail)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        
        # Left Panel - Scenes List (Master)
        self.left_panel = QFrame()
        self.left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_scenes = QLabel(" Scenes")
        lbl_scenes.setObjectName("headerLabel")
        lbl_scenes.setContentsMargins(5, 10, 5, 10)
        left_layout.addWidget(lbl_scenes)
        
        self.list_scenes = QTreeWidget()
        self.list_scenes.setHeaderHidden(True)
        self.list_scenes.itemSelectionChanged.connect(self.on_scene_selected)
        self.list_scenes.setObjectName("sceneList")
        left_layout.addWidget(self.list_scenes)
        
        # Right Panel - Shots Table (Detail)
        self.right_panel = QFrame()
        self.right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_details = QLabel(" Shot Details")
        self.lbl_details.setObjectName("headerLabel")
        self.lbl_details.setContentsMargins(5, 10, 5, 10)
        right_layout.addWidget(self.lbl_details)
        
        # Ribbon Toolbar
        self.table_ribbon = QToolBar()
        self.table_ribbon.setObjectName("tableRibbon")
        self.table_ribbon.setMovable(False)
        
        self.action_make_primary = QAction("⭐", self)
        self.action_make_primary.setToolTip("Make this column primary")
        self.action_make_primary.triggered.connect(self.on_make_primary)
        
        self.action_edit_template = QAction("📄", self)
        self.action_edit_template.setToolTip("Edit the column template")
        self.action_edit_template.triggered.connect(self.on_edit_template)
        
        self.action_rename_column = QAction("✏️", self)
        self.action_rename_column.setToolTip("Rename")
        self.action_rename_column.triggered.connect(self.on_rename_column)
        
        self.action_edit_values = QAction("📋", self)
        self.action_edit_values.setToolTip("Edit values")
        self.action_edit_values.triggered.connect(self.on_edit_values)
        
        self.action_segregate_columns = QAction("🗂️", self)
        self.action_segregate_columns.setToolTip("Segregate primary columns")
        self.action_segregate_columns.triggered.connect(self.on_segregate_columns)
        
        self.table_ribbon.addAction(self.action_make_primary)
        self.table_ribbon.addAction(self.action_edit_template)
        self.table_ribbon.addAction(self.action_rename_column)
        self.table_ribbon.addAction(self.action_edit_values)
        self.table_ribbon.addSeparator()
        self.table_ribbon.addAction(self.action_segregate_columns)
        
        self.enable_ribbon_actions(False)
        right_layout.addWidget(self.table_ribbon)
        
        self.table_shots = QTableWidget()
        self.table_shots.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_shots.setAlternatingRowColors(True)
        self.table_shots.horizontalHeader().setStretchLastSection(True)
        self.table_shots.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_shots.verticalHeader().setVisible(False)
        
        self.table_shots.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_shots.horizontalHeader().customContextMenuRequested.connect(self.on_header_context_menu)
        self.table_shots.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        right_layout.addWidget(self.table_shots)
        
        # Add to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([300, 900])
        
        main_layout.addWidget(self.splitter)
        
    def apply_theme(self):
        # A modern dark theme for pipeline tools
        self.setStyleSheet("""
            QMainWindow, QDialog, QMessageBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }
            QMenuBar {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border-bottom: 1px solid #333333;
            }
            QMenuBar::item:selected {
                background-color: #3f3f46;
            }
            QMenu {
                background-color: #252526;
                color: #e0e0e0;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 20px 4px 20px;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
            QFrame#toolbarFrame {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
                font-weight: bold;
            }
            QFrame#leftPanel, QFrame#rightPanel {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLabel#projectLabel {
                color: #ffffff;
            }
            QLabel#headerLabel {
                background-color: #252526;
                color: #a0a0a0;
                font-weight: bold;
                border-bottom: 1px solid #333333;
            }
            QPushButton {
                background-color: #3a3d41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #4a4d51;
            }
            QPushButton:pressed {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 10px 5px;
                border-bottom: 1px solid #333333;
            }
            QTreeWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
                font-weight: bold;
            }
            QTreeWidget::item:hover:!selected {
                background-color: #2a2d2e;
            }
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #cccccc;
                gridline-color: #333333;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 6px;
                border: none;
                border-right: 1px solid #333;
                border-bottom: 1px solid #333;
                font-weight: bold;
            }
            QSplitter::handle {
                background-color: #3d3d3d;
            }
            QToolBar {
                background-color: #252526;
                border: none;
                border-bottom: 1px solid #333333;
                spacing: 5px;
                padding: 2px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 6px;
                color: #e0e0e0;
                font-size: 16px;
            }
            QToolBar QToolButton:hover {
                background-color: #3f3f46;
                border: 1px solid #555555;
            }
            QToolBar QToolButton:pressed {
                background-color: #007acc;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 14px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #424242;
                min-width: 20px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def toggle_sidebar(self):
        # Check if left panel is visible or collapsed
        is_visible = self.left_panel.isVisible()
        self.left_panel.setVisible(not is_visible)

    def on_load_clicked(self, *args):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Storytable File", "", "Storytable Files (*.storytable);;All Files (*)"
        )
        if file_path:
            self.load_files([file_path])

    def on_batch_load_clicked(self, *args):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Storytable Files", "", "Storytable Files (*.storytable);;All Files (*)"
        )
        if file_paths:
            self.load_files(file_paths)

    def on_import_indiv_json(self):
        self.handle_indiv_import("JSON Files (*.json);;All Files (*)", convert_json_to_storytable)

    def on_import_indiv_md(self):
        self.handle_indiv_import("Markdown Files (*.md);;All Files (*)", convert_md_to_storytable)

    def on_import_batch_json(self):
        self.handle_batch_import("JSON Files (*.json);;All Files (*)", convert_json_to_storytable)
        
    def on_import_batch_md(self):
        self.handle_batch_import("Markdown Files (*.md);;All Files (*)", convert_md_to_storytable)

    def handle_indiv_import(self, file_filter, converter_func):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Convert File", "", file_filter
        )
        if file_path:
            default_out = file_path.rsplit('.', 1)[0] + '.storytable'
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Storytable File", 
                default_out, 
                "Storytable Files (*.storytable)"
            )
            
            if output_path:
                try:
                    converter_func(file_path, output_path)
                    
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Load File")
                    msg_box.setText(f"Successfully saved to:\n{output_path}\n\nDo you want to load this file now?")
                    load_btn = msg_box.addButton("Load", QMessageBox.AcceptRole)
                    cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
                    msg_box.exec()
                    
                    if msg_box.clickedButton() == load_btn:
                        self.load_files([output_path])
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to convert file:\n{str(e)}")

    def handle_batch_import(self, file_filter, converter_func):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Convert", "", file_filter
        )
        if not file_paths:
            return
            
        prefix, ok = QInputDialog.getText(
            self, "Batch Target Prefix", "Enter the naming prefix (e.g. 'episode'):"
        )
        if not ok or not prefix.strip():
            return
        prefix = prefix.strip()
        
        save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if not save_dir:
            return
            
        success_count = 0
        converted_files = []
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(file_paths))
        self.progress_bar.setValue(0)
        
        for i, file_path in enumerate(file_paths):
            output_name = f"{prefix}{i+1}.storytable"
            output_path = os.path.join(save_dir, output_name)
            try:
                converter_func(file_path, output_path)
                success_count += 1
                converted_files.append(output_path)
            except Exception as e:
                print(f"Failed to convert {file_path}: {e}")
                
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
            
        self.progress_bar.setVisible(False)
                
        if success_count > 0:
            dialog = MultiSelectDialog(converted_files, self)
            if dialog.exec() == QDialog.Accepted:
                selected_files = dialog.get_selected_files()
                if selected_files:
                    self.load_files(selected_files)
        else:
            QMessageBox.warning(self, "Batch Failed", "No files were successfully converted.")

    def load_files(self, filepaths):
        self.loaded_projects = []
        
        # A curated list of elegant dark theme compatible colors to assign to different files
        theme_colors = [
            "#3B82F6", # Blue
            "#10B981", # Emerald
            "#F59E0B", # Amber
            "#8B5CF6", # Violet
            "#EF4444", # Red
            "#EC4899", # Pink
            "#06B6D4", # Cyan
        ]
        
        for i, filepath in enumerate(filepaths):
            parser = StoryTableParser()
            success = parser.parse(filepath)
            if success:
                color = theme_colors[i % len(theme_colors)]
                self.loaded_projects.append({
                    "parser": parser,
                    "color": color,
                    "filename": os.path.basename(filepath)
                })
                
        if self.loaded_projects:
            if len(self.loaded_projects) == 1:
                self.lbl_project.setText(f"Project: {self.loaded_projects[0]['parser'].project_name}")
            else:
                self.lbl_project.setText("Multiple Projects Loaded")
                
            self.populate_scenes()
            if self.list_scenes.topLevelItemCount() > 0:
                self.list_scenes.setCurrentItem(self.list_scenes.topLevelItem(0))
    
    def populate_scenes(self):
        self.list_scenes.clear()
        
        for p_idx, project_data in enumerate(self.loaded_projects):
            parser = project_data["parser"]
            file_color = project_data["color"]
            filename = project_data["filename"]
            
            parent_item = QTreeWidgetItem(self.list_scenes)
            parent_item.setText(0, filename)
            parent_item.setForeground(0, QColor(file_color))
            parent_item.setData(0, Qt.UserRole, (p_idx, -1))
            parent_item.setExpanded(False)
            
            for s_idx, scene in enumerate(parser.scenes):
                display_text = f"Scene {scene['id']}: {scene['name']}\n{scene['duration']} | {scene['color']}"
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(0, display_text)
                child_item.setForeground(0, QColor(file_color))
                child_item.setData(0, Qt.UserRole, (p_idx, s_idx))
            
    def on_scene_selected(self):
        selected_items = self.list_scenes.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        if data is None:
            return
            
        p_idx, s_idx = data
        
        project_data = self.loaded_projects[p_idx]
        
        if s_idx == -1:
            item.setExpanded(not item.isExpanded())
            self.table_shots.clearContents()
            self.table_shots.setRowCount(0)
            self.lbl_details.setText(f" Shot Details - {project_data['filename']}")
            self.current_selection = None
            return
            
        self.current_selection = (p_idx, s_idx)
        parser = project_data["parser"]
        scene = parser.scenes[s_idx]
        
        self.lbl_details.setText(f" Shot Details - Scene {scene['id']} ({project_data['filename']})")
        self.populate_shots(parser, scene)
        
    def populate_shots(self, parser, scene):
        self.table_shots.clear()
        
        self.selected_column_idx = -1
        self.enable_ribbon_actions(False)
        
        cols = parser.columns
        self.table_shots.setColumnCount(len(cols))
        self.table_shots.setHorizontalHeaderLabels(cols)
        
        primary_color = QColor("#00bcd4") # Cyan representing primary headers
        white_color = QColor("#ffffff")
        
        for i, col_name in enumerate(cols):
            header_item = self.table_shots.horizontalHeaderItem(i)
            if header_item:
                normalized_col = col_name.lower().replace(" ", "_")
                normalized_primaries = [p.replace(" ", "_") for p in self.primary_columns]
                if normalized_col in normalized_primaries:
                    header_item.setForeground(primary_color)
                else:
                    header_item.setForeground(white_color)
        
        shots = scene['shots']
        self.table_shots.setRowCount(len(shots))
        
        for row_idx, shot_data in enumerate(shots):
            for col_idx, col_value in enumerate(shot_data):
                if col_idx < len(cols):
                    table_item = QTableWidgetItem(str(col_value))
                    table_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    self.table_shots.setItem(row_idx, col_idx, table_item)
        
        self.table_shots.resizeRowsToContents()
        self.table_shots.resizeColumnsToContents()
        
        for i in range(len(cols)):
            if self.table_shots.columnWidth(i) > 300:
                self.table_shots.setColumnWidth(i, 300)
                
        rows = self.table_shots.rowCount()
        cols_count = self.table_shots.columnCount()
        self.status_bar.showMessage(f"Data Dimensions: {rows} rows x {cols_count} columns")

    def enable_ribbon_actions(self, enabled):
        self.action_make_primary.setEnabled(enabled)
        self.action_edit_template.setEnabled(enabled)
        self.action_rename_column.setEnabled(enabled)
        self.action_edit_values.setEnabled(enabled)

    def on_header_clicked(self, logicalIndex):
        self.selected_column_idx = logicalIndex
        self.enable_ribbon_actions(True)
        
        header_item = self.table_shots.horizontalHeaderItem(logicalIndex)
        if not header_item: return
        
        col_name = header_item.text().lower()
        if col_name in self.primary_columns:
            self.action_make_primary.setText("⭐")
            self.action_make_primary.setToolTip("Column is primary (Click to remove primary status)")
        else:
            self.action_make_primary.setText("☆")
            self.action_make_primary.setToolTip("Make this column primary")

    def on_header_context_menu(self, pos):
        logicalIndex = self.table_shots.horizontalHeader().logicalIndexAt(pos)
        if logicalIndex < 0: return
            
        self.on_header_clicked(logicalIndex)
        
        menu = QMenu(self)
        menu.addAction(self.action_make_primary)
        menu.addAction(self.action_edit_template)
        menu.addAction(self.action_rename_column)
        menu.addAction(self.action_edit_values)
        menu.addSeparator()
        menu.addAction(self.action_segregate_columns)
        
        menu.exec(self.table_shots.horizontalHeader().mapToGlobal(pos))

    def on_make_primary(self):
        if self.selected_column_idx < 0: return
        header_item = self.table_shots.horizontalHeaderItem(self.selected_column_idx)
        if not header_item: return
        
        col_name = header_item.text().lower()
        if col_name in self.primary_columns:
            self.primary_columns.remove(col_name)
            self.action_make_primary.setText("☆")
            self.action_make_primary.setToolTip("Make this column primary")
            header_item.setForeground(QColor("#ffffff"))
            QMessageBox.information(self, "Column Status", f"'{header_item.text()}' is no longer a primary column.")
        else:
            self.primary_columns.append(col_name)
            self.action_make_primary.setText("⭐")
            self.action_make_primary.setToolTip("Column is primary (Click to remove primary status)")
            header_item.setForeground(QColor("#00bcd4"))
            QMessageBox.information(self, "Column Status", f"'{header_item.text()}' is now a primary column.")
            
    def on_edit_template(self):
        if self.selected_column_idx < 0: return
        header_item = self.table_shots.horizontalHeaderItem(self.selected_column_idx)
        QMessageBox.information(self, "Edit Template", f"Opening template structure editor for column '{header_item.text()}'.")

    def on_rename_column(self):
        if self.selected_column_idx < 0: return
        header_item = self.table_shots.horizontalHeaderItem(self.selected_column_idx)
        old_name = header_item.text()
        
        new_name, ok = QInputDialog.getText(self, "Rename Column", "Enter new column name:", text=old_name)
        if ok and new_name.strip():
            was_primary = False
            if old_name.lower() in self.primary_columns:
                self.primary_columns.remove(old_name.lower())
                was_primary = True
                
            header_item.setText(new_name.strip())
            
            new_normalized = new_name.strip().lower().replace(" ", "_")
            primary_normalized = [p.replace(" ", "_") for p in self.primary_columns]
            
            if was_primary or new_normalized in primary_normalized:
                if new_name.strip().lower() not in self.primary_columns:
                    self.primary_columns.append(new_name.strip().lower())
                header_item.setForeground(QColor("#00bcd4"))
            else:
                header_item.setForeground(QColor("#ffffff"))
            
    def on_edit_values(self):
        if self.selected_column_idx < 0: return
        
        if not self.current_selection:
            QMessageBox.warning(self, "No Selection", "Please select a specific scene from the sidebar first.")
            return
            
        p_idx, s_idx = self.current_selection
        parser = self.loaded_projects[p_idx]["parser"]
        scene = parser.scenes[s_idx]
        
        if self.selected_column_idx >= len(parser.columns): return
        col_name = parser.columns[self.selected_column_idx]
        normalized_name = col_name.strip().lower().replace(" ", "_")
        
        current_vals = []
        for shot in scene["shots"]:
            val = shot[self.selected_column_idx] if self.selected_column_idx < len(shot) else ""
            current_vals.append(val)
            
        new_values = None
        
        if normalized_name == "scene_id":
            curr_id = scene["id"]
            dialog = SceneIdEditDialog(curr_id, self)
            if dialog.exec() == QDialog.Accepted:
                new_scene_id = dialog.new_scene_id
                new_values = [new_scene_id] * len(current_vals)
                scene["id"] = new_scene_id
                
                shot_id_idx = -1
                for idx, c_name in enumerate(parser.columns):
                    if c_name.strip().lower() in ["shot_id", "shot id"]:
                        shot_id_idx = idx
                        break
                        
                if shot_id_idx != -1:
                    for shot in scene["shots"]:
                        while len(shot) <= shot_id_idx:
                            shot.append("")
                        old_shot_id = shot[shot_id_idx]
                        if old_shot_id:
                            # Extract extra value
                            extra_val = ""
                            if "_" in old_shot_id:
                                extra_val = old_shot_id.split("_", 1)[1]
                            elif "-" in old_shot_id:
                                extra_val = old_shot_id.split("-", 1)[1]
                            elif old_shot_id.startswith(curr_id):
                                extra_val = old_shot_id[len(curr_id):]
                                if extra_val.startswith("-") or extra_val.startswith("_"):
                                    extra_val = extra_val[1:]
                            else:
                                extra_val = old_shot_id
                                
                            shot[shot_id_idx] = f"{new_scene_id}_{extra_val}"
                
        elif normalized_name == "shot_id":
            dialog = ShotIdEditDialog(scene["id"], current_vals, self)
            if dialog.exec() == QDialog.Accepted:
                new_values = dialog.get_new_values()
                
        else:
            dialog = GenericEditDialog(col_name, current_vals, self)
            if dialog.exec() == QDialog.Accepted:
                new_values = dialog.get_new_values()
                
        if new_values:
            for row_idx, shot in enumerate(scene["shots"]):
                while len(shot) <= self.selected_column_idx:
                    shot.append("")
                shot[self.selected_column_idx] = new_values[row_idx]
                
            success = parser.save_to_file()
            if success:
                QMessageBox.information(self, "Edit Values Saved", f"Values for column '{col_name}' updated and file saved successfully.")
            else:
                QMessageBox.warning(self, "Save Failed", "Values updated in memory but failed to save file.")
                
            self.populate_shots(parser, scene)
            self.populate_scenes()

    def on_segregate_columns(self):
        header = self.table_shots.horizontalHeader()
        col_count = self.table_shots.columnCount()
        if col_count == 0:
            return
            
        primary_logical = []
        non_primary_logical = []
        
        for idx in range(col_count):
            header_item = self.table_shots.horizontalHeaderItem(idx)
            if header_item and header_item.text().lower() in self.primary_columns:
                primary_logical.append(idx)
            else:
                non_primary_logical.append(idx)
                
        new_visual_order = primary_logical + non_primary_logical
        
        for visual_idx, logical_idx in enumerate(new_visual_order):
            current_visual_idx = header.visualIndex(logical_idx)
            if current_visual_idx != visual_idx:
                header.moveSection(current_visual_idx, visual_idx)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = StoryTableViewer()
    viewer.show()
    
    sys.exit(app.exec())
