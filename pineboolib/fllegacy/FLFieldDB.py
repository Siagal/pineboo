# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtCore import Qt

from pineboolib import decorators
from pineboolib.fllegacy.FLSqlCursor import FLSqlCursor
from pineboolib.utils import DefFun, filedir, aqtt
from pineboolib.fllegacy.FLSettings import FLSettings
from pineboolib.fllegacy.FLUtil import FLUtil
from pineboolib.fllegacy.FLTableMetaData import FLTableMetaData
from pineboolib.fllegacy.FLRelationMetaData import FLRelationMetaData
from pineboolib.fllegacy.FLSqlQuery import FLSqlQuery
from pineboolib.fllegacy.FLManager import FLManager
from pineboolib.fllegacy.FLFormSearchDB import FLFormSearchDB
from pineboolib.fllegacy.FLFormDB import FLFormDB
import datetime
import pineboolib
import logging

DEBUG = False


class FLNotImplemented():
    def __init__(self, *args, **kwargs):
        raise Exception("Not implemented")


class FLFieldDB(QtWidgets.QWidget):
    logger = logging.getLogger("FLFieldDB")
    _loaded = False
    _parent = None

    _tipo = None
    _lineEdit = None
    _partDecimal = None
    autoSelect = False

    editor_ = None  # Editor para el contenido del campo que representa el componente
    fieldName_ = None  # Nombre del campo de la tabla al que esta asociado este componente
    tableName_ = None  # Nombre de la tabla fóranea
    actionName_ = None  # Nombre de la accion
    foreignField_ = None  # Nombre del campo foráneo
    fieldRelation_ = None  # Nombre del campo de la relación
    filter_ = None  # Nombre del campo de la relación
    cursor_ = None  # Cursor con los datos de la tabla origen para el componente
    cursorInit_ = False  # Indica que si ya se ha inicializado el cursor
    cursorAuxInit = None  # Indica que si ya se ha inicializado el cursor auxiliar
    cursorBackup_ = False  # Backup del cursor por defecto para acceder al modo tabla externa
    cursorAux = False  # Cursor auxiliar de uso interno para almacenar los registros de la tabla relacionada con la de origen

    topWidget_ = False
    showed = False
    showAlias_ = True
    datePopup_ = None
    dateFrame_ = None
    datePickedOn_ = False
    autoComPopup_ = None
    autoComFrame_ = None
    accel_ = None
    keepDisabled_ = False
    editorImg_ = None
    pbAux_ = None
    pbAux2_ = None
    pbAux3_ = None
    pbAux4_ = None
    fieldAlias_ = None
    showEditor_ = True
    fieldMapValue_ = None
    autoCompMode_ = "OnDemandF4"
    timerAutoComp_ = False
    textFormat_ = QtCore.Qt.AutoText
    initNotNullColor_ = False
    textLabelDB = None
    FLWidgetFieldDBLayout = None
    name = None

    _refreshLaterEditor = False

    pushButtonDB = None
    keyF4Pressed = QtCore.pyqtSignal()
    labelClicked = QtCore.pyqtSignal()
    keyReturnPressed = QtCore.pyqtSignal()
    lostFocus = QtCore.pyqtSignal()
    textChanged = QtCore.pyqtSignal(str)
    keyF2Pressed = QtCore.pyqtSignal()

    firstRefresh = None

    def __init__(self, parent, *args):
        super(FLFieldDB, self).__init__(parent)

        self.maxPixImages_ = FLSettings().readEntry("maxPixImages", None)
        if self.maxPixImages_ is None:
            self.maxPixImages_ = 600

        self.topWidget_ = parent
        # self._parent = parent

        self.FLLayoutH = QtWidgets.QVBoxLayout(self)
        self.FLLayoutH.setContentsMargins(0, 0, 0, 0)
        self.FLLayoutH.setSpacing(0)
        self.FLLayoutH.setContentsMargins(0, 0, 0, 0)
        # self.FLLayoutH.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)

        self.lytButtons = QtWidgets.QHBoxLayout()
        self.lytButtons.setContentsMargins(0, 0, 0, 0)
        self.lytButtons.setSpacing(1)
        self.lytButtons.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        # self.lytButtons.SetMinimumSize(22,22)
        # self.lytButtons.SetMaximumSize(22,22)

        self.FLWidgetFieldDBLayout = QtWidgets.QHBoxLayout()
        self.FLWidgetFieldDBLayout.setSpacing(0)
        self.FLWidgetFieldDBLayout.setContentsMargins(0, 0, 0, 0)
        self.FLWidgetFieldDBLayout.setSizeConstraint(
            QtWidgets.QLayout.SetMinAndMaxSize)
        self.FLLayoutH.addLayout(self.lytButtons)
        self.FLLayoutH.addLayout(self.FLWidgetFieldDBLayout)
        self.tableName_ = None
        self.fieldName_ = None
        self.foreignField_ = None
        self.fieldRelation_ = None

        self.textLabelDB = QtWidgets.QLabel()
        self.textLabelDB.setMinimumHeight(16)  # No inicia originalmente aqui
        self.textLabelDB.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        # self.textLabelDB.setFrameShape(QtGui.QFrame.WinPanel)
        self.textLabelDB.setFrameShadow(QtWidgets.QFrame.Plain)
        self.textLabelDB.setLineWidth(0)
        self.textLabelDB.setTextFormat(QtCore.Qt.PlainText)
        self.textLabelDB.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.fieldAlias_ = None
        self.actionName_ = None
        self.filter_ = None

        self.FLWidgetFieldDBLayout.addWidget(self.textLabelDB)

        self.pushButtonDB = pineboolib.project.resolveDGIObject(
            "QPushButton")()
        if pineboolib.project._DGI.localDesktop():
            self.setFocusProxy(self.pushButtonDB)
        # self.pushButtonDB.setFlat(True)
        PBSizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        PBSizePolicy.setHeightForWidth(True)
        self.pushButtonDB.setSizePolicy(PBSizePolicy)
        self.pushButtonDB.setMinimumSize(16, 16)
        self.pushButtonDB.setMaximumSize(24, 24)
        self.pushButtonDB.setFocusPolicy(Qt.NoFocus)
        self.pushButtonDB.setIcon(QtGui.QIcon(
            filedir("../share/icons", "flfielddb.png")))
        # self.FLWidgetFieldDBLayout.addWidget(self.pushButtonDB)
        self.pushButtonDB.clicked.connect(self.searchValue)

        self.timer_1 = QtCore.QTimer(self)
        self.timer_1.singleShot(120, self.loaded)
        self.cursorAux = None

    def __getattr__(self, name):
        return DefFun(self, name)

    def load(self):
        self._loaded = True
        while True:  # Ahora podemos buscar el cursor ... porque ya estamos añadidos al formulario
            parent = getattr(self.topWidget_, "cursor", None)()
            if parent and isinstance(self.topWidget_, FLSqlCursor) or isinstance(self.topWidget_, FLFormDB):
                break
            new_parent = self.topWidget_.parentWidget()
            if new_parent is None:
                self.topWidget_ = None
                print("FLFieldDB : El widget de nivel superior deber ser de la clase FLFormDB o heredar de ella (o fuí demasiado rápido y no lo esperé)")
                break
            self.topWidget_ = new_parent

        if self.topWidget_:
            self.cursor_ = self.topWidget_.cursor()
            # print("Hay topWidget en %s", self)
        if DEBUG:
            if self.cursor_ and self.cursor_.d.buffer_:
                print("*** FLFieldDB::loaded: cursor: %r name: %r at:%r" %
                      (self.cursor_, self.cursor_.curName(), self.cursor_.at()))
                cur_values = [
                    f.value for f in self.cursor_.d.buffer_.fieldList_]
                print("*** cursor Buffer: %r" % cur_values)
            else:
                print("*** FLFieldDB::loaded: SIN cursor ??")

        if not self.name:
            self.setName("FLFieldDB")

        self.cursorBackup_ = False
        self.partDecimal_ = None
        self.initCursor()
        self.initEditor()

    def setName(self, value):
        self.name = str(value)

    """
    Para obtener el nombre de la accion.

    @return Nombre de la accion
    """

    def actionName(self):
        return self.actionName_

    """
    Para establecer el nombre de la accion.

    @param aN Nombre de la accion
    """

    def setActionName(self, aN):
        self.actionName_ = str(aN)

    """
    Para obtener el nombre del campo.

    @return Nombre del campo
    """

    def fieldName(self):
        return self.fieldName_

    """
    Para añadir un filtro al cursor.

    """

    def setFilter(self, f):
        if not self.filter_ == f:
            self.filter_ = f
            self.setMaValue()

    """
    Para obtener el filtro del cursor.

    """

    def filter(self):
        return self.fliter_

    """
    Para establecer el nombre del campo.

    @param fN Nombre del campo
    """

    def setFieldName(self, fN):
        self.fieldName_ = str(fN)

    """
    Para obtener el nombre de la tabla foránea.

    @return Nombre de la tabla
    """

    def tableName(self):
        return self.tableName_

    """
    Para establecer el nombre de la tabla foránea.

    @param fT Nombre de la tabla
    """

    def setTableName(self, fT):

        self.tableName_ = None
        if not fT == "":
            self.tableName_ = fT

    """
    Para obtener el nombre del campo foráneo.

    @return Nombre del campo
    """

    def foreignField(self):
        return self.foreignField_
    """
    Para establecer el nombre del campo foráneo.

    @param fN Nombre del campo
    """

    def setForeignField(self, fN):
        self.foreignField_ = str(fN)

    """
    Para obtener el nombre del campo relacionado.

    @return Nombre del campo
    """

    def fieldRelation(self):
        return self.fieldRelation_

    """
    Para establecer el nombre del campo relacionado.

    @param fN Nombre del campo
    """

    def setFieldRelation(self, fN):
        self.fieldRelation_ = str(fN)

    """
    Para establecer el alias del campo, mostrado en su etiqueta si showAlias es true

    @param alias Alias del campo, es el valor de la etiqueta. Si es vacio no hace nada.
    """

    def setFieldAlias(self, alias):
        if alias:
            self.fieldAlias_ = alias
            if self.showAlias_:
                self.textLabelDB.setText(self.fieldAlias_)

    """
    Establece el formato del texto

    @param f Formato del campo
    """

    def setTextFormat(self, f):
        self.textFormat_ = f
        ted = self.editor_
        if isinstance(ted, pineboolib.project.resolveDGIObject("QTextEdit")):
            ted.setTextFormat(self.textFormat_)

    def textFormat(self):
        """@return El formato del texto."""
        ted = self.editor_
        if isinstance(ted, pineboolib.project.resolveDGIObject("QTextEdit")):
            return ted.textFormat()
        return self.textFormat_

    def setEchoMode(self, m):
        """Establece el modo de "echo".

        @param m Modo (Normal, NoEcho, Password)
        """
        led = self.editor_
        if isinstance(led, pineboolib.project.resolveDGIObject("QLineEdit")):
            led.setEchoMode(m)

    def echoMode(self):
        """Returns the echo mode.

        @return El mode de "echo" (Normal, NoEcho, Password)
        """
        led = self.editor_
        if isinstance(led, pineboolib.project.resolveDGIObject("QLineEdit")):
            return led.echoMode()
        return pineboolib.project.resolveDGIObject("QLineEdit").Normal

    def _process_autocomplete_events(self, event):
        timerActive = False
        if self.autoComFrame_ and self.autoComFrame_.isVisible():
            if event.key() == Qt.Key_Down and self.autoComPopup_:
                self.autoComPopup_.setQuickFocus()
                return True

            # --> WIN
            if self.editor_:
                self.editor_.releaseKeyboard()
            if self.autoComPopup_:
                self.autoComPopup_.releaseKeyboard()
            # <-- WIN

            self.autoComFrame_.hide()
            if self.editor_ and event.key() == Qt.Key_Backspace:
                self.editor_.backspace()

            if not self.timerAutoComp_:
                self.timerAutoComp_ = QtCore.QTimer(self)
                self.timerAutoComp_.timeout.connect(
                    self.toggledAutoCompletion)
            else:
                self.timerAutoComp_.stop()

            if not event.key() == Qt.Key_Enter and not event.key() == Qt.Key_Return:
                timerActive = True
                self.timerAutoComp_.start(500)
            else:
                timer = QtCore.QTimer(self)
                timer.singleShot(0, self.autoCompletionUpdateValue)
                return True
        if not timerActive and self.autoCompMode_ == "AlwaysAuto" and not (self.autoComFrame_ or self.autoComFrame_.isvisible()):
            if event.key() in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_ydiaeresis):
                if not self.timerAutoComp_:
                    self.timerAutoComp_ = QtCore.QTimer(self)
                    self.timerAutoComp_.timeout.connect(
                        self.toggledAutoCompletion)
                else:
                    self.timerAutoComp_.stop()

            if not event.key() == Qt.Key_Enter and not event.key() == Qt.Key_Return:
                timerActive = True
                self.timerAutoComp_.start(500)
            else:
                timer.singleShot(0, self.autoCompletionUpdateValue)
                return True

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(int)
    def eventFilter(self, obj, event):
        """Process Qt events for keypresses.

        Filtro de eventos
        """
        if not obj:
            return True

        QtWidgets.QWidget.eventFilter(self, obj, event)
        if event.type() == QtCore.QEvent.KeyPress:
            k = event
            if self._process_autocomplete_events(event):
                return True
            if isinstance(obj, pineboolib.project.resolveDGIObject("FLLineEdit")):
                if k.key() == Qt.Key_F4:
                    self.keyF4Pressed()
                    return True
            elif isinstance(obj, pineboolib.project.resolveDGIObject("QTextEdit")):
                if k.key() == Qt.Key_F4:
                    self.keyF4Pressed()
                    return True
                return False

            if k.key() == Qt.Key_Enter or k.key() == Qt.Key_Return:
                self.focusNextPrevChild(True)
                self.keyReturnPressed.emit()
                return True

            if k.key() == Qt.Key_Up:
                self.focusNextPrevChild(False)
                return True

            if k.key() == Qt.Key_Down:
                self.focusNextPrevChild(True)
                return True

            if k.key() == Qt.Key_F2:
                self.keyF2Pressed.emit()
                return True

            return False

        # elif isinstance(event, QtCore.QEvent.MouseButtonRelease) and
        # isinstance(obj,self.textLabelDB) and event.button() == Qt.LeftButton:
        elif event.type() == QtCore.QEvent.MouseButtonRelease and isinstance(obj, type(self.textLabelDB)) and event.button() == Qt.LeftButton:
            self.emitLabelClicked()
        else:
            return False

    @QtCore.pyqtSlot()
    def updateValue(self, data=None):
        """Actualiza el valor del campo con una cadena de texto.

        @param t Cadena de texto para actualizar el campo
        """
        # print("Update Value", type(data), type(self.editor_))
        # if isinstance(data, QString): #Para quitar en el futuro
        #   data = str(data)
        if not self.cursor_:
            return

        isNull = False

        """
        if data is None:
            if not self.cursor_:
                return
            #ted = self.editor_
            data = self.editor_
            print("Tipo ...", type(data))
            if isinstance(data, FLLineEdit):
                t = self.editor_.text()

            elif isinstance(data, QtGui.QTextEdit):
                t = str(self.editor_.toPlainText())

            elif isinstance(data, FLDateEdit):
                t = str(self.editor_.date().toString(Qt.ISODate))

            #else:
                #return

            if not self.cursor_.bufferIsNull(self.fieldName_):
                if t == self.cursor_.valueBuffer(self.fieldName_):
                    return
            else:
                if not t:
                    return

            if not t:
                self.cursor_.setValueBuffer(self.fieldName_, None)
            else:
                self.cursor_.setValueBuffer(self.fieldName_, t)

        """
        if isinstance(self.editor_, pineboolib.project.resolveDGIObject("FLDateEdit")):
            data = str(self.editor_.date().toString("yyyy-MM-dd"))
            if not data:
                isNull = True

            if not self.cursor_.bufferIsNull(self.fieldName_):

                if str(data) == self.cursor_.valueBuffer(self.fieldName_):
                    return
            elif isNull:
                return

            if isNull:
                self.cursor_.setValueBuffer(self.fieldName_, str(
                    QtCore.QDate().toString("dd-MM-yyyy")))
            else:
                self.cursor_.setValueBuffer(self.fieldName_, data)

        elif isinstance(self.editor_, pineboolib.project.resolveDGIObject("FLTimeEdit")):
            data = str(self.editor_.time().toString("hh:mm:ss"))

            if not data:
                isNull = True
            if not self.cursor_.bufferIsNull(self.fieldName_):

                if str(data) == self.cursor_.valueBuffer(self.fieldName_):
                    return
            elif isNull:
                return

            if isNull:
                self.cursor_.setValueBuffer(self.fieldName_, str(
                    QtCore.QTime().toString("hh:mm:ss")))
            else:
                self.cursor_.setValueBuffer(self.fieldName_, data)

        elif isinstance(self.editor_, pineboolib.project.resolveDGIObject("QCheckBox")):
            data = bool(self.editor_.checkState())

            if not self.cursor_.bufferIsNull(self.fieldName_):
                if data == bool(self.cursor_.valueBuffer(self.fieldName_)):
                    return

            self.cursor_.setValueBuffer(self.fieldName_, data)

        elif isinstance(self.editor_, pineboolib.project.resolveDGIObject("QTextEdit")):
            data = str(self.editor_.toPlainText())
            if not self.cursor_.bufferIsNull(self.fieldName_):
                if self.cursor_.valueBuffer(self.fieldName_) == data:
                    return

            self.cursor_.setValueBuffer(self.fieldName_, data)

        elif isinstance(self.editor_, pineboolib.project.resolveDGIObject("FLLineEdit")):

            data = self.editor_.text()
            if not self.cursor_.bufferIsNull(self.fieldName_):
                if data == self.cursor_.valueBuffer(self.fieldName_):
                    return

            self.cursor_.setValueBuffer(self.fieldName_, data)

        elif isinstance(self.editor_, pineboolib.project.resolveDGIObject("QComboBox")):
            data = str(self.editor_.currentText())

            if not self.cursor_.bufferIsNull(self.fieldName_):
                if data == self.cursor_.valueBuffer(self.fieldName_):
                    return

            self.cursor_.setValueBuffer(self.fieldName_, str(data))

        elif isinstance(self.editorImg_, pineboolib.project.resolveDGIObject("FLPixmapView")):
            if data == self.cursor_.valueBuffer(self.fieldName_):
                return

            self.cursor_.setValueBuffer(self.fieldName_, data)

        """
        elif isinstance(self.editor_, str) or isinstance(data, int):
            tMD = self.cursor_.metadata()
            if not tMD:
                return
            field = tMD.field(self.fieldName_)
            if not field:
                return

            ol = field.hasOptionsList()
            tAux = data

            if ol and self.editor_:
                tAux = field.optionsList()[data]

            if not self.cursor_.bufferIsNull(self.fieldName_):
                if tAux == self.cursor_.valueBuffer(self.fieldName_):
                    return

            elif not tAux:
                return


            s = tAux
            if field.type() == "string" and not ol:
                if len(s) > 1 and s[0] == " ":
                    self.cursor_.bufferChanged.disconnect(self.refreshQuick)
                    self.cursor.setValueBuffer(self.fieldName_, s[1:])
                    self.cursor_.bufferChanged.connect(self.refreshQuick)
                    return

            if self.editor_ and (field.type() == "double" or field.type() == "int" or field.type() == "uint"):
                s = self.editor_.text()

            if s:
                self.cursor_.setValueBuffer(self.fieldName_, s)
            else:
                self.cursor_.setValueBuffer(self.fieldName_, "")
        """
        # if self.isVisible() and self.hasFocus() and field.type() == "string" and field.length() == len(s):
        # self.focusNextPrevChild(True)

    def status(self):
        print("****************STATUS**************")
        print("FLField:", self.fieldName_)
        print("FieldAlias:", self.fieldAlias_)
        print("FieldRelation:", self.fieldRelation_)
        print("Cursor:", self.cursor_)
        if self.cursor_:
            print("CurName:", self.cursor().curName())
        print("Editor: %s, EditorImg: %s" % (self.editor_, self.editorImg_))
        print("RefreshLaterEditor:", self._refreshLaterEditor)
        print("************************************")

    """
    Establece el valor contenido en elcampo.

    @param v Valor a establecer
    """

    def setValue(self, v):
        if not self.cursor_:
            print("FLFieldDB(%s):ERROR: El control no tiene cursor todavía. (%s)" % (
                self.fieldName_, self))
            return
        # if v:
        #    print("FLFieldDB(%s).setValue(%s) ---> %s" % (self.fieldName_, v, self.editor_))

        if v == "":
            v = None

        tMD = self.cursor_.metadata()
        if not tMD:
            return

        field = tMD.field(self.fieldName_)
        if not field:
            print("FLFieldDB::setValue(%s) : No existe el campo " %
                  self.fieldName_)
            return

        type_ = field.type()
        # v = QVariant(cv)
        if field.hasOptionsList():
            idxItem = -1
            if type_ == "string":
                idxItem = field.optionsList().findIndex(v)
            if idxItem == -1:
                self.editor_.setCurrentItem(v)
            self.updateValue(self.editor_.currentText())
            return

        """
        fltype_ = None

        if type_ == "int" or type_ == "double" or type_ == "time" or type_ == "date" or type_ == "bytearray":
            fltype_ = type_
        elif type_ == "serial" or type_ == "uint":
            fltype_ = "uint"
        elif type_ == "bool" or type_ == "unlock":
            fltype_ = "bool"
        elif type_ == "string" or type_ == "pixmap" or type_ == "stringList":
            fltype_ = "string"



        #print("v.type()", v.type())
        if v.type() == "bool" and not fltype_ == "bool":
            if type_ == "double" or type_ == "int" or type_ == "uint":
                v = 0
            else:
                v.clear()

        if v.type() == "string" and v.toString().isEmpty():

            if type_ == "double" or type_ == "int" or type_ == "uint":

                v.clear()

        isNull = False
        if not v.isValid() or v.isNull():
            isNull = True

        if isNull == True and not field.allowNull():
            defVal = field.defaultValue()
            if defVal.isValid() and not defVal.isNull():
                v = defVal
                isNull = False

        #v.cast(fltype_) FIXME

        """
        if type_ == "uint" or type_ == "int" or type_ == "string":
            if self.editor_:
                doHome = False
                if not self.editor_.text():
                    doHome = True
                if v is not None:
                    self.editor_.setText(v)
                else:
                    self.editor_.setText("")

                if doHome:
                    self.editor_.home(False)

        elif type_ == "stringlist":
            if not self.editor_:
                return

            if v is not None:
                self.editor_.setText(v)
            else:
                self.editor_.setText("")

        elif type_ == "double":
            if self.editor_:
                s = None
                if v is not None:
                    if self.partDecimal_:
                        s = round(float(v), self.partDecimal_)
                    else:
                        s = round(float(v), field.partDecimal())
                    self.editor_.setText(str(s))
                else:
                    self.editor_.setText("")

        elif type_ == "serial":
            if self.editor_:
                if v is not None:
                    self.editor_.setText(str(v))
                else:
                    self.editor_.setText("0")

        elif type_ == "pixmap":
            if self.editorImg_:

                if v is None:
                    self.editorImg_.clear()
                    return
                pix = QtGui.QPixmap(v)
                # if not QtGui.QPixmapCache().find(cs.left(100), pix):
                # print("FLFieldDB(%s) :: La imagen no se ha cargado correctamente" % self.fieldName_)
                #    QtGui.QPixmapCache().insert(cs.left(100), pix)
                # print("PIX =", pix)
                if pix:
                    self.editorImg_.setPixmap(pix)
                else:
                    self.editorImg_.clear()

        elif type_ == "date":
            if self.editor_:
                if v is None:
                    self.editor_.setDate(QtCore.QDate())
                elif isinstance(v, str):
                    self.editor_.setDate(QtCore.QDate.fromString(v, "yyyy-MM-dd"))
                else:
                    self.editor_.setDate(v)

        elif type_ == "time":
            if self.editor_:
                if v is None:
                    self.editor_.setTime(QtCore.QTime())
                else:
                    self.editor_.setTime(v)

        elif type == "bool":
            if self.editor_ and v is not None:
                self.editor_.setChecked(v)

    """
    Obtiene el valor contenido en el campo.
    """

    def value(self):
        if not self.cursor_:
            return None

        tMD = self.cursor_.metadata()
        if not tMD:
            return None

        field = tMD.field(self.fieldName_)
        if not field:
            print(FLUtil.tr("FLFieldDB::value() : No existe el campo ") + self.fieldName_)
            return None

        v = None

        if field.hasOptionsList():
            v = int(self.editor_.currentItem())
            return v

        type_ = field.type()
        # fltype = FLFieldMetaData.flDecodeType(type_)
        if self.cursor_.bufferIsNull(self.fieldName_):
            if type_ == "double" or type_ == "int" or type_ == "uint":
                return 0

        if type_ == "double" or type_ == "int" or type_ == "uint" or type_ == "string" or type_ == "stringlist":
            if self.editor_:
                ed_ = self.editor_
                if isinstance(ed_, pineboolib.project.resolveDGIObject("FLLineEdit")):
                    v = ed_.text()

        elif type_ == "serial":
            if self.editor_:
                ed_ = self.editor_
                if isinstance(ed_, pineboolib.project.resolveDGIObject("FLSpinBox")):
                    v = ed_.value()

        elif type_ == "pixmap":
            v = self.cursor_.valueBuffer(self.fieldName_)

        elif type_ == "date":
            if self.editor_:
                v = self.editor_.date().toString(Qt.ISODate)

        elif type_ == "time":
            if self.editor_:
                v = self.editor_.time().toString(Qt.ISODate)

        elif type_ == "bool":
            if self.editor_:
                v = self.editor_.isChecked()

        # v.cast(fltype)
        return v

    """
    Marca como seleccionado el contenido del campo.
    """

    def selectAll(self):
        if not self.cursor_:
            return

        if not self.cursor_.metadata():
            return

        field = self.cursor_.metadata().field(self.fieldName_)
        if not field:
            return
        type_ = field.type()

        if type_ == "double" or type_ == "int" or type_ == "uint" or type_ == "string":
            if self.editor_:
                self.editor_.selectAll()

        elif type_ == "serial":
            if self.editor_:
                self.editor_.selectAll()

    """
    Devuelve el cursor de donde se obtienen los datos. Muy util
    para ser usado en el modo de tabla externa (fieldName y tableName
    definidos, foreingField y fieldRelation en blanco).
    """

    def cursor(self):
        return self.cursor_

    """
    Devuelve el valor de la propiedad showAlias. Esta propiedad es
    usada para saber si hay que mostrar el alias cuando se está
    en modo de cursor relacionado.
    """

    def showAlias(self):
        return self.showAlias_

    """
    Establece el estado de la propiedad showAlias.
    """

    def setShowAlias(self, value):
        if not self.showAlias_ == value:
            self.showAlias_ = value
            if self.showAlias_:
                self.textLabelDB.show()
            else:
                self.textLabelDB.hide()

    """
    Inserta como acelerador de teclado una combinación de teclas, devolviendo su identificador

    @param key Cadena de texto que representa la combinación de teclas (p.e. "Ctrl+Shift+O")
    @return El identificador asociado internamente a la combinación de teclas aceleración insertada
    """
    @decorators.NotImplementedWarn
    def insertAccel(self, key):  # FIXME
        return None
        """
        if not self.accel_:
            self.accel_ = QtCore.QAccel(self.editor_)
            connect(accel_, SIGNAL(activated(int)), this, SLOT(emitActivatedAccel(int)));#FIXME

        id = self.accel_.findKey(QtCore.QKeySequence(key))

        if not id == -1:
            return
        id = self.accel_.insertItem(QtCore.QKeySequence(key))
        return id
        """

    """
    Elimina, desactiva, una combinación de teclas de aceleración según su identificador.

    @param identifier Identificador de la combinación de teclas de aceleración
    """
    @decorators.NotImplementedWarn
    def removeAccel(self, identifier):  # FIXME
        if not self.accel_:
            return
        self.accel_.removeItem(identifier)

    """
    Establece la capacidad de mantener el componente deshabilitado ignorando posibles
    habilitaciones por refrescos. Ver FLFieldDB::keepDisabled_ .

    @param keep TRUE para activar el mantenerse deshabilitado y FALSE para desactivar
    """

    def setKeepDisabled(self, keep):
        self.keepDisabled_ = keep

    """
    Devuelve el valor de la propiedad showEditor.
    """

    def showEditor(self):
        return self.showEditor_

    """
    Establece el valor de la propiedad showEditor.
    """

    def setShowEditor(self, show):
        self.showEditor_ = show
        ed = QtWidgets.QWidget()
        if self.editor_:
            ed = self.editor_
        elif self.editorImg_:
            ed = self.editorImg_

        if ed:
            if show:
                ed.show()
            else:
                ed.hide()

    """
    Establece el número de decimales
    """

    def setPartDecimal(self, d):
        self.partDecimal_ = d
        self.refreshQuick(self.fieldName_)
        # self.editor_.setText(self.editor_.text(),False)

    """
    Para asistente de completado automático.
    """

    def setAutoCompletionMode(self, m):
        self.autoCompMode_ = m

    def autoCompletionMode(self):
        return self.autoCompMode_

    """
    Refresca el contenido del campo con los valores del cursor de la tabla origen.

    Si se indica el nombre de un campo sólo "refresca" si el campo indicado
    coincide con la propiedad fieldRelation, tomando como filtro el valor del campo
    fieldRelation de la tabla relacionada. Si no se indica nigún nombre de
    campo el refresco es llevado a cabo siempre.

    @param fN Nombre de un campo
    """
    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot('QString')
    def refresh(self, fN=None):
        if not self.cursor_ or not isinstance(self.cursor_, FLSqlCursor):
            print("FLField.refresh() Cancelado")
            return
        tMD = self.cursor_.metadata()
        if not tMD:
            return

        v = None
        nulo = False
        if not fN:

            v = self.cursor_.valueBuffer(self.fieldName_)
            nulo = self.cursor_.bufferIsNull(self.fieldRelation_)

            # if self.cursor_.cursorRelation():
            # print(1)
            # if self.cursor_.cursorRelation().valueBuffer(self.fieldRelation_) in ("", None):
            # FIXME: Este código estaba provocando errores al cargar formRecord hijos
            # ... el problema es, que posiblemente el cursorRelation entrega información
            # ... errónea, y aunque comentar el código soluciona esto, seguramente esconde
            # ... otros errores en el cursorRelation. Pendiente de investigar más.
            # v = None
            # if DEBUG: print("FLFieldDB: valueBuffer padre vacío.")

        else:
            if not self.cursorAux and fN.lower() == self.fieldRelation_.lower():
                if self.cursor_.bufferIsNull(self.fieldRelation_):
                    return

                field = tMD.field(self.fieldRelation_)
                tmd = FLSqlCursor(field.relationM1().foreignTable()).metadata()
                if not tmd:
                    return

                # if self.topWidget_ and not self.topWidget_.isShown() and not self.cursor_.modeAccess() == FLSqlCursor.Insert:
                #    if tmd and not tmd.inCache():
                #        del tmd
                #    return

                if not field:
                    if tmd and not tmd.inCache():
                        del tmd

                if not field.relationM1():
                    print(
                        "FLFieldDB :El campo de la relación debe estar relacionado en M1")
                    if tmd and not tmd.inCache():
                        del tmd
                    return

                v = self.cursor_.valueBuffer(self.fieldRelation_)
                q = FLSqlQuery()
                q.setForwardOnly(True)
                q.setTablesList(field.relationM1().foreignTable())
                q.setSelect("%s,%s" % (self.foreignField(),
                                       field.relationM1().foreignField()))
                q.setFrom(field.relationM1().foreignTable())
                where = field.formatAssignValue(
                    field.relationM1().foreignField(), v, True)
                filterAc = self.cursor_.filterAssoc(self.fieldRelation_, tmd)
                if filterAc:
                    if not where:
                        where = filterAc
                    else:
                        where += " AND %s" % filterAc

                # if not self.filter_:
                #    q.setWhere(where)
                # else:
                #    q.setWhere(str(self.filter_ + " AND " + where))
                if self.filter_:
                    where = "%s AND %s" % (self.filter_, where)

                q.setWhere(where)
                if q.exec_() and q.next():
                    v0 = q.value(0)
                    v1 = q.value(1)
                    if not v0 == self.value():
                        self.setValue(v0)
                    if not v1 == v:
                        self.cursor_.setValueBuffer(self.fieldRelation_, v1)

                if tmd and not tmd.inCache():
                    del tmd
            return

        field = tMD.field(str(self.fieldName_))
        if not field:
            return
        type_ = field.type()

        if not type_ == "pixmap" and not self.editor_:
            self._refreshLaterEditor = fN
            return

        modeAcces = self.cursor_.modeAccess()
        partDecimal = None
        if self.partDecimal_:
            partDecimal = self.partDecimal_
        else:
            partDecimal = field.partDecimal()
            self.partDecimal_ = field.partDecimal()

        ol = field.hasOptionsList()

        fDis = False

        # if isinstance(v , QString): #Para quitar
        # v = str(v)
        if DEBUG:
            print("FLFieldDB:: refresh fN:%r fieldName:%r v:%s" %
                  (fN, self.fieldName_, repr(v)[:64]))

        if (self.keepDisabled_ or self.cursor_.fieldDisabled(self.fieldName_) or
                (modeAcces == FLSqlCursor.Edit and (field.isPrimaryKey() or tMD.fieldListOfCompoundKey(self.fieldName_))) or
                not field.editable() or modeAcces == FLSqlCursor.Browse):
            fDis = True

        self.setDisabled(fDis)

        if type_ == "double":
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")
            s = None
            if v not in (None, ""):
                s = round(float(v), partDecimal)
                self.editor_.setText(str(s))
            elif not nulo:
                self.editor_.setText(field.defaultValue())

            self.editor_.textChanged.connect(self.updateValue)

            # if v == None and not nulo:
            #    self.editor_.setText("0.00")

        elif type_ == "string":
            doHome = False
            if not ol:
                try:
                    self.editor_.textChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception(
                        "Error al desconectar señal textChanged")

            if v is not None:
                if ol:
                    if v.find("QT_TRANSLATE") != -1:
                        v = aqtt(v)
                    idx = field.getIndexOptionsList(v)
                    if idx is not None:
                        self.editor_.setCurrentIndex(idx)
                else:
                    self.editor_.setText(v)
            else:
                if ol:
                    self.editor_.setCurrentIndex(0)
                elif not nulo:
                    self.editor_.setText(field.defaultValue())
                else:
                    self.editor_.setText("")

            if not ol and doHome:
                self.editor_.home(False)

            if not ol:
                self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "uint":
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")
            # s = None
            if v is not None:
                self.editor_.setText(str(v))
            elif not nulo:
                self.editor_.setText(field.defaultValue())

            self.editor_.textChanged.connect(self.updateValue)

            if v is None and not nulo:
                self.editor_.setText("0")

        elif type_ == "int":
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")

            if v is not None:
                self.editor_.setText(str(v))
            elif not nulo:
                self.editor_.setText(field.defaultValue())

            self.editor_.textChanged.connect(self.updateValue)

            if v is None and not nulo:
                self.editor_.setText("0")

        elif type_ == "serial":
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")
            self.editor_.setText(str(0))

            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "pixmap":
            if not self.editorImg_:
                self.editorImg_ = pineboolib.project.resolveDGIObject(
                    "FLPixmapView")(self)
                self.editorImg_.setFocusPolicy(Qt.NoFocus)
                self.editorImg_.setSizePolicy(self.sizePolicy())
                self.editorImg_.setMaximumSize(self.maximumSize())
                self.editorImg_.setMinimumSize(self.minimumSize())
                self.editorImg_.setAutoScaled(True)
                # self.FLWidgetFieldDBLayout.removeWidget(self.pushButtonDB)
                self.FLWidgetFieldDBLayout.addWidget(self.editorImg_)
                self.pushButtonDB.hide()

                if field.visible():
                    self.editorImg_.show()
                else:
                    return
                # else:
            # if modeAcces == FLSqlCursor.Browse:
            if field.visible():
                # cs = QString()
                if not v:
                    self.editorImg_.clear()
                    return
                    # cs = v.toString()
                # if cs.isEmpty():
                #    self.editorImg_.clear()
                #    return
                pix = QtGui.QPixmap(v)
                # if not QtGui.QPixmapCache.find(cs.left(100), pix):
                # pix.loadFromData()
                # QtGui.QPixmapCache.insert(cs.left(100), pix)

                if pix:
                    self.editorImg_.setPixmap(pix)
                else:
                    self.editorImg_.clear()

            # if modeAcces == FLSqlCursor.Browse:
                # self.pushButtonDB.setVisible(False)

        elif type_ == "date":
            if self.cursor_.modeAccess() == FLSqlCursor.Insert and nulo and not field.allowNull():
                defVal = field.defaultValue()
                if defVal:
                    defVal = defVal.toDate()
                else:
                    defVal = QtCore.QDate.currentDate()

                self.editor_.setDate(defVal)
                self.updateValue(defVal)

            else:
                try:
                    self.editor_.dateChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception(
                        "Error al desconectar señal textChanged")

                if v:
                    util = FLUtil()
                    v = util.dateDMAtoAMD(v)
                    self.editor_.setDate(v)
                else:
                    self.editor_.setDate()

                self.editor_.dateChanged.connect(self.updateValue)

        elif type_ == "time":
            if self.cursor_.modeAccess() == FLSqlCursor.Insert and nulo and not field.allowNull():
                defVal = field.defaultValue()
                if defVal:
                    defVal = defVal.toTime()
                else:
                    defVal = QtCore.QTime.currentTime()

                self.editor_.setTime(defVal)
                self.updateValue(defVal)

            else:
                try:
                    self.editor_.timeChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception(
                        "Error al desconectar señal timeChanged")

                if v is not None:
                    self.editor_.setTime(v)

                self.editor_.timeChanged.connect(self.updateValue)

        elif type_ == "stringlist":
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal timeChanged")
            if v is not None:
                self.editor_.setText(v)
            else:
                self.editor_.setText(field.defaultValue())
            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "bool":
            try:
                self.editor_.toggled.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal toggled")

            if v is not None:

                self.editor_.setChecked(v)
            else:
                dV = field.defaultValue()
                if dV is not None:
                    self.editor_.setChecked(dV)

            self.editor_.toggled.connect(self.updateValue)

        if not field.visible():
            if self.editor_:
                self.editor_.hide()
            elif self.editorImg_:
                self.editorImg_.hide()
            self.setDisabled(True)

    """
    Refresco rápido
    """
    @QtCore.pyqtSlot('QString')
    def refreshQuick(self, fN=None):
        if not fN or not fN == self.fieldName_ or not self.cursor_:
            return

        tMD = self.cursor_.metadata()
        field = tMD.field(self.fieldName_)

        if not field:
            return

        if field.outTransaction():
            return

        type_ = field.type()

        if not type_ == "pixmap" and not self.editor_:
            return
        v = self.cursor_.valueBuffer(self.fieldName_)
        nulo = self.cursor_.bufferIsNull(self.fieldName_)

        if self.partDecimal_ == -1:
            self.partDecimal_ = field.partDecimal()

        ol = field.hasOptionsList()

        if type_ == "double":
            if str(v) == self.editor_.text():
                return

            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")

            if not nulo:
                self.editor_.setText(v, False)

            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "string":
            doHome = False
            if ol:
                if str(v) == self.editor_.currentText():
                    return
            else:
                if str(v) == self.editor_.text():
                    return

                if not self.editor_.text():
                    doHome = True

            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")

            if v:
                if ol:
                    self.editor_.setCurrentIndex(field.optionsList().index(v))

                else:
                    self.editor_.setText(v, False)

            else:
                if ol:
                    self.editor_.setCurrentIndex(0)

                else:
                    self.editor_.setText("", False)

            if not ol and doHome:
                self.editor_.home(False)

            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "uint" or type_ == "int" or type_ == "serial":
            if v == self.editor_.text():
                return
            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal textChanged")

            if not nulo:
                self.editor_.setText(v)

            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "pixmap":
            if not self.editorImg_:
                self.editorImg_ = pineboolib.project.resolveDGIObject(
                    "FLPixmapView")(self)
                self.editorImg_.setFocusPolicy(QtCore.Qt.NoFocus)
                self.editorImg_.setSizePolicy(self.sizePolicy())
                self.editorImg_.setMaximumSize(self.maximumSize())
                self.editorImg_.setMinimumSize(self.minimumSize())
                self.editorImg_.setAutoScaled(True)
                self.FLWidgetFieldDBLayout.addWidget(self.editorImg_)
                if field.visible():
                    self.editorImg_.show()

            if not nulo:
                if not v:
                    self.editorImg_.clear()
                    return

            pix = QtGui.QPixmap(v)
            # pix.loadFromData(v)

            if pix.isNull():
                self.editorImg_.clear()
            else:
                self.editorImg_.setPixmap(pix)

        elif type_ == "date":
            if v == str(self.editor_.date()):
                return

            try:
                self.editor_.valueChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception(
                    "Error al desconectar señal valueChanged")
            self.editor_.setDate(v)
            self.editor_.valueChanged.connect(self.updateValue)

        elif type_ == "time":
            if v == str(self.editor_.time()):
                return

            try:
                self.editor_.timeChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal")

            self.editor_.setTime(v)
            self.editor_.timeChanged.connect(self.updateValue)

        elif type_ == "stringlist":
            if v == str(self.editor_.toPlainText()):
                return

            try:
                self.editor_.textChanged.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal")

            self.editor_.setText(v)
            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "bool":
            if v == self.editor_.isChecked():
                return

            try:
                self.editor_.toggled.disconnect(self.updateValue)
            except Exception:
                self.logger.exception("Error al desconectar señal")

            self.editor_.setChecked(v)
            self.editor_.toggled.connect(self.updateValue)

    def initCursor(self):
        """
        Inicia el cursor segun este campo sea de la tabla origen o de
        una tabla relacionada
        """

        if self.tableName_ and not self.foreignField_ and not self.fieldRelation_:
            self.cursorBackup_ = self.cursor_
            if self.cursor_:
                self.cursor_ = FLSqlCursor(self.tableName_)
                # FIXME: self.cursor_ = FLSqlCursor(self.tableName_, True, self.cursor_.db().connectionName(), 0, 0, self)
            else:
                if not self.topWidget_:
                    return
                self.cursor_ = FLSqlCursor(self.tableName_)
                # FIXME: self.cursor_ = FLSqlCursor(self.tableName_, True, FLSqlConnections.database().connectionName(), 0, 0, self)
            self.cursor_.setModeAccess(FLSqlCursor.Browse)
            if self.showed:
                try:
                    self.cursor_.cursorUpdated.disconnect(self.refresh)
                except Exception:
                    self.logger.exception("Error al desconectar señal")
            self.cursor_.cursorUpdated.connect(self.refresh)
            return
        else:
            if self.cursorBackup_:
                try:
                    self.cursor_.cursorUpdated.disconnect(self.refresh)
                except Exception:
                    self.logger.exception("Error al desconectar señal")
                self.cursor_ = self.cursorBackup_
                self.cursorBackup_ = False

        if not self.cursor_:
            return

        if not self.tableName_ or not self.foreignField_ or not self.fieldRelation_:
            if self.foreignField_ and self.fieldRelation_:
                if self.showed:
                    try:
                        self.cursor_.bufferChanged.disconnect(self.refresh)
                    except Exception:
                        self.logger.exception("Error al desconectar señal")
                self.cursor_.bufferChanged.connect(self.refresh)

            if self.showed:
                try:
                    self.cursor_.newBuffer.disconnect(self.refresh)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

                try:
                    self.cursor_.bufferChanged.disconnect(self.refreshQuick)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

            self.cursor_.newBuffer.connect(self.refresh)
            self.cursor_.bufferChanged.connect(self.refreshQuick)
            return

        tMD = self.cursor_.db().manager().metadata(self.tableName_)
        if not tMD:
            return

        try:
            self.cursor_.newBuffer.disconnect(self.refresh)
        except TypeError:
            pass

        try:
            self.cursor_.bufferChanged.disconnect(self.refreshQuick)
        except TypeError:
            pass

        self.cursorAux = self.cursor()
        if not self.cursor().metadata():
            return

        curName = self.cursor().metadata().name()

        rMD = tMD.relation(self.fieldRelation_, self.foreignField_, curName)
        if not rMD:
            checkIntegrity = False
            testM1 = self.cursor_.metadata().relation(
                self.foreignField_, self.fieldRelation_, self.tableName_)
            if testM1:
                if testM1.cardinality() == FLRelationMetaData.RELATION_1M:
                    checkIntegrity = True
            fMD = tMD.field(self.fieldRelation_)

            if fMD:
                rMD = FLRelationMetaData(
                    curName, self.foreignField_, FLRelationMetaData.RELATION_1M, False, False, checkIntegrity)

                fMD.addRelationMD(rMD)
                print("FLFieldDB : La relación entre la tabla del formulario ( %s ) y la tabla ( %s ) de este campo ( %s ) no existe, "
                      "pero sin embargo se han indicado los campos de relación( %s, %s)"
                      % (curName, self.tableName_, self.fieldName_, self.fieldRelation_, self.foreignField_))
                print("FLFieldDB : Creando automáticamente %s.%s --1M--> %s.%s" %
                      (self.tableName_, self.fieldRelation_, curName, self.foreignField_))
            else:
                print("FLFieldDB : El campo ( %s ) indicado en la propiedad fieldRelation no se encuentra en la tabla ( %s )" % (
                      self.fieldRelation_, self.tableName_))

        if self.tableName_:
                # self.cursor_ = FLSqlCursor(self.tableName_)
            self.cursor_ = FLSqlCursor(
                self.tableName_, False, self.cursor_.connectionName(), self.cursorAux, rMD, self)

        if not self.cursor_:
            self.cursor_ = self.cursorAux
            if self.showed:
                try:
                    self.cursor_.newBuffer.disconnect(self.refresh)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

                try:
                    self.cursor_.bufferChanged.disconnect(
                        self.refreshQuick)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

            self.cursor_.newBuffer.connect(self.refresh)
            self.cursor_.bufferChanged.connect(self.refreshQuick)
            self.cursorAux = None
            return
        else:
            if self.showed:
                try:
                    self.cursor_.newBuffer.disconnect(self.setNoShowed)
                except Exception:
                    self.logger.exception("Error al desconectar señal")
            self.cursor_.newBuffer.connect(self.setNoShowed)

        self.cursor_.setModeAccess(FLSqlCursor.Browse)
        if self.showed:
            try:
                self.cursor_.newBuffer.disconnect(self.refresh)
            except Exception:
                self.logger.exception("Error al desconectar señal")

            try:
                self.cursor_.bufferChanged.disconnect(self.refreshQuick)
            except Exception:
                self.logger.exception("Error al desconectar señal")

        self.cursor_.newBuffer.connect(self.refresh)
        self.cursor_.bufferChanged.connect(self.refreshQuick)

        # self.cursor_.append(self.cursor_.db().db().recordInfo(self.tableName_).find(self.fieldName_)) #FIXME
        # self.cursor_.append(self.cursor_.db().db().recordInfo(self.tableName_).find(self.fieldRelation_))
        # #FIXME

    def initEditor(self):
        """
        Crea e inicia el editor apropiado para editar el tipo de datos
        contenido en el campo (p.e: si el campo contiene una fecha crea
        e inicia un QDataEdit)
        """
        # print("Inicializando editor", self.fieldName_, self)
        if not self.cursor_:
            return

        # if self.editor_:
        #    del self.editor_
        #    self.editor_ = None

        # if self.editorImg_:
        #    del self.editorImg_
        #    self.editorImg_ = None

        tMD = self.cursor_.metadata()
        if not tMD:
            return

        field = tMD.field(self.fieldName_)
        if not field:
            return

        type_ = field.type()
        # len_ = field.length()
        partInteger = field.partInteger()
        partDecimal = None
        if type_ == "double":
            if self.partDecimal_:
                partDecimal = self.partDecimal_
            else:
                partDecimal = field.partDecimal()
                self.partDecimal_ = field.partDecimal()

        # rX = field.regExpValidator()
        ol = field.hasOptionsList()

        rt = None
        if field.relationM1():
            if not field.relationM1().foreignTable() == tMD.name():
                rt = field.relationM1().foreignTable()

        hasPushButtonDB = False
        self.fieldAlias_ = field.alias()

        self.textLabelDB.setFont(QtWidgets.QApplication.font())
        if not type_ == "pixmap" and not type_ == "bool":
            if not field.allowNull() and field.editable():
                self.textLabelDB.setText("%s*" % self.fieldAlias_)
            else:
                self.textLabelDB.setText(self.fieldAlias_)
        else:
            self.textLabelDB.hide()

        if rt:
            hasPushButtonDB = True
            tmd = self.cursor_.db().manager().metadata(rt)
            if not tmd:
                self.pushButtonDB.setDisabled(True)

            if tmd and not tmd.inCache():
                del tmd

        self.initMaxSize_ = self.maximumSize()
        self.initMinSize_ = self.minimumSize()
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setType" % self.objectName(), type_)
            if self.showAlias():
                pineboolib.project._DGI._par.addQueque("%s_setAlias" % self.objectName(), self.fieldAlias_)

        if type_ == "uint" or type_ == "int" or type_ == "double" or type_ == "string":
            if ol:
                self.editor_ = pineboolib.project.resolveDGIObject(
                    "QComboBox")(self)
                self.editor_.name = "editor"
                self.editor_.setEditable(False)
                # self.editor_.setAutoCompletion(True)
                self.editor_.setSizePolicy(
                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
                self.editor_.setMinimumSize(22, 22)
                self.editor_.setFont(QtWidgets.QApplication.font())
                # if not self.cursor_.modeAccess() == FLSqlCursor.Browse:
                # if not field.allowNull():
                # self.editor_.palette().setColor(self.editor_.backgroundRole(), self.notNullColor())
                # self.editor_.setStyleSheet('background-color:' + self.notNullColor().name())

                olTranslated = []
                olNoTranslated = field.optionsList()
                for olN in olNoTranslated:
                    olTranslated.append(olN)
                self.editor_.addItems(olTranslated)
                if not pineboolib.project._DGI.localDesktop():
                    pineboolib.project._DGI._par.addQueque("%s_setOptionsList" % self.objectName(), olTranslated)
                self.editor_.installEventFilter(self)
                if self.showed:
                    try:
                        self.editor_.activated.disconnect(self.updateValue)
                    except Exception:
                        self.logger.exception("Error al desconectar señal")
                self.editor_.activated.connect(self.updateValue)

            else:
                self.editor_ = pineboolib.project.resolveDGIObject(
                    "FLLineEdit")(self, "editor")
                self.editor_.setFont(QtWidgets.QApplication.font())
                self.editor_.setMinimumSize(22, 22)
                self.editor_._tipo = type_
                self.editor_.partDecimal = partDecimal
                if not self.cursor_.modeAccess() == FLSqlCursor.Browse:
                    if not field.allowNull() and field.editable() and not (type_ == "time" or type_ == "date"):
                        # self.editor_.palette().setColor(self.editor_.backgroundRole(), self.notNullColor())
                        self.editor_.setStyleSheet(
                            'background-color:' + self.notNullColor().name())
                    self.editor_.installEventFilter(self)

                if type_ == "double":
                    self.editor_.setValidator(FLDoubleValidator(
                        None, pow(10, partInteger) - 1, self.editor_))
                    self.editor_.setAlignment(Qt.AlignRight)
                else:
                    if type_ == "uint" or type_ == "int":
                        if type_ == "uint":
                            self.editor_.setValidator(FLUIntValidator(
                                None, pow(10, partInteger) - 1, self.editor_))
                        else:
                            self.editor_.setValidator(FLIntValidator(
                                ((pow(10, partInteger) - 1) * (-1)), pow(10, partInteger) - 1, self.editor_))
                        self.editor_.setAlignment(Qt.AlignRight)
                    else:
                        # self.editor_.setMaxLength(len) FIXME
                        # if not rX.isEmpty():
                            # r = rX
                            # self.editor_.setValidator(QtGui.QRegExpValidator(r, self.editor_))

                        self.editor_.setAlignment(Qt.AlignLeft)

                        self.keyF4Pressed.connect(self.toggleAutoCompletion)
                        if self.autoCompMode_ == "OnDemandF4":
                            self.editor_.setToolTip(
                                "Para completado automático pulsar F4")
                            self.editor_.setWhatsThis(
                                "Para completado automático pulsar F4")
                        elif self.autoCompMode_ == "AlwaysAuto":
                            self.editor_.setToolTip(
                                "Completado automático permanente activado")
                            self.editor_.setWhatsThis(
                                "Completado automático permanente activado")
                        else:
                            self.editor_.setToolTip(
                                "Completado automático desactivado")
                            self.editor_.setWhatsThis(
                                "Completado automático desactivado")

                if self.showed:
                    try:
                        self.editor_.lostFocus.disconnect(self.emitLostFocus)
                        self.editor_.textChanged.disconnect(self.updateValue)
                        self.editor_.textChanged.disconnect(
                            self.emitTextChanged)
                    except Exception:
                        self.logger.exception("Error al desconectar señal")

                self.editor_.lostFocus.connect(self.emitLostFocus)
                self.editor_.textChanged.connect(self.updateValue)
                self.editor_.textChanged.connect(self.emitTextChanged)

                if hasPushButtonDB:
                    if not pineboolib.project._DGI.localDesktop():
                        pineboolib.project._DGI._par.addQueque("%s_setHasPushButton" % self.objectName(), True)
                    if self.showed:
                        try:
                            self.KeyF2Pressed.disconnect(
                                self.pushButtonDB.animateClick())
                            self.labelClicked.disconnect(
                                self.openFormRecordRelation)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")

                    self.keyF2Pressed.connect(
                        self.pushButtonDB.animateClick)  # FIXME
                    self.labelClicked.connect(self.openFormRecordRelation)
                    self.textLabelDB.installEventFilter(self)
                    tlf = self.textLabelDB.font()
                    tlf.setUnderline(True)
                    self.textLabelDB.setFont(tlf)
                    cB = QtGui.QColor(Qt.darkBlue)
                    # self.textLabelDB.palette().setColor(self.textLabelDB.foregroundRole(), cB)
                    self.textLabelDB.setStyleSheet('color:' + cB.name())
                    self.textLabelDB.setCursor(Qt.PointingHandCursor)

            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy(7), QtWidgets.QSizePolicy.Policy(0))
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            self.FLWidgetFieldDBLayout.addWidget(self.pushButtonDB)
            self.FLWidgetFieldDBLayout.addWidget(self.editor_)

        elif type_ == "serial":
            self.editor_ = pineboolib.project.resolveDGIObject(
                "FLLineEdit")(self, "editor")
            self.editor_.setFont(QtWidgets.QApplication.font())
            self.editor_.setMaxValue(pow(10, field.partInteger()) - 1)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy(7), QtWidgets.QSizePolicy.Policy(0))
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            self.FLWidgetFieldDBLayout.addWidget(self.editor_)
            self.editor_.installEventFilter(self)
            self.editor_.setDisabled(True)
            self.editor_.setAlignment(QtCore.Qt.AlignRight)
            self.pushButtonDB.hide()

            if self.showed:
                try:
                    self.editor_.textChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception("Error al desconectar señal")
            self.editor_.textChanged.connect(self.updateValue)

        elif type_ == "pixmap":
            # if not self.cursor_.modeAccess() == FLSqlCursor.Browse:
            if not self.tableName():
                if not self.editorImg_:
                    self.FLWidgetFieldDBLayout.setDirection(
                        QtWidgets.QBoxLayout.Down)
                    self.editorImg_ = pineboolib.project.resolveDGIObject(
                        "FLPixmapView")(self)
                    self.editorImg_.setFocusPolicy(Qt.NoFocus)
                    self.editorImg_.setSizePolicy(self.sizePolicy())
                    self.editorImg_.setMaximumSize(self.maximumSize())
                    self.editorImg_.setMinimumSize(self.minimumSize())
                    self.editorImg_.setAutoScaled(True)
                    self.FLWidgetFieldDBLayout.removeWidget(self.pushButtonDB)
                    self.FLWidgetFieldDBLayout.addWidget(self.editorImg_)
                self.textLabelDB.hide()

                sizePolicy = QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                sizePolicy.setHeightForWidth(True)

                if not self.pbAux3_:
                    spcBut = QtWidgets.QSpacerItem(
                        20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
                    self.lytButtons.addItem(spcBut)
                    self.pbAux3_ = pineboolib.project.resolveDGIObject(
                        "QPushButton")(self)
                    self.pbAux3_.setSizePolicy(sizePolicy)
                    self.pbAux3_.setMinimumSize(22, 22)
                    self.pbAux3_.setFocusPolicy(Qt.NoFocus)
                    self.pbAux3_.setIcon(QtGui.QIcon(
                        filedir("../share/icons", "gtk-open.png")))
                    self.pbAux3_.setText("")
                    self.pbAux3_.setToolTip("Abrir fichero de imagen")
                    self.pbAux3_.setWhatsThis("Abrir fichero de imagen")
                    self.lytButtons.addWidget(self.pbAux3_)
                    if self.showed:
                        try:
                            self.pbAux3_.clicked.disconnect(self.searchPixmap)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")
                    self.pbAux3_.clicked.connect(self.searchPixmap)
                    if not hasPushButtonDB:
                        if self.showed:
                            try:
                                self.KeyF2Pressed.disconnect(
                                    self.pbAux3_.animateClick)
                            except Exception:
                                self.logger.exception(
                                    "Error al desconectar señal")
                        try:
                            self.keyF2Pressed.connect(
                                self.pbAux3_.animateClick)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")

                        self.pbAux3_.setFocusPolicy(Qt.StrongFocus)
                        self.pbAux3_.installEventFilter(self)

                if not self.pbAux4_:
                    self.pbAux4_ = pineboolib.project.resolveDGIObject(
                        "QPushButton")(self)
                    self.pbAux4_.setSizePolicy(sizePolicy)
                    self.pbAux4_.setMinimumSize(22, 22)
                    self.pbAux4_.setFocusPolicy(Qt.NoFocus)
                    self.pbAux4_.setIcon(QtGui.QIcon(
                        filedir("../share/icons", "gtk-paste.png")))
                    self.pbAux4_.setText("")
                    self.pbAux4_.setToolTip(
                        "Pegar imagen desde el portapapeles")
                    self.pbAux4_.setWhatsThis(
                        "Pegar imagen desde el portapapeles")
                    self.lytButtons.addWidget(self.pbAux4_)
                    if self.showed:
                        try:
                            self.pbAux4_.clicked.disconnect(
                                self.setPixmapFromClipboard)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")
                    self.pbAux4_.clicked.connect(self.setPixmapFromClipboard)

                if not self.pbAux_:
                    self.pbAux_ = pineboolib.project.resolveDGIObject(
                        "QPushButton")(self)
                    self.pbAux_.setSizePolicy(sizePolicy)
                    self.pbAux_.setMinimumSize(22, 22)
                    self.pbAux_.setFocusPolicy(Qt.NoFocus)
                    self.pbAux_.setIcon(QtGui.QIcon(
                        filedir("../share/icons", "gtk-clear.png")))
                    self.pbAux_.setText("")
                    self.pbAux_.setToolTip("Borrar imagen")
                    self.pbAux_.setWhatsThis("Borrar imagen")
                    self.lytButtons.addWidget(self.pbAux_)
                    if self.showed:
                        try:
                            self.pbAux_.clicked.disconnect(self.clearPixmap)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")
                    self.pbAux_.clicked.connect(self.clearPixmap)

                if not self.pbAux2_:
                    self.pbAux2_ = pineboolib.project.resolveDGIObject(
                        "QPushButton")(self)
                    savepixmap_ = QtWidgets.QMenu(self.pbAux2_)
                    savepixmap_.addAction("JPG")
                    savepixmap_.addAction("XPM")
                    savepixmap_.addAction("PNG")
                    savepixmap_.addAction("BMP")

                    self.pbAux2_.setMenu(savepixmap_)
                    self.pbAux2_.setSizePolicy(sizePolicy)
                    self.pbAux2_.setMinimumSize(22, 22)
                    self.pbAux2_.setFocusPolicy(Qt.NoFocus)
                    self.pbAux2_.setIcon(QtGui.QIcon(
                        filedir("../share/icons", "gtk-save.png")))
                    self.pbAux2_.setText("")
                    self.pbAux2_.setToolTip("Guardar imagen como...")
                    self.pbAux2_.setWhatsThis("Guardar imagen como...")
                    self.lytButtons.addWidget(self.pbAux2_)
                    if self.showed:
                        try:
                            savepixmap_.triggered.disconnect(self.savePixmap)
                        except Exception:
                            self.logger.exception("Error al desconectar señal")
                    savepixmap_.triggered.connect(self.savePixmap)

                    if hasPushButtonDB:
                        self.pushButtonDB.installEventFilter(self)
                    else:  # lo desactivo si no tiene el control
                        self.pushButtonDB.setDisabled(True)

        elif type_ == "date":
            self.editor_ = pineboolib.project.resolveDGIObject(
                "FLDateEdit")(self, "editor")
            self.editor_.setFont(QtWidgets.QApplication.font())
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            self.FLWidgetFieldDBLayout.insertWidget(1, self.editor_)

            # self.editor_.setOrder(QtGui.QDateEdit.DMY)
            # self.editor_.setAutoAdvance(True)
            # self.editor_.setSeparator("-")
            self.editor_.installEventFilter(self)
            self.pushButtonDB.hide()

            if not self.cursor_.modeAccess() == FLSqlCursor.Browse:
                # if not self.pbAux_:
                #    #self.pbAux_ = QtGui.QPushButton(self)
                #    # self.pbAux_.setFlat(True)
                #    #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7) ,QtGui.QSizePolicy.Policy(0))
                #    # sizePolicy.setHeightForWidth(True)
                #    # self.pbAux_.setSizePolicy(sizePolicy)
                #    #self.pbAux_.setMinimumSize(25, 25)
                #    #self.pbAux_.setMaximumSize(25, 25)
                #    # self.pbAux_.setFocusPolicy(Qt.NoFocus)
                #    # self.pbAux_.setIcon(QtGui.QIcon(filedir("../share/icons","date.png")))
                #    # self.pbAux_.setText("")
                #    #self.pbAux_.setToolTip("Seleccionar fecha (F2)")
                #    #self.pbAux_.setWhatsThis("Seleccionar fecha (F2)")
                #    # self.lytButtons.addWidget(self.pbAux_) FIXME
                #    # self.FLWidgetFieldDBLayout.addWidget(self.pbAux_)
                #    # if self.showed:
                #        # self.pbAux_.clicked.disconnect(self.toggleDatePicker)
                #        # self.KeyF2Pressed_.disconnect(self.pbAux_.animateClick)
                #    # self.pbAux_.clicked.connect(self.toggleDatePicker)
                #    # self.keyF2Pressed_.connect(self.pbAux_.animateClick) #FIXME
                self.editor_.setCalendarPopup(True)

            if self.showed:
                try:
                    self.editor_.dateChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

            self.editor_.dateChanged.connect(self.updateValue)
            if self.cursor_.modeAccess() == FLSqlCursor.Insert and not field.allowNull():
                defVal = field.defaultValue()
                # if not defVal.isValid() or defVal.isNull():
                if not defVal:
                    self.editor_.setDate(QtCore.QDate.currentDate())
                else:
                    self.editor_.setDate(defVal.toDate())

        elif type_ == "time":
            self.editor_ = pineboolib.project.resolveDGIObject(
                "FLTimeEdit")(self)
            self.editor_.setFont(QtWidgets.QApplication.font())
            # self.editor_.setAutoAdvance(True)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            self.FLWidgetFieldDBLayout.addWidget(self.editor_)
            self.editor_.installEventFilter(self)
            self.pushButtonDB.hide()
            if self.showed:
                try:
                    self.editor_.timeChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

            self.editor_.timeChanged.connect(self.updateValue)
            if self.cursor_.modeAccess() == FLSqlCursor.Insert and not field.allowNull():
                defVal = field.defaultValue()
                # if not defVal.isValid() or defVal.isNull():
                if not defVal:
                    self.editor_.setTime(QtCore.QTime.currentTime())
                else:
                    self.editor_.setTime(defVal.toTime())

        elif type_ == "stringlist":

            self.editor_ = pineboolib.project.resolveDGIObject(
                "QTextEdit")(self)
            self.editor_.setFont(QtWidgets.QApplication.font())
            self.editor_.setTabChangesFocus(True)
            self.editor_.setMinimumHeight(120)
            self.editor_.setMaximumHeight(120)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            # ted.setTexFormat(self.textFormat_)

            # if isinstance(self.textFormat_, Qt.RichText) and not self.cursor_.modeAccess() == FLSqlCursor.Browse:
            # self.FLWidgetFieldDBLayout.setDirection(QtGui.QBoxLayout.Down)
            # self.FLWidgetFieldDBLayout.remove(self.textLabelDB)
            # textEditTab_ = AQTextEditBar(self, "extEditTab_", self.textLabelDB) #FIXME
            # textEditTab_.doConnections(ted)
            # self.FLWidgetFieldDBLayout.addWidget(textEditTab_)

            self.FLWidgetFieldDBLayout.addWidget(self.editor_)
            self.editor_.installEventFilter(self)

            if self.showed:
                try:
                    self.editor_.textChanged.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception("Error al desconectar señal")

            self.editor_.textChanged.connect(self.updateValue)

            self.keyF4Pressed.connect(self.toggleAutoCompletion)
            if self.autoCompMode_ == "OnDemandF4":
                self.editor_.setToolTip("Para completado automático pulsar F4")
                self.editor_.setWhatsThis(
                    "Para completado automático pulsar F4")
            elif self.autoCompMode_ == "AlwaysAuto":
                self.editor_.setToolTip(
                    "Completado automático permanente activado")
                self.editor_.setWhatsThis(
                    "Completado automático permanente activado")
            else:
                self.editor_.setToolTip("Completado automático desactivado")
                self.editor_.setWhatsThis("Completado automático desactivado")

        elif type_ == "bool":
            self.editor_ = pineboolib.project.resolveDGIObject(
                "QCheckBox")(self)
            # self.editor_.setName("editor")
            self.editor_.setText(tMD.fieldNameToAlias(self.fieldName_))
            self.editor_.setFont(QtWidgets.QApplication.font())
            self.editor_.installEventFilter(self)

            self.editor_.setMinimumWidth(self.fontMetrics().width(
                tMD.fieldNameToAlias(self.fieldName())) + self.fontMetrics().maxWidth() * 2)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy(7), QtWidgets.QSizePolicy.Policy(0))
            sizePolicy.setHeightForWidth(True)
            self.editor_.setSizePolicy(sizePolicy)
            self.FLWidgetFieldDBLayout.addWidget(self.editor_)

            if self.showed:
                try:
                    self.editor_.toggled.disconnect(self.updateValue)
                except Exception:
                    self.logger.exception("Error al desconectar señal")
            self.editor_.toggled.connect(self.updateValue)

        if self.editor_:
            self.editor_.setFocusPolicy(Qt.StrongFocus)
            self.setFocusProxy(self.editor_)
            self.setTabOrder(self.pushButtonDB, self.editor_)
            if hasPushButtonDB:
                self.pushButtonDB.setFocusPolicy(Qt.NoFocus)
                self.editor_.setToolTip(
                    "Para buscar un valor en la tabla relacionada pulsar F2")
                self.editor_.setWhatsThis(
                    "Para buscar un valor en la tabla relacionada pulsar F2")

        elif self.editorImg_:
            self.editorImg_.setFocusPolicy(Qt.NoFocus)
            if hasPushButtonDB:
                self.pushButtonDB.setFocusPolicy(Qt.StrongFocus)

        if not hasPushButtonDB:
            self.pushButtonDB.hide()

        if self.initMaxSize_.width() < 80:
            self.setShowEditor(False)
        else:
            self.setShowEditor(self.showEditor_)

        if self._refreshLaterEditor:
            self.refresh(self._refreshLaterEditor)
            self._refreshLaterEditor = False

    """
    Borra imagen en campos tipo Pixmap.
    """

    def clearPixmap(self):
        if self.editorImg_:
            self.editorImg_.clear()
            self.cursor_.setValueBuffer(self.fieldName_, None)

    """
    Guarda imagen en campos tipo Pixmap.

    @param fmt Indica el formato con el que guardar la imagen
    """

    def savePixmap(self, f):
        if self.editorImg_:
            ext = f.text().lower()
            filename = "imagen.%s" % ext
            ext = "*.%s" % ext
            util = FLUtil()
            savefilename = QtWidgets.QFileDialog.getSaveFileName(
                self, util.translate("Pineboo", "Guardar imagen como"), filename, ext)
            if savefilename:
                pix = QtGui.QPixmap(self.editorImg_.pixmap())
                QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
                if pix:
                    if not pix.save(savefilename[0]):
                        QtWidgets.QMessageBox.warning(self, util.translate(
                            "Pineboo", "Error"), util.translate("Pineboo", "Error guardando fichero"))

            QtWidgets.QApplication.restoreOverrideCursor()

    """
    Muestra/Oculta el asistente de completado automático.
    """
    @QtCore.pyqtSlot()
    def toggleAutoCompletion(self):
        print("FIXMEEEE: toggleAutoCompletion")
        return

    """
    Actualiza el valor del campo a partir del contenido que
    ofrece el asistente de completado automático.
    """
    @decorators.NotImplementedWarn
    def autoCompletionUpdateValue(self):
        return

    """
    Abre un formulario de edición para el valor seleccionado en su acción correspondiente
    """
    @QtCore.pyqtSlot()
    def openFormRecordRelation(self):
        if not self.cursor_:
            return

        if not self.fieldName_:
            return

        tMD = self.cursor_.metadata()
        if not tMD:
            return

        field = tMD.field(self.fieldName_)
        if not field:
            return

        if not field.relationM1():
            print("FLFieldDB : El campo de búsqueda debe tener una relación M1")
            return

        fMD = field.associatedField()
        a = None

        v = self.cursor_.valueBuffer(field.name())
        if v is None or (fMD and self.cursor_.bufferIsNull(fMD.name())):
            QtWidgets.QMessageBox.warning(QtWidgets.QApplication.focusWidget(
            ), "Aviso", "Debe indicar un valor para %s" % field.alias(), QtWidgets.QMessageBox.Ok)
            return

        mng = FLManager(self.cursor_.db().manager())
        c = FLSqlCursor(field.relationM1().foreignTable(),
                        True, self.cursor_.db().connectionName())
        # c = FLSqlCursor(field.relationM1().foreignTable())
        c.select(mng.formatAssignValue(
            field.relationM1().foreignField(), field, v, True))
        # if c.size() <= 0:
        #    return

        if c.size() <= 0:
            return

        c.next()

        if not self.actionName_:
            a = c.action()
        else:
            a = self.actionName_

        c.setAction(a)

        self.modeAccess = self.cursor_.modeAccess()
        if self.modeAccess == FLSqlCursor.Insert or self.modeAccess == FLSqlCursor.Del:
            self.modeAccess = FLSqlCursor.Edit

        c.openFormInMode(self.modeAccess, False)

    """
    Abre un dialogo para buscar en la tabla relacionada
    """
    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(int)
    def searchValue(self):
        if not self.cursor_:
            return

        if not self.fieldName_:
            return
        tMD = self.cursor_.metadata()
        if not tMD:
            return

        field = tMD.field(self.fieldName_)
        if not field:
            return

        if not field.relationM1():
            print("FLFieldDB : El campo de búsqueda debe tener una relación M1")
            return

        fMD = field.associatedField()

        if fMD:
            if not fMD.relationM1():
                print("FLFieldDB : El campo asociado debe tener una relación M1")
                return
            v = self.cursor_.valueBuffer(fMD.name())
            if v is None or self.cursor_.bufferIsNull(fMD.name()):
                QtWidgets.QMessageBox.warning(QtWidgets.QApplication.focusWidget(
                ), "Aviso", "Debe indicar un valor para %s" % fMD.alias())
                return

            mng = self.cursor_.db().manager()
            c = FLSqlCursor(field.relationM1().foreignTable())
            # c.select(mng.formatAssignValue(fMD.relationM1().foreignField(), fMD, v, True))

            # if c.size() > 0:
            #    c.next()
            if not self.actionName_:
                a = mng.action(field.relationM1().foreignTable())
            else:
                a = mng.action(self.actionName_)
                a.setTable(field.relationM1().foreignField())

            f = FLFormSearchDB(c, a.name(), None)
            f.setWindowModality(QtCore.Qt.ApplicationModal)
            f.setFilter(mng.formatAssignValue(
                fMD.relationM1().foreignField(), fMD, v, True))
        else:
            mng = self.cursor_.db().manager()
            if not self.actionName_:
                a = mng.action(field.relationM1().foreignTable())
                if not a:
                    return
            else:
                a = mng.action(self.actionName_)
                if not a:
                    return
                a.setTable(field.relationM1().foreignTable())
            c = FLSqlCursor(a.table())
            # f = FLFormSearchDB(c, a.name(), self.topWidget_)
            f = FLFormSearchDB(c, c.action(), None)
            f.setWindowModality(QtCore.Qt.ApplicationModal)

        f.setMainWidget()
        """
        lObjs = f.queryList("FLTableDB")
        obj = lObjs.first()
        del lObjs
        objTdb = obj
        if fMD and objTdb:
            objTdb.setTablename(field.relationM1().foreignTable())
            objTdb.setFieldRelation(field.associatedFieldFilterTo())
            objTdb.setForeignField(fMD.relationM1().foreignField())
            if fMD.relationM1().foreignTable() == tMD.name():
                objTdb.setReadOnly(True)

        f.setFilter(self.filter_)
        if f.mainWidget():
            if objTdb:
                curValue = self.value()
                if field.type() == "string" and curValue:
                    objTdb.setInitSearch(curValue)
                    objTdb.putFisrtCol(field.relationM1().foreignField())
                QtCore.QTimer.singleShot(0,objTdb.lineEditSearch, self.setFocus)
        """
        v = f.exec_(field.relationM1().foreignField())
        f.close()
        if c:
            c.deletelater()
        if v:
            # self.setValue("")
            self.setValue(v)

    """
    Abre un dialogo para buscar un fichero de imagen.

    Si el campo no es de tipo Pixmap no hace nada
    """
    @QtCore.pyqtSlot()
    def searchPixmap(self):
        if not self.cursor_ or not self.editorImg_:
            return

        if not self.fieldName_:
            return
        tMD = FLTableMetaData(self.cursor_.metadata())
        if not tMD:
            return

        field = tMD.field(self.fieldName_)

        if not field:
            return
        util = FLUtil()
        if field.type() == "pixmap":
            fd = QtWidgets.QFileDialog(self, util.translate(
                "pineboo", "Elegir archivo"), None, "*")
            fd.setViewMode(QtWidgets.QFileDialog.Detail)
            filename = None
            if (fd.exec_() == QtWidgets.QDialog.Accepted):
                filename = fd.selectedFiles()

            if not filename:
                return
            self.setPixmap(filename[0])

    """
  Carga una imagen en el campo de tipo pixmap
  @param filename: Ruta al fichero que contiene la imagen
    """

    def setPixmap(self, filename):
        img = QtGui.QImage(filename)

        if not img:
            return

        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        pix = QtGui.QPixmap()
        buffer = QtCore.QBuffer()

        if img.width() <= self.maxPixImages_ and img.height() <= self.maxPixImages_:
            pix.convertFromImage(img)
        else:
            newWidth = 0
            newHeight = 0
            if img.width() < img.height():
                newHeight = self.maxPixImages_
                newWidth = round(newHeight * img.width() / img.height())
            else:
                newWidth = self.maxPixImages_
                newHeight = round(newWidth * img.height() / img.width())
            pix.convertFromImage(img.scaled(newWidth, newHeight))

        QtWidgets.QApplication.restoreOverrideCursor()

        if not pix:
            return

        self.editorImg_.setPixmap(pix)
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        buffer.open(QtCore.QBuffer.ReadWrite)
        pix.save(buffer, "XPM")

        QtWidgets.QApplication.restoreOverrideCursor()

        if not buffer:
            return
        s = None

        s = str(buffer.data(), "utf-8")

        # if not QtGui.QPixmapCache.find(s.left(100)):
        #    QtGui.QPixmapCache.insert(s.left(100), pix)
        self.updateValue(s)

    """
  Carga una imagen en el campo de tipo pixmap con el ancho y alto preferido

  @param pixmap: pixmap a cargar en el campo
  @param w: ancho preferido de la imagen
  @param h: alto preferido de la imagen
  @author Silix
    """

    def setPixmapFromPixmap(self, pixmap, w=0, h=0):
        if pixmap.isNull():
            return

        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        pix = QtGui.QPixmap()
        buffer = QtCore.QBuffer()

        img = QtGui.QImage(pixmap.convertToImage())
        if not w == 0 and not h == 0:
            pix.convertFromImage(img.scaled(w, h))
        else:
            pix.convertFromImage(img)

        QtWidgets.QApplication.restoreOverrideCursor()
        if not pix:
            return

        self.editorImg_.setPixmap(pix)
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        buffer.open(QtCore.QBuffer.ReadWrite)
        pix.save(buffer, "XPM")

        QtWidgets.QApplication.restoreOverrideCursor()

        if not buffer:
            return
        s = None

        s = str(buffer.data(), "utf-8")

        # if not QtGui.QPixmapCache.find(s.left(100)):
        #    QtGui.QPixmapCache.insert(s.left(100), pix)
        self.updateValue(s)

    """
  Carga una imagen desde el portapapeles en el campo de tipo pixmap
  @author Silix
    """

    def setPixmapFromClipboard(self, unknown):
        clb = QtWidgets.QApplication.clipboard()
        img = clb.image()

        print(type(img))
        if not isinstance(img, QtGui.QImage):
            return

        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        pix = QtGui.QPixmap()
        buffer = QtCore.QBuffer()

        if img.width() <= self.maxPixImages_ and img.height() <= self.maxPixImages_:
            pix.convertFromImage(img)
        else:
            newWidth = 0
            newHeight = 0
            if img.width() < img.height():
                newHeight = self.maxPixImages_
                newWidth = round(newHeight * img.width() / img.height())
            else:
                newWidth = self.maxPixImages_
                newHeight = round(newWidth * img.height() / img.width())

            pix.convertFromImage(img.scaled(newWidth, newHeight))

        QtWidgets.QApplication.restoreOverrideCursor()

        if not pix:
            return

        self.editorImg_.setPixmap(pix)
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        buffer.open(QtCore.QBuffer.ReadWrite)
        pix.save(buffer, "XPM")

        QtWidgets.QApplication.restoreOverrideCursor()

        if not buffer:
            return
        s = None

        s = str(buffer.data(), "utf-8")

        # if not QtGui.QPixmapCache.find(s.left(100)):
        #    QtGui.QPixmapCache.insert(s.left(100), pix)
        self.updateValue(s)

    """
  Devueve el objeto imagen asociado al campo

  @return imagen asociada al campo
  @author Silix
    """
    @decorators.NotImplementedWarn
    def pixmap(self):
        pix = QtGui.QPixmap
        pix.loadFromData(self.value().toCString())
        return pix

    """
    Emite la señal de foco perdido
    """

    def emitLostFocus(self):
        self.lostFocus.emit()

    """
    Establece que el control no está mostrado
    """
    @QtCore.pyqtSlot()
    def setNoShowed(self):
        if self.foreignField_ and self.fieldRelation_:
            self.showed = False
            if self.isVisible():
                self.showWidget()

    """
    Establece el valor de este campo según el resultado de la consulta
    cuya claúsula 'where' es;  nombre campo del objeto que envía la señal igual
    al valor que se indica como parámetro.

    Sólo se pueden conectar objetos tipo FLFielDB, y su uso normal es conectar
    la señal FLFieldDB::textChanged(cons QString&) a este slot.

    @param v Valor
    """
    @decorators.NotImplementedWarn
    @QtCore.pyqtSlot(str)
    def setMapValue(self, v=None):
        if v:
            self.fieldMapValue_ = self.sender()
            self.mapValue_ = v
            self.setMapValue()
        else:
            if not self.fieldMapValue_ or not self.cursor_:
                return
            tMD = self.cursor_.metadata()
            if not tMD:
                return

            fSN = self.fieldMapValue_.fieldName()
            field = tMD.field(self.fieldName_)
            fieldSender = tMD.field(fSN)

            if not field or not fieldSender:
                return

            if field.relationM1():
                if not field.relationM1().foreignTable() == tMD.name():
                    mng = self.cursor_.db().manager()
                    rt = field.relationM1().foreignTable()
                    fF = self.fieldMapValue_.foreignField()
                    q = FLSqlQuery(None, self.cursor_.db().connectionName())
                    q.setForwardOnly(True)
                    q.setTablesList(rt)
                    q.setSelect("%s,%s" %
                                (field.relationM1().foreignField(), fF))
                    q.setFrom(rt)

                    where = mng.formatAssignValue(
                        fF, fieldSender, self.mapValue_, True)
                    assocTmd = mng.metadata(rt)
                    filterAc = self.cursor_.filterAssoc(fF, assocTmd)
                    if assocTmd and not assocTmd.inCache():
                        del assocTmd

                    if filterAc:
                        if not where:
                            where = filterAc
                        else:
                            where = "%s AND %s" % (where, filterAc)

                    if not self.filter_:
                        q.setWhere(where)
                    else:
                        q.setWhere("%s AND %s" % (self.filter_, where))

                    if q.exec_() and q.next():
                        # self.setValue("")
                        self.setValue(q.value(0))

    """
    Emite la señal de keyF2Pressed.

    La señal key_F2_Pressed del editor (sólo si el editor es FLLineEdit)
    está conectada a este slot.
    """
    @QtCore.pyqtSlot()
    def emitKeyF2Pressed(self):
        self.keyF2Pressed.emit()

    """
    Emite la señal de labelClicked. Se usa en los campos M1 para editar el formulario de edición del valor seleccionado.
    """
    @QtCore.pyqtSlot()
    def emitLabelClicked(self):
        self.labelClicked.emit()

    """
    Emite la señal de textChanged.

    La señal textChanged del editor (sólo si el editor es FLLineEdit)
    está conectada a este slot.
    """
    @QtCore.pyqtSlot(str)
    def emitTextChanged(self, t):
        self.textChanged.emit(t)

    """
    Emite la señal activatedAccel( int )
    """
    @QtCore.pyqtSlot(int)
    def ActivatedAccel(self, identifier):
        if self.editor_ and self.editor_.hasFocus:
            self.activatedAccel.emit()

    def setDisabled(self, disable):
        if not pineboolib.project._DGI.localDesktop():
            pineboolib.project._DGI._par.addQueque("%s_setDisabled" % self.objectName(), disable)
        self.setEnabled(not disable)

    """
    Redefinida por conveniencia
    """

    def setEnabled(self, enable):
        # print("FLFieldDB: %r setEnabled: %r" % (self.fieldName_, enable))
        if self.editor_:
            if hasattr(self.editor_, "setReadOnly"):
                tMD = self.cursor_.metadata()
                field = tMD.field(self.fieldName_)

                self.editor_.setReadOnly(not enable)
                if not enable or not field.editable():
                    self.editor_.setStyleSheet('background-color: #f0f0f0')
                else:
                    # TODO: al re-habilitar un control, restaurar el color que
                    # le toca
                    if not field.allowNull() and not (field.type() == "time" or field.type() == "date"):
                        self.editor_.setStyleSheet(
                            'background-color:' + self.notNullColor().name())
                    else:
                        self.editor_.setStyleSheet('background-color: #fff')

            else:
                self.editor_.setEnabled(enable)
        if self.pushButtonDB:
            self.pushButtonDB.setEnabled(enable)
        return
        if enable:
            self.setAttribute(Qt.WA_ForceDisabled, False)
        else:
            self.setAttribute(Qt.WA_ForceDisabled, True)

        if not self.isTopLevel() and self.parentWidget() and not self.parentWidget().isEnabled() and enable:
            return

        if enable:
            if self.testAttribute(Qt.WA_Disabled):
                self.setAttribute(Qt.WA_Disabled, False)
                self.enabledChange(not enable)
                if self.children():
                    for w in self.children():
                        if not w.testAttribute(Qt.WA_ForceDisabled):
                            le = w
                            if isinstance(le, pineboolib.project.resolveDGIObject("QLineEdit")):
                                allowNull = True
                                tMD = self.cursor_.metadata()
                                if tMD:
                                    field = tMD.field(self.fieldName_)
                                    if field and not field.allowNull():
                                        allowNull = False

                                if allowNull:
                                    cBg = QtGui.QColor.blue()
                                    cBg = QtWidgets.QApplication().palette().color(
                                        QtGui.QPalette.Active, QtGui.QPalette.Base)
                                else:
                                    cBg = self.NotNullColor().name()

                                le.setDisabled(False)
                                le.setReadOnly(False)
                                le.palette().setColor(QtGui.QPalette.Base, cBg)
                                le.setCursor(Qt.IBeamCursor)
                                le.setFocusPolicy(Qt.StrongFocus)
                                continue
                            w.setEnabled(True)

            else:
                if not self.testAttribute(Qt.WA_Disabled):
                    if self.focusWidget() == self:
                        parentIsEnabled = False
                        if not self.parentWidget() or self.parentWidget().isEnabled():
                            parentIsEnabled = True
                        if not parentIsEnabled or not self.focusNextPrevChild(True):
                            self.clearFocus()
                    self.setAttribute(Qt.WA_Disabled)
                    self.enabledChange(not enable)

                    if self.children():
                        for w in self.children():
                            if isinstance(w, pineboolib.project.resolveDGIObject("QLineEdit")):
                                le = w
                                if le:
                                    le.setDisabled(False)
                                    le.setReadOnly(True)
                                    le.setCursor(Qt.IBeamCursor)
                                    le.setFocusPolicy(Qt.NoFocus)
                                    continue

                            if isinstance(w, QtWidgets.pineboolib.project.resolveDGIObject("QTextEdit")):
                                te = w
                                te.setDisabled(False)
                                te.setReadOnly(True)
                                te.viewPort().setCursor(Qt.IBeamCursor)
                                te.setFocusPolicy(Qt.NoFocus)
                                continue

                            if w == self.textLabelDB and self.pushButtonDB:
                                w.setDisabled(False)
                                continue

                            w.setEnabled(False)
                            w.setAttribute(Qt.WA_ForceDisabled, False)

    """
    Captura evento mostrar
    """

    def showEvent(self, e):
        self.showWidget()
        super(FLFieldDB, self).showEvent(e)
    """
    Redefinida por conveniencia
    """

    def showWidget(self):
        if self._loaded:
            if not self.showed:
                if self.topWidget_:
                    self.showed = True
                    if not self.firstRefresh:
                        self.refresh()
                        self.firstRefresh = True

                    # if self.cursorAux:
                        # print("Cursor auxiliar a ", self.tableName_)
                    if self.cursorAux and self.cursor_ and self.cursor_.bufferIsNull(self.fieldName_):

                        if not self.cursorAux.bufferIsNull(self.foreignField_):
                            mng = self.cursor_.db().manager()
                            tMD = self.cursor_.metadata()
                            if tMD:
                                v = self.cursorAux.valueBuffer(
                                    self.foreignField_)
                                # print("El valor de %s.%s es %s" % (tMD.name(), self.foreignField_, v))

                                # FIXME q = FLSqlQuery(False,
                                # self.cursor_.db().connectionName())
                                q = FLSqlQuery()
                                q.setForwardOnly(True)
                                q.setTablesList(self.tableName_)
                                q.setSelect(self.fieldName_)
                                q.setFrom(self.tableName_)
                                where = mng.formatAssignValue(
                                    tMD.field(self.fieldRelation_), v, True)
                                filterAc = self.cursorAux.filterAssoc(
                                    self.foreignField_, tMD)

                                if filterAc:
                                    # print("FilterAC == ", filterAc)
                                    if where not in (None, ""):
                                        where = filterAc
                                    else:
                                        where = "%s AND %s" % (where, filterAc)

                                if not self.filter_:
                                    q.setWhere(where)
                                else:
                                    q.setWhere("%s AND %s" %
                                               (self.filter_ + where))

                                # print("where tipo", type(where))
                                # print("Consulta = %s" % q.sql())
                                if q.exec_() and q.first():
                                    value = q.value(0)
                                    if isinstance(value, str):
                                        if value[0:3] == "RK@":
                                            value = self.cursor_.fetchLargeValue(
                                                value)
                                    if isinstance(value, datetime.date):
                                        value = value.strftime('%d-%m-%Y')
                                    self.setValue(value)
                                if not tMD.inCache():
                                    del tMD

                else:
                    self.initFakeEditor()

                self.showed = True

    """
    Inicializa un editor falso y no funcional.

    Esto se utiliza cuando se está editando el formulario con el diseñador y no
    se puede mostrar el editor real por no tener conexión a la base de datos.
    Crea una previsualización muy esquemática del editor, pero suficiente para
    ver la posisicón y el tamaño aproximado que tendrá el editor real.
    """

    def initFakeEditor(self):

        hasPushButtonDB = None
        if not self.tableName_ and not self.foreignField_ and not self.fieldRelation_:
            hasPushButtonDB = True
        else:
            hasPushButtonDB = False

        if not self.fieldName_:
            self.fieldAlias_ = FLUtil.tr("Error: fieldName vacio")
        else:
            self.fieldAlias_ = self.fieldName_

        if not self.editor_:
            self.editor_ = pineboolib.project.resolveDGIObject("QLineEdit")()
            self.editor_.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            self.textLabelDB.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
            # self.editor_.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
            self.editor_.setMinimumWidth(100)
            self.FLWidgetFieldDBLayout.addWidget(self.editor_)
            self.editor_.setFocusPolicy(Qt.StrongFocus)
            self.setFocusProxy(self.editor_)
            self.setTabOrder(self.pushButtonDB, self.editor_)
            self.editor_.show()

        self.textLabelDB.setText(self.fieldAlias_)
        if self.showAlias_:
            self.textLabelDB.show()
        else:
            self.textLabelDB.hide()

        if hasPushButtonDB:
            self.pushButtonDB.setFocusPolicy(Qt.NoFocus)
            self.pushButtonDB.show()
        else:
            self.pushButtonDB.hide()

        prty = ""
        if self.tableName_:
            prty += "tN:" + self.tableName_ + ","
        if self.foreignField_:
            prty += "fF:" + self.foreignField_ + ","
        if self.fieldRelation_:
            prty += "fR:" + self.fieldRelation_ + ","
        if self.actionName_:
            prty += "aN:" + self.actionName_ + ","

        if prty:
            self.editor_.setText(prty)
            self.editor_.home(False)

        if self.maximumSize().width() < 80:
            self.setShowEditor(False)
        else:
            self.setShowEditor(self.showEditor_)

    """
    Color de los campos obligatorios
    """

    def notNullColor(self):
        if not self.initNotNullColor_:
            self.initNotNullColor_ = True
        self.notNullColor_ = FLSettings().readEntry(
            "ebcomportamiento/colorObligatorio", None)
        if self.notNullColor_ is None:
            self.notNullColor_ = QtGui.QColor(255, 233, 173)
        return self.notNullColor_


