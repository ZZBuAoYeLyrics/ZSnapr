from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QFont, QCursor, QLinearGradient, QFontDatabase
import sys
import pyautogui
from PIL import Image, ImageQt
import time
from core.log_sys import get_logger
from modules.qt_manager import get_qt_app
from core.font_manager.icon_manager import MaterialSymbolsTTFManager, RenderConfig, IconVariations

class ModernRegionSelector(QWidget):
    # Enhanced Material Design 3 region selector with smooth performance
    
    selection_completed = Signal(tuple)
    selection_cancelled = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.logger.debug("ModernRegionSelector.__init__")
        
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.selection_rect = QRect()
        self.screenshot_pixmap = None
        self.toolbar = None
        self.result = None
        self.screen_rect = QRect()
        self.material_font_loaded = False
        # Icon manager instance for toolbar icons
        self.icon_manager = MaterialSymbolsTTFManager()
        
        # Enhanced interaction states
        self.dragging = False
        self.resizing = False
        self.resize_handle = None
        self.drag_offset = QPoint()
        self.hover_handle = None
        
        # Handle settings
        self.HANDLE_SIZE = 10
        self.HANDLE_MARGIN = 5
        self.MIN_SELECTION_SIZE = 20
        
        # Material Design colors
        self.MD3_PRIMARY = QColor(103, 80, 164)
        self.MD3_ON_PRIMARY = QColor(255, 255, 255)
        self.MD3_SURFACE = QColor(255, 255, 255)
        self.MD3_ON_SURFACE = QColor(28, 27, 31)
        self.MD3_OUTLINE = QColor(121, 116, 126)
        self.MD3_SUCCESS = QColor(56, 142, 60)
        self.MD3_ERROR = QColor(211, 47, 47)
        
    def select_region(self):
        # Show enhanced region selection overlay
        self.logger.log_qt_event("REGION_SELECTOR_START")
        try:
            self.logger.debug("Getting QApplication through QtManager")
            app = get_qt_app()
            self.logger.debug("Got QApplication instance")
            
            # Get screen geometry for boundary checks
            self.screen_rect = app.primaryScreen().geometry()
            self.logger.debug(f"Screen geometry: {self.screen_rect}")
            
            # Capture screenshot
            self.logger.debug("Taking screenshot with pyautogui")
            screenshot = pyautogui.screenshot()
            self.logger.debug(f"Screenshot size: {screenshot.size}")
            
            qt_image = ImageQt.ImageQt(screenshot)
            self.screenshot_pixmap = QPixmap.fromImage(qt_image)
            self.logger.debug("Screenshot converted to QPixmap")
            
            # Setup fullscreen overlay
            self.logger.debug("Setting up fullscreen overlay")
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
            self.setGeometry(self.screen_rect)
            self.setCursor(QCursor(Qt.CrossCursor))
            
            self.logger.debug("Calling showFullScreen()")
            self.showFullScreen()
            
            # Force process events to ensure window is shown
            self.logger.debug("Processing events to ensure window display")
            app.processEvents()
            
            # Verify window is visible
            if self.isVisible():
                self.logger.log_qt_event("OVERLAY_SHOWN")
            else:
                self.logger.error("Window failed to show properly")
                return None
            
            # Enable smooth mouse tracking
            self.setMouseTracking(True)
            
            # Connect signals - Keep for compatibility but use direct result setting
            self.selection_completed.connect(self._on_selection_completed)
            self.selection_cancelled.connect(self._on_selection_cancelled)
            self.logger.debug("Signals connected")
            
            self.result = None
            
            # Optimized event processing loop for better performance
            self.logger.debug("Starting optimized event processing loop")
            start_time = time.time()
            loop_count = 0
            last_log_time = start_time
            
            while self.result is None and (time.time() - start_time) < 30:
                try:
                    app.processEvents()
                    # Reduced sleep time for higher frame rate
                    time.sleep(0.001)  # 1ms delay for ~1000 FPS potential
                    loop_count += 1
                    
                    current_time = time.time()
                    
                    # Log every 3 seconds to reduce overhead
                    if current_time - last_log_time >= 3.0:
                        elapsed = current_time - start_time
                        fps_estimate = loop_count / elapsed if elapsed > 0 else 0
                        self.logger.debug(f"Event loop: {loop_count} iterations, {elapsed:.2f}s, ~{fps_estimate:.0f} FPS, visible={self.isVisible()}")
                        last_log_time = current_time
                    
                    # Check if window was closed
                    if not self.isVisible():
                        self.logger.debug("Window no longer visible, breaking loop")
                        break
                        
                    # Emergency break with higher threshold
                    if loop_count > 500000:  # Higher threshold for better performance
                        self.logger.warning("Event loop exceeded maximum iterations, breaking")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error in event loop: {e}")
                    break
            
            elapsed_total = time.time() - start_time
            self.logger.debug(f"Event loop finished: {loop_count} iterations, {elapsed_total:.2f}s total")
            self.logger.log_qt_event("REGION_SELECTOR_END", f"Result: {self.result}")
            
            return self.result
            
        except Exception as e:
            self.logger.error(f"Region selection error: {e}")
            self.logger.exception("Region selection exception:")
            return None
    
    def paintEvent(self, event):
        # Highly optimized painting for maximum performance
        painter = QPainter(self)
        
        # Enable high-performance rendering hints
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        # Use composition mode for better performance
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw original screenshot as background
        painter.drawPixmap(0, 0, self.screenshot_pixmap)
        
        # Only redraw changed regions for better performance
        update_rect = event.rect()
        
        # Draw semi-transparent overlay (optimized)
        self._draw_optimized_overlay(painter, update_rect)
        
        if not self.selection_rect.isEmpty():
            # Only draw selection elements if they intersect with update region
            if self.selection_rect.intersects(update_rect):
                self._draw_selection_border(painter)
                self._draw_resize_handles(painter)
                self._draw_info_overlay(painter)
        else:
            # Draw instructions only if needed
            if update_rect.intersects(QRect(0, 0, self.width(), 120)):
                self._draw_instructions(painter)
    
    def _draw_optimized_overlay(self, painter, update_rect):
        # Highly optimized overlay drawing with region clipping
        overlay_color = QColor(0, 0, 0, 120)
        
        if self.selection_rect.isEmpty():
            # No selection - only draw overlay in update region
            painter.fillRect(update_rect, overlay_color)
        else:
            # Only draw overlay parts that intersect with update region
            # Top area
            if self.selection_rect.top() > 0:
                top_rect = QRect(0, 0, self.width(), self.selection_rect.top())
                if top_rect.intersects(update_rect):
                    painter.fillRect(top_rect.intersected(update_rect), overlay_color)
            
            # Bottom area
            if self.selection_rect.bottom() < self.height():
                bottom_rect = QRect(0, self.selection_rect.bottom() + 1, 
                                  self.width(), self.height() - self.selection_rect.bottom() - 1)
                if bottom_rect.intersects(update_rect):
                    painter.fillRect(bottom_rect.intersected(update_rect), overlay_color)
            
            # Left area
            if self.selection_rect.left() > 0:
                left_rect = QRect(0, self.selection_rect.top(), 
                                self.selection_rect.left(), self.selection_rect.height())
                if left_rect.intersects(update_rect):
                    painter.fillRect(left_rect.intersected(update_rect), overlay_color)
            
            # Right area
            if self.selection_rect.right() < self.width():
                right_rect = QRect(self.selection_rect.right() + 1, self.selection_rect.top(),
                                 self.width() - self.selection_rect.right() - 1, self.selection_rect.height())
                if right_rect.intersects(update_rect):
                    painter.fillRect(right_rect.intersected(update_rect), overlay_color)
    
    def _draw_clear_selection(self, painter):
        # Selection area remains completely clear (original screenshot visible)
        # No overlay or highlight in selection area - keep it fully transparent
        pass
    
    def _draw_selection_border(self, painter):
        # Modern selection border
        pen = QPen(self.MD3_PRIMARY, 2)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(self.selection_rect)
        
        # Add outer glow
        glow_pen = QPen(QColor(self.MD3_PRIMARY.red(), self.MD3_PRIMARY.green(), 
                              self.MD3_PRIMARY.blue(), 80), 4)
        painter.setPen(glow_pen)
        painter.drawRect(self.selection_rect.adjusted(-1, -1, 1, 1))
    
    def _draw_resize_handles(self, painter):
        # Draw modern resize handles
        handles = self._get_resize_handles()
        
        for handle_type, handle_rect in handles.items():
            # Handle styling
            if self.hover_handle == handle_type:
                handle_color = self.MD3_PRIMARY
                handle_size = self.HANDLE_SIZE + 2
            else:
                handle_color = QColor(self.MD3_PRIMARY.red(), self.MD3_PRIMARY.green(), 
                                    self.MD3_PRIMARY.blue(), 200)
                handle_size = self.HANDLE_SIZE
            
            # Draw handle shadow
            shadow_rect = QRect(handle_rect.center().x() - handle_size//2 + 1, 
                              handle_rect.center().y() - handle_size//2 + 1,
                              handle_size, handle_size)
            painter.fillRect(shadow_rect, QColor(0, 0, 0, 60))
            
            # Draw main handle
            main_rect = QRect(handle_rect.center().x() - handle_size//2, 
                            handle_rect.center().y() - handle_size//2,
                            handle_size, handle_size)
            painter.fillRect(main_rect, handle_color)
            
            # Add white border
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(main_rect)
    
    def _draw_info_overlay(self, painter):
        # Draw dimensions and position info
        width = self.selection_rect.width()
        height = self.selection_rect.height()
        
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        
        # Main dimensions
        text = f"{width} × {height}"
        text_rect = painter.fontMetrics().boundingRect(text)
        
        # Smart positioning
        info_x = self.selection_rect.center().x() - text_rect.width() // 2
        info_y = max(25, self.selection_rect.top() - 15)
        
        # Ensure info stays on screen
        info_x = max(10, min(info_x, self.width() - text_rect.width() - 10))
        
        # Background
        bg_rect = QRect(info_x - 12, info_y - text_rect.height() - 6,
                       text_rect.width() + 24, text_rect.height() + 12)
        
        painter.fillRect(bg_rect.adjusted(1, 1, 1, 1), QColor(0, 0, 0, 40))  # Shadow
        painter.fillRect(bg_rect, self.MD3_SURFACE)
        painter.setPen(QPen(self.MD3_OUTLINE, 1))
        painter.drawRect(bg_rect)
        
        # Text
        painter.setPen(QPen(self.MD3_ON_SURFACE))
        painter.drawText(QPoint(info_x, info_y), text)
        
        # Position info
        small_font = QFont("Segoe UI", 9)
        painter.setFont(small_font)
        pos_text = f"({self.selection_rect.x()}, {self.selection_rect.y()})"
        painter.setPen(QPen(QColor(self.MD3_ON_SURFACE.red(), self.MD3_ON_SURFACE.green(), 
                                  self.MD3_ON_SURFACE.blue(), 160)))
        painter.drawText(QPoint(info_x, info_y + 16), pos_text)
    
    def _draw_instructions(self, painter):
        return
        font = QFont("Segoe UI", 16, QFont.Medium)
        painter.setFont(font)
        
        instruction = "Click and drag to select region"
        text_rect = painter.fontMetrics().boundingRect(instruction)
        
        text_x = self.width() // 2 - text_rect.width() // 2
        text_y = 60
        
        # Background card
        card_rect = QRect(text_x - 24, text_y - text_rect.height() - 12,
                         text_rect.width() + 48, text_rect.height() + 24)
        
        painter.fillRect(card_rect.adjusted(2, 2, 2, 2), QColor(0, 0, 0, 40))  # Shadow
        painter.fillRect(card_rect, self.MD3_SURFACE)
        painter.setPen(QPen(self.MD3_OUTLINE, 1))
        painter.drawRect(card_rect)
        
        # Main text
        painter.setPen(QPen(self.MD3_ON_SURFACE))
        painter.drawText(QPoint(text_x, text_y), instruction)
        
        # Shortcuts
        small_font = QFont("Segoe UI", 11)
        painter.setFont(small_font)
        shortcuts = "ESC: Cancel • Enter: Confirm • Drag edges to resize"
        shortcuts_rect = painter.fontMetrics().boundingRect(shortcuts)
        shortcuts_x = self.width() // 2 - shortcuts_rect.width() // 2
        
        painter.setPen(QPen(QColor(self.MD3_ON_SURFACE.red(), self.MD3_ON_SURFACE.green(), 
                                  self.MD3_ON_SURFACE.blue(), 140)))
        painter.drawText(QPoint(shortcuts_x, text_y + 30), shortcuts)
    
    def _get_resize_handles(self):
        # Get resize handle rectangles with boundary checks
        if self.selection_rect.isEmpty():
            return {}
        
        handles = {}
        margin = self.HANDLE_MARGIN
        size = self.HANDLE_SIZE
        
        rect = self.selection_rect
        
        # Corner handles
        handles['top_left'] = QRect(rect.left() - margin, rect.top() - margin, size, size)
        handles['top_right'] = QRect(rect.right() - size + margin, rect.top() - margin, size, size)
        handles['bottom_left'] = QRect(rect.left() - margin, rect.bottom() - size + margin, size, size)
        handles['bottom_right'] = QRect(rect.right() - size + margin, rect.bottom() - size + margin, size, size)
        
        # Edge handles
        handles['top'] = QRect(rect.center().x() - size//2, rect.top() - margin, size, size)
        handles['bottom'] = QRect(rect.center().x() - size//2, rect.bottom() - size + margin, size, size)
        handles['left'] = QRect(rect.left() - margin, rect.center().y() - size//2, size, size)
        handles['right'] = QRect(rect.right() - size + margin, rect.center().y() - size//2, size, size)
        
        return handles
    
    def _get_cursor_for_handle(self, handle_type):
        # Return appropriate cursor for handle
        cursors = {
            'top_left': Qt.SizeFDiagCursor,
            'top_right': Qt.SizeBDiagCursor,
            'bottom_left': Qt.SizeBDiagCursor,
            'bottom_right': Qt.SizeFDiagCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
        }
        return cursors.get(handle_type, Qt.ArrowCursor)
    
    def _constrain_to_screen(self, rect):
        # Ensure rectangle stays within screen bounds
        constrained = QRect(rect)
        
        # Constrain position
        if constrained.left() < 0:
            constrained.moveLeft(0)
        if constrained.top() < 0:
            constrained.moveTop(0)
        if constrained.right() > self.screen_rect.width():
            constrained.moveRight(self.screen_rect.width())
        if constrained.bottom() > self.screen_rect.height():
            constrained.moveBottom(self.screen_rect.height())
        
        # Ensure minimum size
        if constrained.width() < self.MIN_SELECTION_SIZE:
            constrained.setWidth(self.MIN_SELECTION_SIZE)
        if constrained.height() < self.MIN_SELECTION_SIZE:
            constrained.setHeight(self.MIN_SELECTION_SIZE)
        
        # Final boundary check
        if constrained.right() > self.screen_rect.width():
            constrained.moveLeft(self.screen_rect.width() - constrained.width())
        if constrained.bottom() > self.screen_rect.height():
            constrained.moveTop(self.screen_rect.height() - constrained.height())
        
        return constrained
    
    def mousePressEvent(self, event):
        # Enhanced mouse press with boundary checks
        if event.button() == Qt.LeftButton:
            if not self.selection_rect.isEmpty():
                # Check for handle interaction
                handles = self._get_resize_handles()
                for handle_type, handle_rect in handles.items():
                    if handle_rect.contains(event.pos()):
                        self.resizing = True
                        self.resize_handle = handle_type
                        self._hide_toolbar()
                        return
                
                # Check for drag interaction
                if self.selection_rect.contains(event.pos()):
                    self.dragging = True
                    self.drag_offset = event.pos() - self.selection_rect.topLeft()
                    self.setCursor(Qt.ClosedHandCursor)
                    self._hide_toolbar()
                    return
            
            # Start new selection
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selecting = True
            self.setCursor(Qt.CrossCursor)
            self._hide_toolbar()
    
    def mouseMoveEvent(self, event):
        # Optimized mouse move handling with minimal redraws
        old_rect = QRect(self.selection_rect)
        
        if self.selecting:
            self.end_point = event.pos()
            self._update_selection_rect()
            # Only update changed regions
            self._update_regions(old_rect, self.selection_rect)
        elif self.resizing and self.resize_handle:
            self._resize_selection(event.pos())
            # Only update changed regions
            self._update_regions(old_rect, self.selection_rect)
        elif self.dragging:
            # Move entire selection with boundary checks
            new_top_left = event.pos() - self.drag_offset
            new_rect = QRect(new_top_left, self.selection_rect.size())
            self.selection_rect = self._constrain_to_screen(new_rect)
            # Only update changed regions
            self._update_regions(old_rect, self.selection_rect)
        else:
            # Handle hover effects with minimal updates
            self._update_hover_state(event.pos())
    
    def _update_regions(self, old_rect, new_rect):
        # Smart region updates to minimize redraws
        if old_rect != new_rect:
            # Calculate union of old and new rects plus some margin for handles/overlay
            margin = 50
            update_rect = old_rect.united(new_rect).adjusted(-margin, -margin, margin, margin)
            
            # Constrain to screen bounds
            screen_rect = QRect(0, 0, self.width(), self.height())
            update_rect = update_rect.intersected(screen_rect)
            
            # Update only the necessary region
            self.update(update_rect)
        else:
            # No change, no update needed
            pass
    
    def mouseReleaseEvent(self, event):
        # Clean mouse release handling
        if event.button() == Qt.LeftButton:
            if self.selecting:
                self.selecting = False
                self.end_point = event.pos()
                self._update_selection_rect()
                if not self.selection_rect.isEmpty():
                    self._show_modern_toolbar()
            elif self.resizing:
                self.resizing = False
                self.resize_handle = None
                if not self.selection_rect.isEmpty():
                    self._show_modern_toolbar()
            elif self.dragging:
                self.dragging = False
                self.setCursor(Qt.ArrowCursor)
                if not self.selection_rect.isEmpty():
                    self._show_modern_toolbar()
            
            self.update()
    
    def _resize_selection(self, pos):
        # Resize with boundary constraints
        if not self.resize_handle:
            return
        
        rect = QRect(self.selection_rect)
        
        if 'left' in self.resize_handle:
            rect.setLeft(pos.x())
        if 'right' in self.resize_handle:
            rect.setRight(pos.x())
        if 'top' in self.resize_handle:
            rect.setTop(pos.y())
        if 'bottom' in self.resize_handle:
            rect.setBottom(pos.y())
        
        # Apply constraints
        self.selection_rect = self._constrain_to_screen(rect.normalized())
    
    def _update_hover_state(self, pos):
        # Smooth hover state updates
        if self.selection_rect.isEmpty():
            self.setCursor(Qt.CrossCursor)
            return
        
        handles = self._get_resize_handles()
        old_hover = self.hover_handle
        self.hover_handle = None
        
        for handle_type, handle_rect in handles.items():
            if handle_rect.contains(pos):
                self.hover_handle = handle_type
                self.setCursor(QCursor(self._get_cursor_for_handle(handle_type)))
                break
        
        if not self.hover_handle:
            if self.selection_rect.contains(pos):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.CrossCursor)
        
        # Only update if hover state changed
        if old_hover != self.hover_handle:
            self.update()
    
    def _update_selection_rect(self):
        # Update selection with constraints
        rect = QRect(self.start_point, self.end_point).normalized()
        self.selection_rect = self._constrain_to_screen(rect)
    
    def keyPressEvent(self, event):
        # Handle keyboard shortcuts - Fixed for immediate response
        if event.key() == Qt.Key_Escape:
            self._cancel_selection()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._confirm_selection()
    
    def _ensure_material_font(self):
        # Try load Material Symbols font once
        if self.material_font_loaded:
            return True
        try:
            font_path = "core/font_manager/icons/MaterialSymbolsOutlined-VariableFont_FILL,GRAD,opsz,wght.ttf"
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                self.material_font_loaded = True
                return True
        except Exception:
            pass
        return False

    def _show_modern_toolbar(self):
        # Enhanced Material Design 3 toolbar with modern icons
        if self.toolbar:
            self.toolbar.hide()
            self.toolbar.deleteLater()
        
        self.toolbar = QWidget(self)
        self.toolbar.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Enhanced Material Design 3 styling with glassmorphism effect
        self.toolbar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 250),
                    stop:1 rgba(248, 250, 252, 240));
                border-radius: 16px;
                border: 1px solid rgba(226, 232, 240, 180);
                backdrop-filter: blur(20px);
            }}
            QPushButton {{
                background-color: transparent;
                color: rgb(51, 65, 85);
                border: none;
                padding: 12px 16px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
                font-family: 'Segoe UI', 'SF Pro Display', system-ui;
                min-width: 80px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 25),
                    stop:1 rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 15));
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background: rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 35);
                transform: translateY(0px);
            }}
            QPushButton#primary {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgb({self.MD3_PRIMARY.red() + 10}, {self.MD3_PRIMARY.green() + 10}, {self.MD3_PRIMARY.blue() + 10}),
                    stop:1 rgb({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}));
                color: rgb({self.MD3_ON_PRIMARY.red()}, {self.MD3_ON_PRIMARY.green()}, {self.MD3_ON_PRIMARY.blue()});
                border: 1px solid rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 100);
                box-shadow: 0 4px 12px rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 40);
            }}
            QPushButton#primary:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgb({self.MD3_PRIMARY.red() + 20}, {self.MD3_PRIMARY.green() + 20}, {self.MD3_PRIMARY.blue() + 20}),
                    stop:1 rgb({self.MD3_PRIMARY.red() + 10}, {self.MD3_PRIMARY.green() + 10}, {self.MD3_PRIMARY.blue() + 10}));
                box-shadow: 0 6px 16px rgba({self.MD3_PRIMARY.red()}, {self.MD3_PRIMARY.green()}, {self.MD3_PRIMARY.blue()}, 60);
            }}
            QPushButton#success {{ 
                color: rgb({self.MD3_SUCCESS.red()}, {self.MD3_SUCCESS.green()}, {self.MD3_SUCCESS.blue()});
                border: 1px solid rgba({self.MD3_SUCCESS.red()}, {self.MD3_SUCCESS.green()}, {self.MD3_SUCCESS.blue()}, 30);
            }}
            QPushButton#success:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({self.MD3_SUCCESS.red()}, {self.MD3_SUCCESS.green()}, {self.MD3_SUCCESS.blue()}, 25),
                    stop:1 rgba({self.MD3_SUCCESS.red()}, {self.MD3_SUCCESS.green()}, {self.MD3_SUCCESS.blue()}, 15));
                border: 1px solid rgba({self.MD3_SUCCESS.red()}, {self.MD3_SUCCESS.green()}, {self.MD3_SUCCESS.blue()}, 60);
            }}
            QPushButton#error {{ 
                color: rgb({self.MD3_ERROR.red()}, {self.MD3_ERROR.green()}, {self.MD3_ERROR.blue()});
                border: 1px solid rgba({self.MD3_ERROR.red()}, {self.MD3_ERROR.green()}, {self.MD3_ERROR.blue()}, 30);
            }}
            QPushButton#error:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({self.MD3_ERROR.red()}, {self.MD3_ERROR.green()}, {self.MD3_ERROR.blue()}, 25),
                    stop:1 rgba({self.MD3_ERROR.red()}, {self.MD3_ERROR.green()}, {self.MD3_ERROR.blue()}, 15));
                border: 1px solid rgba({self.MD3_ERROR.red()}, {self.MD3_ERROR.green()}, {self.MD3_ERROR.blue()}, 60);
            }}
        """)
        
        # Enhanced shadow effect with multiple layers
        effect = QGraphicsDropShadowEffect(self.toolbar)
        effect.setBlurRadius(24)
        effect.setOffset(0, 8)
        effect.setColor(QColor(0, 0, 0, 25))
        self.toolbar.setGraphicsEffect(effect)
        
        layout = QHBoxLayout(self.toolbar)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Build buttons with icons rendered by icon manager
        def make_icon(name: str, size: int = 20, rgba=(51, 65, 85, 255)):
            cfg = RenderConfig(size=size, color=rgba, background=None)
            img = self.icon_manager.render_icon(name, cfg)
            qimage = ImageQt.ImageQt(img)
            return QPixmap.fromImage(qimage)
        
        confirm_btn = QPushButton("Copy")
        confirm_btn.setObjectName("primary")
        confirm_btn.setToolTip("Copy selection to clipboard (Enter)")
        confirm_btn.setIcon(make_icon("content_copy", 20))
        confirm_btn.setIconSize(QSize(20, 20))
        confirm_btn.clicked.connect(self._confirm_selection)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("success")
        save_btn.setToolTip("Save selection to file")
        save_btn.setIcon(make_icon("save", 20))
        save_btn.setIconSize(QSize(20, 20))
        save_btn.clicked.connect(self._save_selection)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("error")
        cancel_btn.setToolTip("Cancel selection (Esc)")
        cancel_btn.setIcon(make_icon("close", 20))
        cancel_btn.setIconSize(QSize(20, 20))
        cancel_btn.clicked.connect(self._cancel_selection)

        layout.addWidget(confirm_btn)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        
        # Smart positioning with enhanced screen boundary checks
        toolbar_width = 280
        toolbar_height = 60
        
        # Center horizontally with screen bounds
        toolbar_x = max(20, min(
            self.selection_rect.center().x() - toolbar_width // 2,
            self.width() - toolbar_width - 20
        ))
        
        # Position below selection with improved spacing, or above if no space
        toolbar_y = self.selection_rect.bottom() + 20
        if toolbar_y + toolbar_height > self.height() - 20:
            toolbar_y = max(20, self.selection_rect.top() - toolbar_height - 20)
        
        self.toolbar.setGeometry(toolbar_x, toolbar_y, toolbar_width, toolbar_height)
        
        # Add entrance animation effect
        self.toolbar.show()
        
        # Optional: Add fade-in animation
        QTimer.singleShot(50, lambda: self.toolbar.setWindowOpacity(1.0))
    
    def _hide_toolbar(self):
        # Hide toolbar
        if self.toolbar:
            self.toolbar.hide()
    
    def _confirm_selection(self):
        # Confirm selection - Fixed to prevent double-click issue
        self.logger.log_qt_event("CONFIRM_SELECTION")
        if not self.selection_rect.isEmpty():
            rect = (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
            self.logger.debug(f"Confirming selection with rect: {rect}")
            # Set result immediately and close
            self.result = (rect, "copy")
            self._close_app()
        else:
            self.logger.debug("Empty selection, cancelling")
            self.result = None
            self._close_app()
    
    def _save_selection(self):
        # Save selection - Fixed to prevent double-click issue
        if not self.selection_rect.isEmpty():
            rect = (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
            self.logger.debug(f"Saving selection with rect: {rect}")
            # Set result immediately and close
            self.result = (rect, "save")
            self._close_app()
        else:
            self.result = None
            self._close_app()
    
    def _cancel_selection(self):
        # Cancel selection - Direct result setting
        self.logger.debug("Cancelling selection")
        self.result = None
        self._close_app()
    
    def _on_selection_completed(self, rect):
        # Handle completion - This method is now unused but kept for compatibility
        self.logger.debug(f"Selection completed with rect: {rect}")
        self.result = rect
        self._close_app()
    
    def _on_selection_cancelled(self):
        # Handle cancellation - This method is now unused but kept for compatibility
        self.logger.debug("Selection cancelled")
        self.result = None
        self._close_app()
    
    def _close_app(self):
        # Clean shutdown without calling app.quit()
        self.logger.debug("Closing region selector")
        if self.toolbar:
            self.logger.debug("Closing toolbar")
            self.toolbar.close()
            self.toolbar = None
        
        # Just close the window, don't quit the app
        self.logger.debug("Closing main window")
        self.close()
        self.logger.log_qt_event("REGION_SELECTOR_CLOSED")