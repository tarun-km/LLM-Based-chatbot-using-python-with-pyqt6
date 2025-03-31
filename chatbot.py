import sys
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLabel, QPushButton, 
                            QScrollArea, QFrame, QSplitter, QComboBox, QTextBrowser)
from PyQt6.QtCore import Qt, QSize, QTimer, QMargins
from PyQt6.QtGui import QFont, QColor, QTextOption

class BetterMessage(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Set distinct background colors with proper styling
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E9F5FE; 
                    border-radius: 10px; 
                    padding: 0px;
                    margin: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F8F8F8; 
                    border-radius: 10px; 
                    padding: 0px;
                    margin: 2px;
                }
            """)
        
        # Create layout with proper spacing
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(15, 10, 15, 10)  # Left, Top, Right, Bottom
        
        # Add sender label with explicit text color
        sender = QLabel("You" if is_user else "AI Assistant")
        sender.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                color: #333333; 
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(sender)
        
        # Use QTextBrowser instead of QTextEdit for better word wrapping and rendering
        message = QTextBrowser()
        message.setOpenExternalLinks(True)  # Allow clickable links
        message.setMarkdown(text)
        message.setStyleSheet("""
            QTextBrowser {
                border: none; 
                background-color: transparent; 
                color: #222222;
                selection-background-color: #B0D0E0;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # Configure proper text options
        text_options = message.document().defaultTextOption()
        text_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        message.document().setDefaultTextOption(text_options)
        message.document().setDocumentMargin(0)
        
        # Disable scrollbars but keep text accessible
        message.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        message.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(message)
        
        # Use timer to allow content to be rendered before adjusting size
        QTimer.singleShot(0, lambda: self.adjust_size(message))
    
    def adjust_size(self, text_widget):
        # Ensure the document layout is updated
        text_widget.document().adjustSize()
        
        # Calculate needed height with a little extra padding
        doc_size = text_widget.document().size()
        text_widget.setMinimumHeight(int(doc_size.height()) + 5)
        text_widget.setMaximumHeight(int(doc_size.height()) + 15)
        
        # For very long content, apply a maximum height and enable scrolling
        if doc_size.height() > 500:
            text_widget.setMaximumHeight(500)
            text_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


class ChatbotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.conversation_history = []
        self.api_url = "http://localhost:11434/api/generate"
        
    def initUI(self):
        self.setWindowTitle("Ollama Chatbot")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #F5F5F5;")
        
        # Main widget and layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #F5F5F5; color: #333333;")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Add more space
        main_layout.setSpacing(15)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #333333; font-weight: bold;")
        self.model_selector = QComboBox()
        self.model_selector.addItems(["phi", "phi3", "llama3.1", "mistral", "llama3.2-vision:latest"])
        self.model_selector.setCurrentText("phi")
        self.model_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #5E72E4;
                selection-color: white;
            }
        """)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_selector)
        model_layout.addStretch(1)
        main_layout.addLayout(model_layout)
        
        # Chat area with improved styling
        self.chat_area = QWidget()
        self.chat_area.setObjectName("chatArea")
        self.chat_area.setStyleSheet("""
            #chatArea {
                background-color: white;
                border-radius: 5px;
            }
        """)
        
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(20)  # Increased spacing between messages
        self.chat_layout.setContentsMargins(20, 20, 20, 20)  # More padding
        
        # Scroll area with improved styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.chat_area)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DDDDDD;
                background-color: white;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 12px;
                background-color: white;
                color: #333333;
                font-size: 14px;
            }
        """)
        self.message_input.setMinimumHeight(80)
        self.message_input.setMaximumHeight(120)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #5E72E4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #4A5FCF;
            }
            QPushButton:pressed {
                background-color: #3A4FBF;
            }
        """)
        send_button.setFixedWidth(100)
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        # Add a splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.scroll_area)
        
        input_container = QWidget()
        input_container.setLayout(input_layout)
        
        # Add to main layout
        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(input_container, 0)
        
        self.setCentralWidget(central_widget)
        
        # Welcome message
        self.add_message("Hi! I'm an AI assistant powered by Ollama. How can I help you today?", False)
        
        # Set up event filter for key press
        self.message_input.keyPressEvent = self.handle_key_press
    
    def handle_key_press(self, event):
        # Handle Enter key press to send message, but allow Shift+Enter for new line
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.send_message()
        else:
            # For all other keys, use the default handling
            QTextEdit.keyPressEvent(self.message_input, event)
        
    def add_message(self, text, is_user=True):
        message_widget = BetterMessage(text, is_user)
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to bottom with a delay to ensure layout updates are complete
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        # Ensure we scroll to the bottom of the conversation
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        user_message = self.message_input.toPlainText().strip()
        if not user_message:
            return
            
        # Add user message to UI
        self.add_message(user_message, True)
        
        # Clear input field
        self.message_input.clear()
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Get selected model
        model = self.model_selector.currentText()
        
        # Send to Ollama API and get response
        self.get_ai_response(user_message, model)
    
    def get_ai_response(self, message, model):
        try:
            # Format messages for Ollama
            messages = self.conversation_history.copy()
            
            # Configure the API request payload
            payload = {
                "model": model,
                "prompt": message,
                "stream": False
            }
            
            if len(messages) > 1:
                # If we have conversation history, include it
                formatted_history = ""
                for msg in messages[:-1]:  # Exclude the current message
                    prefix = "User: " if msg["role"] == "user" else "Assistant: "
                    formatted_history += prefix + msg["content"] + "\n"
                
                # Add the current message with context
                payload["prompt"] = formatted_history + "User: " + message + "\nAssistant:"
            
            # Make the API call
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                ai_message = response_data.get("response", "").strip()
                
                # Add AI response to UI and conversation history
                self.add_message(ai_message, False)
                self.conversation_history.append({"role": "assistant", "content": ai_message})
            else:
                error_message = f"Error: {response.status_code} - {response.text}"
                self.add_message(f"```\n{error_message}\n```", False)
                
        except requests.exceptions.ConnectionError:
            self.add_message("Error: Could not connect to Ollama server.\n\nMake sure Ollama is running with the selected model loaded. You can start it with:\n```\nollama run " + self.model_selector.currentText() + "\n```", False)
        except requests.exceptions.Timeout:
            self.add_message("Error: Request to Ollama timed out.\n\nThe model might be taking too long to respond or Ollama might be overloaded.", False)
        except Exception as e:
            self.add_message(f"Error connecting to Ollama: {str(e)}\n\nMake sure Ollama is running with the selected model loaded. You can start it with:\n```\nollama run " + self.model_selector.currentText() + "\n```", False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set app-wide font with better size and explicit color
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    # Default color palette to ensure text is visible
    palette = app.palette()
    palette.setColor(palette.ColorRole.WindowText, QColor("#333333"))
    palette.setColor(palette.ColorRole.Text, QColor("#333333"))
    palette.setColor(palette.ColorRole.ButtonText, QColor("#333333"))
    app.setPalette(palette)
    
    # Set exception hook to catch unhandled exceptions
    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys.__excepthook__(exctype, value, traceback)
    
    sys.excepthook = exception_hook
    
    window = ChatbotUI()
    window.show()
    sys.exit(app.exec())