class FLDoubleValidator(QtGui.QDoubleValidator):

    def __init__(self, *args, **kwargs):
        super(FLDoubleValidator, self).__init__()

    def validate(self, input_, i):
        return super(FLDoubleValidator, self).validate(input_, i)
        if not input_:
            return QtGui.QValidator.Acceptable

        input_ = input_.replace(",", ".")

        state = QtGui.QDoubleValidator.validate(self, input_, i)

        if state in (QtGui.QValidator.Invalid, QtGui.QValidator.Intermediate):
            s = input_[1:len(input_) - 1]
            if input_[1] == "-" and (QtGui.QDoubleValidator.validate(self, s, i) == QtGui.QValidator.Acceptable or not s):
                state = QtGui.QValidator.Acceptable
            else:
                state = QtGui.QValidator.Invalid
        else:
            state = QtGui.QValidator.Acceptable

        if QtCore.QLocale().decimalPoint() == ",":
            input_ = input_.replace(".", ",")
        else:
            input_ = input_.replace(",", ".")

        return state


class FLIntValidator(QtGui.QIntValidator):

    def __init__(self, *args, **kwargs):
        super(FLIntValidator, self).__init__()

    def validate(self, input_, i):
        """
        if not input_:
            return QtGui.QValidator.Acceptable
        if QtCore.QLocale().decimalPoint() == ",":
            input_ = input_.replace(".", QtCore.QLocale().decimalPoint())
        else:
            input_ = input_.replace(",", QtCore.QLocale().decimalPoint())

        iV = QtGui.QIntValidator()
        state = super(FLIntValidator, self).validate(input_, i)
        if state == QtGui.QValidator.Invalid or state == QtGui.QValidator.Intermediate:
            s = input_[1:]
            if input_[0] == "-" and super(FLIntValidator, self).validate(self, s, i) == QtGui.QValidator.Acceptable:
                state = QtGui.QValidator.Acceptable
            else:
                state = QtGui.QValidator.Invalid
        else:

            state = QtGui.QValidator.Acceptable
        return state
        """
        return super(FLIntValidator, self).validate(input_, i)


class FLUIntValidator(QtGui.QDoubleValidator):

    def __init__(self, *args, **kwargs):
        super(FLUIntValidator, self).__init__()

    def validate(self, input_, i):
        """
        if not input_:
            return QtGui.QValidator.Acceptable

        iV = QtGui.QIntValidator()
        state = iV.validate(input_, i)
        if state == QtGui.QValidator.Intermediate:
            state = QtGui.QValidator.Invalid

        return state
        """
        return super(FLUIntValidator, self).validate(input_, i)
