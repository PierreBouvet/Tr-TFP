import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QTimer
from frontend.spectrometer_window import SpectrometerWindow
from backend.tfp_handler import TFPHandler
from backend.ni_handler import NIHandler

def main():
    app = QApplication(sys.argv)
    
    # Set Application Icon
    root_dir = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(root_dir, "Icon_fullscale.png")
    
    splash = None
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        # Create and show splash screen
        pixmap = QPixmap(icon_path)
        # Scale down by 25% (to 75% of original size)
        scaled_pixmap = pixmap.scaled(
            pixmap.size() * 0.5, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        splash = QSplashScreen(scaled_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
    
    window = SpectrometerWindow()
    
    # Stay on screen for 0.2s then disappear
    if splash:
        QTimer.singleShot(200, lambda: (splash.finish(window), window.show()))
    else:
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
