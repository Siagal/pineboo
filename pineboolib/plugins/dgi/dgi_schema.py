# # -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui

from xml.etree.ElementTree import fromstring
from json import dumps

from pineboolib.utils import DefFun
import pineboolib
import sys
import datetime
import re


class dgi_schema(object):

    _desktopEnabled = False
    _mLDefault = False
    _name = None
    _alias = None
    _localDesktop = True

    def __init__(self):
        self._desktopEnabled = True  # Indica si se usa en formato escritorio con interface Qt
        self.setUseMLDefault(True)
        self.setLocalDesktop(True)
        self._name = "dgi_shema"
        self._alias = "Default Schema"
        self.loadReferences()
        self.parserDGI = parserJson()

    def name(self):
        return self._name

    def alias(self):
        return self._alias

    # Establece un lanzador alternativo al de la aplicación
    def alternativeMain(self, options):
        pass

    def useDesktop(self):
        return self._desktopEnabled

    def setUseDesktop(self, val):
        self._desktopEnabled = val

    def localDesktop(self):  # Indica si son ventanas locales o remotas a traves de algún parser
        return self._localDesktop

    def setLocalDesktop(self, val):
        self._localDesktop = val

    def setUseMLDefault(self, val):
        self._mLDefault = val

    def useMLDefault(self):
        return self._mLDefault

    def setParameter(self, param):  # Se puede pasar un parametro al dgi
        pass

    def extraProjectInit(self):
        pass

    def showInitBanner(self):
        print("")
        print("=============================================")
        print("                 %s MODE               " % self._alias)
        print("=============================================")
        print("")
        print("")

    def mainForm(self):
        pass

    def loadReferences(self):
        self.FLLineEdit = FLLineEdit
        self.FLDateEdit = FLDateEdit
        self.FLTimeEdit = FLTimeEdit
        self.FLPixmapView = FLPixmapView
        self.FLSpinBox = FLSpinBox

        self.QPushButton = QtWidgets.QPushButton
        self.QLineEdit = QLineEdit
        self.QComboBox = QComboBox
        self.QCheckBox = QCheckBox
        self.QTextEdit = QTextEdit

    def AndroidPlatform(self):
        try:
            import PyQt5.QtAndroidExtras
        except ImportError:
            return False

        return True


class FLLineEdit(QtWidgets.QLineEdit):

    _tipo = None
    _partDecimal = 0
    _partInteger = 0
    _maxValue = None
    autoSelect = True
    _name = None
    _longitudMax = None
    _parent = None

    lostFocus = QtCore.pyqtSignal()

    def __init__(self, parent, name=None):
        super(FLLineEdit, self).__init__(parent)
        self._name = name
        if isinstance(parent.fieldName_, str):
            self._fieldName = parent.fieldName_
            self._tipo = parent.cursor_.metadata().fieldType(self._fieldName)
            self._partDecimal = parent.partDecimal_
            self._partInteger = parent.cursor_.metadata().field(self._fieldName).partInteger()
            self._longitudMax = parent.cursor_.metadata().field(self._fieldName).length()
            self._parent = parent

    def __getattr__(self, name):
        return DefFun(self, name)

    def setText(self, texto, b=True):
        if self._maxValue:
            if self._maxValue < int(texto):
                texto = self._maxValue

        texto = str(texto)

        # Miramos si le falta digitos a la parte decimal ...
        if self._tipo == "double" and len(texto) > 0:
            if texto == "0":
                d = 0
                texto = "0."
                while d < self._partDecimal:
                    texto = texto + "0"
                    d = d + 1

            i = None
            l = len(texto) - 1
            try:
                i = texto.index(".")
            except Exception:
                pass

            if i:
                # print("Posicion de . (%s) de %s en %s" % (i, l, texto))
                f = (i + self._partDecimal) - l
                # print("Part Decimal = %s , faltan %s" % (self._partDecimal, f))
                while f > 0:
                    texto = texto + "0"
                    f = f - 1

        super(FLLineEdit, self).setText(texto)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setText" % self._parent.objectName(), texto)
        self.textChanged.emit(texto)

    def text(self):
        texto = str(super(FLLineEdit, self).text())

        if texto is None:
            texto = ""

        return str(texto)

    """
    Especifica un valor máximo para el text (numérico)
    """

    def setMaxValue(self, value):
        self._maxValue = value

    """
    def focusInEvent(self, *f):
        print("focus in!! ---> ", f)
        if self._tipo == "double" or self._tipo == "int" or self._tipo == "Uint":
            self.blockSignals(True)
            s = self.text()
            super(FLLineEdit,self).setText(s)
            self.blockSignals(False)
        if self.autoSelect and self.selectedText().isEmpty() and not self.isReadOnly():
            self.selectAll()

        QtGui.QLineEdit.focusInEvent(f)

    def focusOutEvent(self, f):
        print("Adios --->", f)
        if self._tipo == "double" or self._tipo == "int" or self._tipo == "Uint":
            self.setText(self.text())

        super(FLLineEdit,self).focusOutEvent(self, f)

    """


