from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, 
                             QLabel, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt
import os
import h5py

from HDF5_BLS import Wrapper

class HDF5SaveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Results to HDF5_BLS")
        self.resize(500, 400)
        
        self.file_path = ""
        self.selected_group = "/"
        
        self.layout = QVBoxLayout(self)
        
        # File Selection
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select or create HDF5 file...")
        self.file_edit.setReadOnly(True)
        
        self.new_file_btn = QPushButton("New File")
        self.new_file_btn.clicked.connect(self.create_new_file)
        
        self.open_file_btn = QPushButton("Open File")
        self.open_file_btn.clicked.connect(self.browse_existing_file)
        
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.new_file_btn)
        file_layout.addWidget(self.open_file_btn)
        self.layout.addLayout(file_layout)
        
        # Search/Browse Tree
        self.layout.addWidget(QLabel("Select target group:"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("HDF5 Structure")
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.layout.addWidget(self.tree)
        
        # Group Controls
        group_btn_layout = QHBoxLayout()
        self.new_group_btn = QPushButton("New Group")
        self.new_group_btn.clicked.connect(self.create_new_group)
        self.new_group_btn.setEnabled(False)
        group_btn_layout.addWidget(self.new_group_btn)
        group_btn_layout.addStretch()
        self.layout.addLayout(group_btn_layout)
        
        # Dialog Controls
        btns_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save here")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btns_layout.addStretch()
        btns_layout.addWidget(self.cancel_btn)
        btns_layout.addWidget(self.save_btn)
        self.layout.addLayout(btns_layout)

    def create_new_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Create New HDF5 file", "", "HDF5 Files (*.h5 *.hdf5)"
        )
        if filename:
            self.wrp = Wrapper(filename)
            self.file_path = filename
            self.file_edit.setText(filename)
            self.refresh_tree()
            self.new_group_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

    def browse_existing_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Existing HDF5 file", "", "HDF5 Files (*.h5 *.hdf5)"
        )
        if filename:
            self.wrp = Wrapper(filename)
            self.file_path = filename
            self.file_edit.setText(filename)
            self.refresh_tree()
            self.new_group_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

    def refresh_tree(self):
        self.tree.clear()
        if not os.path.exists(self.file_path):
            root = QTreeWidgetItem(self.tree, ["/"])
            self.tree.addTopLevelItem(root)
            return

        try:
            with h5py.File(self.file_path, 'r') as f:
                root_item = QTreeWidgetItem(self.tree, ["/"])
                self.populate_tree(f, root_item)
                root_item.setExpanded(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read HDF5 file: {e}")

    def populate_tree(self, group, parent_item):
        for name, item in group.items():
            if isinstance(item, h5py.Group):
                child_item = QTreeWidgetItem(parent_item, [name])
                self.populate_tree(item, child_item)

    def on_selection_changed(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            self.selected_group = "/"
            return
        
        item = selected_items[0]
        path = []
        while item:
            text = item.text(0)
            if text != "/":
                path.insert(0, text)
            item = item.parent()
        
        self.selected_group = "/" + "/".join(path)
        print(f"Selected group: {self.selected_group}")

    def create_new_group(self):
        if not self.file_path:
            return
            
        group_name, ok = QInputDialog.getText(self, "New Group", "Enter group name:")
        if ok and group_name:
            try:
                from HDF5_BLS import Wrapper
                # Use Wrapper to create the group to ensure it follows any HDF5_BLS logic
                wrp = Wrapper(self.file_path)
                # If selected_group is root, parent is "/"
                # Logic: create_group(name, parent_group, type)
                # Based on doc, 'type' can be "Measure" for instance.
                wrp.create_group(group_name, self.selected_group, "Measure")
                wrp.close()
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create group: {e}")

    def get_selection(self):
        self.wrp.close()
        return {
            "file_path": self.file_path,
            "selected_group": self.selected_group
        }
