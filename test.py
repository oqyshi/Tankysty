from PyQt5.QtWidgets import (QWidget, QInputDialog, QApplication)
import sys

def getUserName(text):
    app = QApplication(sys.argv)
    if text:
        return QInputDialog.getText(QWidget(), 'Игрок ' + text, 'Введите ваше имя')
    else:
        return QInputDialog.getText(QWidget(), 'Продолжить?' + text, 'Что бы продолжить нажмите ОК')

print(getUserName())