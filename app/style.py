def light_mode(self):
    return """
    QWidget {
        background-color: #FFFFFF;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333333;
    }

    QLabel {
        font-size: 15px;
        font-weight: 600;
        color: #111111;
        padding: 6px 12px;
    }

    QListWidget {
        background-color: #FAFAFA;
        border: none;
        border-radius: 12px;
        padding: 0;
        outline: none;
    }

    QListWidget::item {
        padding: 14px 16px;
        border-bottom: 1px solid #E5E7EB;
        font-size: 14px;
        color: #222222;
        margin-left: 8px;
        margin-right: 8px;
    }

    QListWidget::item:selected {
        background-color: #D0E7FF;
        color: #0B60D8;
        border-radius: 10px;
        margin: 4px 8px;
    }

    QTextEdit {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 16px;
        font-size: 16px;
        color: #111111;
        outline: none;
        selection-background-color: #D0E7FF;
    }

    QSplitter::handle {
        background-color: #E5E7EB;
        width: 4px;
        margin: 0 4px;
        border-radius: 2px;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0px 0px 0px 0px;
    }

    QScrollBar::handle:vertical {
        background: #A3BFFA;
        min-height: 30px;
        border-radius: 4px;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 20px; /* half or more of the button height */
    padding: 10px 30px; /* vertical padding controls height, horizontal for width */
    min-height: 20px;   /* fixed height for consistent rounding */
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.6px;
    box-shadow: 0 4px 12px rgba(0,120,212,0.3);
    }

    QPushButton:hover {
        background-color: #005ea6;
        box-shadow: 0 6px 20px rgba(0,94,166,0.4);
    }

    QPushButton:pressed {
        background-color: #004477;
        box-shadow: 0 2px 8px rgba(0,68,119,0.5);
    }
    """