class FLPixmapView(QtWidgets.QWidget):
    frame_ = None
    scrollView = None
    autoScaled_ = None
    path_ = None
    pixmap_ = None
    pixmapView_ = None
    lay_ = None
    gB_ = None
    _parent = None

    def __init__(self, parent):
        super(FLPixmapView, self).__init__(parent)
        # self.scrollView = QtWidgets.QScrollArea(parent)
        self.autoScaled_ = False
        self.lay_ = QtWidgets.QHBoxLayout(self)
        self.pixmap_ = QtGui.QPixmap()
        self.pixmapView_ = QtWidgets.QLabel(self)
        self.lay_.addWidget(self.pixmapView_)
        self._parent = parent

    def setPixmap(self, pix):
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setPixmap" % self._parent.objectName(), self._parent.cursor_.valueBuffer(self._parent.fieldName_))
            return

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.pixmap_ = pix
        if not self.autoScaled_:
            self.resize(self.pixmap_.size().width(),
                        self.pixmap_.size().height())
        self.pixmapView_.clear()
        self.pixmapView_.setPixmap(self.pixmap_)
        self.repaint()
        QtWidgets.QApplication.restoreOverrideCursor()

    def drawContents(self, p, cx, cy, cw, ch):
        p.setBrush(QtGui.QPalette.Background)
        p.drawRect(cx, cy, cw, ch)
        if self.autoScaled_:
            newWidth = self.width() - 2
            newHeight = self.height() - 2

            if self.pixmapWiev_ is not None and self.pixmapView_.width() == newWidth and self.pixmapView_.height() == newHeight:
                return

            img = self.pixmap_
            if img.width() > newWidth or img.height() > newHeight:
                self.pixmapView_.convertFromImage(img.scaled(
                    newWidth, newHeight, QtCore.Qt.KeepAspectRatio))
            else:
                self.pixmapView_.convertFromImage(img)

            if self.pixmapView_ is not None:
                p.drawPixmap((self.width() / 2) - (self.pixmapView_.width() / 2),
                             (self.height() / 2) - (self.pixmapView_.height() / 2), self.pixmapView_)
            elif self.pixmap_ is not None:
                p.drawPixmap((self.width() / 2) - (self.pixmap_.width() / 2),
                             (self.height() / 2) - (self.pixmap_.height() / 2), self.pixmap_)

    def previewUrl(self, url):
        u = QtCore.QUrl(url)
        if u.isLocalFile():
            path = u.path()

        if not path == self.path_:
            self.path_ = path
            img = QtGui.QImage(self.path_)

            if img is None:
                return

            pix = QtGui.QPixmap()
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            pix.convertFromImage(img)
            QtWidgets.QApplication.restoreOverrideCursor()

            if pix is not None:
                self.setPixmap(pix)

    def clear(self):
        self.pixmapView_.clear()

    def pixmap(self):
        return self.pixmap_

    def setAutoScaled(self, autoScaled):
        self.autoScaled_ = autoScaled


class FLDateEdit(QtWidgets.QDateEdit):

    valueChanged = QtCore.pyqtSignal()
    DMY = "dd-MM-yyyy"
    _parent = None

    def __init__(self, parent, name):
        super(FLDateEdit, self).__init__(parent)
        self.setDisplayFormat("dd-MM-yyyy")
        self.setMinimumWidth(120)
        self.setMaximumWidth(120)
        self._parent = parent

    def setOrder(self, order):
        self.setDisplayFormat(order)

    def setDate(self, d=None):
        from pineboolib.qsatype import Date

        if d in (None, "NAN"):
            d = QtCore.QDate.fromString(str("01-01-2000"), "dd-MM-yyyy")
        if isinstance(d, str):
            if "T" in d:
                d = d[:d.find("T")]

        if isinstance(d, Date):
            d = d.date_

        if isinstance(d, datetime.date):
            d = QtCore.QDate.fromString(str(d), "yyyy-MM-dd")

        if not isinstance(d, QtCore.QDate):
            date = QtCore.QDate.fromString(d, "dd-MM-yyyy")
        else:
            date = d

        super(FLDateEdit, self).setDate(date)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setDate" % self._parent.objectName(), date.toString())
        else:
            self.setStyleSheet('color: black')

    def __getattr__(self, name):
        return DefFun(self, name)


