from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QFont, QCursor, QFontDatabase
import sys
import pyautogui
from PIL import Image, ImageQt
from core.font_manager.icon_manager import MaterialSymbolsTTFManager, RenderConfig, IconVariations

class RegionSelector(QWidget):
    """Professional region selection tool using PySide6"""
    
    selection_completed = Signal(tuple)
    selection_cancelled = Signal()
    
    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.selection_rect = QRect()
        self.screenshot_pixmap = None
        self.toolbar = None
        self.result = None
        self.material_font_available = "Material Symbols Outlined" in QFontDatabase.families()
        # Icon manager instance for toolbar icons
        self.icon_manager = MaterialSymbolsTTFManager()
        
    def select_region(self):
        """Show region selection overlay and return selected coordinates"""
        try:
            # Ensure QApplication exists
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert PIL image to QPixmap
            qt_image = ImageQt.ImageQt(screenshot)
            self.screenshot_pixmap = QPixmap.fromImage(qt_image)
            
            # Setup fullscreen overlay
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.setGeometry(app.primaryScreen().geometry())
            self.setCursor(QCursor(Qt.CrossCursor))
            self.showFullScreen()
            
            # Connect signals
            self.selection_completed.connect(self._on_selection_completed)
            self.selection_cancelled.connect(self._on_selection_cancelled)
            
            # Start event loop
            self.result = None
            app.exec()
            
            return self.result
            
        except Exception as e:
            print(f"Region selection error: {e}")
            return None
    
    def paintEvent(self, event):
        """Paint the overlay with darkened background and bright selection"""
        painter = QPainter(self)
        
        # Draw darkened screenshot background
        darkened_pixmap = QPixmap(self.screenshot_pixmap.size())
        darkened_pixmap.fill(QColor(0, 0, 0, 128))
        
        painter.drawPixmap(0, 0, self.screenshot_pixmap)
        painter.drawPixmap(0, 0, darkened_pixmap)
        
        # Draw selection area if exists
        if not self.selection_rect.isEmpty():
            # Draw bright selection area
            selection_pixmap = self.screenshot_pixmap.copy(self.selection_rect)
            painter.drawPixmap(self.selection_rect.topLeft(), selection_pixmap)
            
            # Draw selection border
            pen = QPen(QColor(0, 255, 0), 3)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)
            
            # Draw corner handles
            handle_size = 8
            brush = QBrush(QColor(0, 255, 0))
            painter.setBrush(brush)
            
            corners = [
                self.selection_rect.topLeft(),
                self.selection_rect.topRight(),
                self.selection_rect.bottomLeft(),
                self.selection_rect.bottomRight()
            ]
            
            for corner in corners:
                handle_rect = QRect(
                    corner.x() - handle_size//2,
                    corner.y() - handle_size//2,
                    handle_size,
                    handle_size
                )
                painter.fillRect(handle_rect, brush)
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.drawRect(handle_rect)
                painter.setPen(pen)
            
            # Draw dimensions
            width = self.selection_rect.width()
            height = self.selection_rect.height()
            
            font = QFont("Arial", 12, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(QColor(255, 255, 255)))
            
            text = f"{width} × {height}"
            text_rect = painter.fontMetrics().boundingRect(text)
            text_pos = QPoint(
                self.selection_rect.center().x() - text_rect.width()//2,
                self.selection_rect.top() - 10
            )
            
            # Draw text background
            bg_rect = QRect(text_pos.x() - 5, text_pos.y() - text_rect.height() - 5,
                           text_rect.width() + 10, text_rect.height() + 10)
            painter.fillRect(bg_rect, QBrush(QColor(0, 0, 0, 180)))
            
            painter.drawText(text_pos, text)
        
        # No instruction text when no selection
        if self.selection_rect.isEmpty():
            return
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selecting = True
            self._hide_toolbar()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if self.selecting:
            self.end_point = event.pos()
            self._update_selection_rect()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.end_point = event.pos()
            self._update_selection_rect()
            self.update()
            
            if not self.selection_rect.isEmpty():
                self._show_toolbar()
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key_Escape:
            self._cancel_selection()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._confirm_selection()
    
    def _update_selection_rect(self):
        """Update selection rectangle"""
        self.selection_rect = QRect(self.start_point, self.end_point).normalized()

    def _icon_text(self, name: str, fallback: str):
        """Return material icon text if available, otherwise fallback"""
        return name if self.material_font_available else fallback
    
    def _show_toolbar(self):
        """Show floating toolbar"""
        if self.toolbar:
            self.toolbar.hide()
            self.toolbar.deleteLater()
        
        self.toolbar = QWidget(self)
        self.toolbar.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.toolbar.setStyleSheet("""
            QWidget {
                background-color: rgba(33, 33, 33, 205);
                border-radius: 10px;
            }
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                padding: 8px 12px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.10);
            }
            QPushButton#primary { color: #C8E6C9; }   /* Done */
            QPushButton#accent  { color: #BBDEFB; }   /* Save */
            QPushButton#danger  { color: #FFCDD2; }   /* Cancel */
        """)
        effect = QGraphicsDropShadowEffect(self.toolbar)
        effect.setBlurRadius(20)
        effect.setOffset(0, 4)
        effect.setColor(QColor(0, 0, 0, 180))
        self.toolbar.setGraphicsEffect(effect)
        
        layout = QHBoxLayout(self.toolbar)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Build buttons with icons rendered by icon manager
        def make_icon(name: str, size: int = 18, rgba=(255, 255, 255, 255)):
            cfg = RenderConfig(size=size, color=rgba, background=None)
            img = self.icon_manager.render_icon(name, cfg)
            qimage = ImageQt.ImageQt(img)
            return QPixmap.fromImage(qimage)

        confirm_btn = QPushButton("Copy")
        confirm_btn.setObjectName("primary")
        confirm_btn.setToolTip("Confirm and copy to clipboard (Enter)")
        confirm_btn.setIcon(make_icon("done", 18))
        confirm_btn.setIconSize(QSize(18, 18))
        confirm_btn.clicked.connect(self._confirm_selection)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.setToolTip("Save to file")
        save_btn.setIcon(make_icon("save", 18))
        save_btn.setIconSize(QSize(18, 18))
        save_btn.clicked.connect(self._save_selection)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("danger")
        cancel_btn.setToolTip("Cancel (ESC)")
        cancel_btn.setIcon(make_icon("close", 18))
        cancel_btn.setIconSize(QSize(18, 18))
        cancel_btn.clicked.connect(self._cancel_selection)

        layout.addWidget(confirm_btn)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        
        # Position toolbar below selection
        toolbar_x = max(10, min(self.selection_rect.left(), self.width() - 200))
        toolbar_y = min(self.selection_rect.bottom() + 10, self.height() - 60)
        
        self.toolbar.move(toolbar_x, toolbar_y)
        self.toolbar.show()
    
    def _hide_toolbar(self):
        """Hide toolbar"""
        if self.toolbar:
            self.toolbar.hide()
    
    def _confirm_selection(self):
        """Confirm selection"""
        if not self.selection_rect.isEmpty():
            rect = (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
            # default action: copy to clipboard
            self.selection_completed.emit((rect, "copy"))
        else:
            self.selection_cancelled.emit()
    
    def _save_selection(self):
        """Save selection with dialog"""
        if not self.selection_rect.isEmpty():
            rect = (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
            self.selection_completed.emit((rect, "save"))
        else:
            self.selection_cancelled.emit()
    
    def _cancel_selection(self):
        """Cancel selection"""
        self.selection_cancelled.emit()
    
    def _on_selection_completed(self, rect):
        """Handle selection completion"""
        self.result = rect
        self._close_app()
    
    def _on_selection_cancelled(self):
        """Handle selection cancellation"""
        self.result = None
        self._close_app()
    
    def _close_app(self):
        """Close application"""
        if self.toolbar:
            self.toolbar.close()
        self.close()
        
        app = QApplication.instance()
        if app:
            QTimer.singleShot(100, app.quit)