import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import pillow_heif

class ConverterThread(QThread):
    update_progress = pyqtSignal(int)
    conversion_complete = pyqtSignal()

    def __init__(self, input_folder, reduce_to_1080p):
        QThread.__init__(self)
        self.input_folder = input_folder
        self.reduce_to_1080p = reduce_to_1080p

    def run(self):
        pillow_heif.register_heif_opener()
        
        heic_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith('.heic')]
        total_files = len(heic_files)
        
        for i, filename in enumerate(heic_files):
            input_path = os.path.join(self.input_folder, filename)
            output_path = os.path.join(self.input_folder, os.path.splitext(filename)[0] + '.jpg')
            
            try:
                with Image.open(input_path) as img:
                    if self.reduce_to_1080p:
                        img = self.resize_to_1080p(img)
                    img.convert('RGB').save(output_path, 'JPEG')
            except Exception as e:
                print(f'Fehler bei der Konvertierung von {filename}: {str(e)}')
            
            self.update_progress.emit(int((i + 1) / total_files * 100))
        
        self.conversion_complete.emit()

    def resize_to_1080p(self, img):
        target_height = 1080
        aspect_ratio = img.width / img.height
        target_width = int(target_height * aspect_ratio)
        
        if img.height > target_height:
            return img.resize((target_width, target_height), Image.LANCZOS)
        return img

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'HEIC zu JPG Konverter'
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 400, 250)
        
        layout = QVBoxLayout()
        
        self.folder_button = QPushButton('Ordner auswählen', self)
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)
        
        self.label = QLabel('Kein Ordner ausgewählt', self)
        layout.addWidget(self.label)
        
        self.reduce_checkbox = QCheckBox('Auf 1080p reduzieren', self)
        layout.addWidget(self.reduce_checkbox)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)
        
        self.convert_button = QPushButton('Konvertieren', self)
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        layout.addWidget(self.convert_button)
        
        self.setLayout(layout)
        
    def select_folder(self):
        self.folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if self.folder:
            self.label.setText(f'Ausgewählter Ordner: {self.folder}')
            self.convert_button.setEnabled(True)
        
    def start_conversion(self):
        reduce_to_1080p = self.reduce_checkbox.isChecked()
        self.converter_thread = ConverterThread(self.folder, reduce_to_1080p)
        self.converter_thread.update_progress.connect(self.update_progress_bar)
        self.converter_thread.conversion_complete.connect(self.conversion_finished)
        self.converter_thread.start()
        self.convert_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.reduce_checkbox.setEnabled(False)
        
    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)
        
    def conversion_finished(self):
        self.label.setText('Konvertierung abgeschlossen!')
        self.convert_button.setEnabled(True)
        self.folder_button.setEnabled(True)
        self.reduce_checkbox.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())