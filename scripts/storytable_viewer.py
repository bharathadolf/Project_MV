import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, 
                               QPushButton, QLabel, QHeaderView, QFrame,
                               QFileDialog, QMessageBox, QInputDialog, QProgressBar,
                               QDialog, QCheckBox, QDialogButtonBox, QScrollArea)
from PySide6.QtCore import Qt, QSize
from convert_to_storytable import convert_json_to_storytable, convert_md_to_storytable
from PySide6.QtGui import QFont, QIcon, QColor, QAction

class StoryTableParser:
    def __init__(self, filepath=None):
        self.project_name = "Untitled Project"
        self.scenes = []  
        self.columns = []
        if filepath:
            self.parse(filepath)
            
    def parse(self, filepath):
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

class StoryTableViewer(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.loaded_projects = []
        
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
        font = QFont("Inter", 11, QFont.Bold)
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
        
        self.table_shots = QTableWidget()
        self.table_shots.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_shots.setAlternatingRowColors(True)
        self.table_shots.horizontalHeader().setStretchLastSection(True)
        self.table_shots.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_shots.verticalHeader().setVisible(False)
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
                color: #cccccc;
                padding: 6px;
                border: none;
                border-right: 1px solid #333;
                border-bottom: 1px solid #333;
                font-weight: bold;
            }
            QSplitter::handle {
                background-color: #3d3d3d;
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
            return
            
        parser = project_data["parser"]
        scene = parser.scenes[s_idx]
        
        self.lbl_details.setText(f" Shot Details - Scene {scene['id']} ({project_data['filename']})")
        self.populate_shots(parser, scene)
        
    def populate_shots(self, parser, scene):
        self.table_shots.clear()
        
        cols = parser.columns
        self.table_shots.setColumnCount(len(cols))
        self.table_shots.setHorizontalHeaderLabels(cols)
        
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

if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = StoryTableViewer()
    viewer.show()
    
    sys.exit(app.exec())
