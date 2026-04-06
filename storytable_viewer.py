import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QListWidget, QTableWidget, QTableWidgetItem, 
                               QPushButton, QLabel, QHeaderView, QListWidgetItem, QFrame,
                               QFileDialog)
from PySide6.QtCore import Qt, QSize
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

class StoryTableViewer(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.parser = StoryTableParser()
        
        self.setWindowTitle("Storytable Pipeline Viewer")
        self.resize(1200, 800)
        self.create_menus()
        self.setup_ui()
        self.apply_theme()
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        if initial_file and os.path.exists(initial_file):
            self.load_file(initial_file)

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open .storytable", self)
        open_action.triggered.connect(self.on_load_clicked)
        file_menu.addAction(open_action)
        
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
        
        self.list_scenes = QListWidget()
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
            QMainWindow {
                background-color: #1e1e1e;
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
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 5px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
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

    def on_load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Storytable File", "", "Storytable Files (*.storytable);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, filepath):
        success = self.parser.parse(filepath)
        if success:
            self.lbl_project.setText(f"Project: {self.parser.project_name}")
            self.populate_scenes()
            # Select first scene by default if available
            if self.list_scenes.count() > 0:
                self.list_scenes.setCurrentRow(0)
    
    def populate_scenes(self):
        self.list_scenes.clear()
        for i, scene in enumerate(self.parser.scenes):
            display_text = f"Scene {scene['id']}: {scene['name']}\n{scene['duration']} | {scene['color']}"
            item = QListWidgetItem(display_text)
            # Store scene index as data for easy retrieval
            item.setData(Qt.UserRole, i)
            self.list_scenes.addItem(item)
            
    def on_scene_selected(self):
        selected_items = self.list_scenes.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        scene_idx = item.data(Qt.UserRole)
        scene = self.parser.scenes[scene_idx]
        
        self.lbl_details.setText(f" Shot Details - Scene {scene['id']}")
        self.populate_shots(scene)
        
    def populate_shots(self, scene):
        self.table_shots.clear()
        
        # Set columns
        cols = self.parser.columns
        self.table_shots.setColumnCount(len(cols))
        self.table_shots.setHorizontalHeaderLabels(cols)
        
        # Add shots
        shots = scene['shots']
        self.table_shots.setRowCount(len(shots))
        
        for row_idx, shot_data in enumerate(shots):
            for col_idx, col_value in enumerate(shot_data):
                # Ensure we don't go out of bounds if a row has missing cols
                if col_idx < len(cols):
                    table_item = QTableWidgetItem(str(col_value))
                    # Allow text wrapping in table items
                    table_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    self.table_shots.setItem(row_idx, col_idx, table_item)
        
        self.table_shots.resizeRowsToContents()
        self.table_shots.resizeColumnsToContents()
        
        # Adjust some columns if they are too wide
        for i in range(len(cols)):
            if self.table_shots.columnWidth(i) > 300:
                self.table_shots.setColumnWidth(i, 300)
                
        # Update status bar with dimensions
        rows = self.table_shots.rowCount()
        cols_count = self.table_shots.columnCount()
        self.status_bar.showMessage(f"Data Dimensions: {rows} rows x {cols_count} columns")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = StoryTableViewer()
    viewer.show()
    
    sys.exit(app.exec())