class FLTimeEdit(QtWidgets.QTimeEdit):

    def __init__(self, parent):
        super(FLTimeEdit, self).__init__(parent)
        self.setDisplayFormat("hh:mm:ss")
        self.setMinimumWidth(90)
        self.setMaximumWidth(90)

    def setTime(self, v):
        if isinstance(v, str):
            v = v.split(':')
            time = QtCore.QTime(int(v[0]), int(v[1]), int(v[2]))
        else:
            time = v

        super(FLTimeEdit, self).setTime(time)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setTime" % self._parent.objectName(), date.toString())

    def __getattr__(self, name):
        return DefFun(self, name)


class FLSpinBox(QtWidgets.QSpinBox):

    def __init__(self, parent=None):
        super(FLSpinBox, self).__init__(parent)
        # editor()setAlignment(Qt::AlignRight);

    def setMaxValue(self, v):
        self.setMaximum(v)


class QComboBox(QtWidgets.QComboBox):

    _parent = None

    def __init__(self, parent=None):
        self._parent = parent
        super(QComboBox, self).__init__(parent)

    def setCurrentIndex(self, n):
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setCurrentIndex" % self._parent.objectName(), n)
        super(QComboBox, self).setCurrentIndex(n)

    def setCurrentText(self, t):
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setCurrentText" % self._parent.objectName(), t)
        super(QComboBox, self).setCurrentText(n)


class QLineEdit(QtWidgets.QLineEdit):

    _parent = None

    def __init__(self, parent):
        self._parent = parent
        super(QLineEdit, self).__init__(parent)

    def setText(self, text):
        super(QLineEdit, self).setText(text)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setText" % self._parent.objectName(), t)


class QTextEdit(QtWidgets.QTextEdit):

    _parent = None

    def __init__(self, parent):
        self._parent = parent
        super(QTextEdit, self).__init__(parent)

    def setText(self, text):
        super(QTextEdit, self).setText(text)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setText" % self._parent.objectName(), text)


class QCheckBox(QtWidgets.QCheckBox):

    _parent = None

    def __init__(self, parent):
        self._parent = parent
        super(QCheckBox, self).__init__(parent)

    def setChecked(self, b):
        super(QCheckBox, self).setChecked(b)
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setChecked" % self._parent.objectName(), b)


"""
Exportador UI a JSON
"""


class parserJson():

    def __init__(self):
        self.aPropsForbidden = ['images', 'includehints', 'layoutdefaults',
                                'slots', 'stdsetdef', 'stdset', 'version', 'spacer', 'connections']
        self.aObjsForbidden = ['geometry', 'sizePolicy', 'margin', 'spacing', 'frameShadow',
                               'frameShape', 'maximumSize', 'minimumSize', 'font', 'focusPolicy', 'iconSet', 'author', 'comment', 'forwards', 'includes', 'sizepolicy', 'horstretch', 'verstretch']

    def isInDgi(self, property, type):
        if type == "prop":
            if property in self.aPropsForbidden:
                return False
            else:
                if property in self.aObjsForbidden:
                    return False

        return True

    def manageProperties(self, obj):
        if isinstance(obj, dict):
            for property in list(obj):
                if self.isInDgi(property, "prop"):
                    if property == "name" and not self.isInDgi(obj[property], "obj"):
                        del obj
                        return None
                    else:
                        prop = self.manageProperties(obj[property])
                        if prop:
                            obj[property] = prop
                        else:
                            del obj[property]
                else:
                    del obj[property]
        elif isinstance(obj, list):
            ind = 0
            while ind < len(obj):
                it = self.manageProperties(obj[ind])
                if it:
                    obj[ind] = it
                    ind += 1
                else:
                    del obj[ind]
        return obj

    def parse(self, name):
        from xmljson import yahoo as xml2json
        inputFile = name
        outputFile = re.search("\w+.ui", inputFile)

        if outputFile is None:
            print("Error. El fichero debe tener extension .ui")
            return None

        # ret_out = outputFile

        outputFile = re.sub(".ui", ".dgi", inputFile)

        try:
            ui = open(inputFile, 'r')
            xml = ui.read()

        except Exception:
            print("Error. El fichero no existe o no tiene formato XML")
            sys.exit()

        json = xml2json.data(fromstring(xml))
        json = self.manageProperties(json)
        strJson = dumps(json, sort_keys=True, indent=2)

        """
        try:
            dgi = open(outputFile, 'w')
            dgi.write(strJson)
            dgi.close()
        except:
            print("Error. Ha habido un problema durante la escritura del fichero")
            return None
        """
        strJson = strJson.replace("\n", "")
        strJson = " ".join(strJson.split())
        return strJson
