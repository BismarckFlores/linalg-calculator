"""Pruebas gráficas de los modos migrados y su integración con MathLive."""

import os
import sys
import unittest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform != "linux"):
    raise unittest.SkipTest("Qt WebEngine requiere una sesión gráfica.")

try:
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton
except ImportError as problem:
    raise unittest.SkipTest("Instala las dependencias de la interfaz Qt.") from problem

from desktop.forms import MatrixInput
from desktop.math_input import MathInput
from desktop.window import TOOLS, CalculatorWindow


class QtToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--process-per-site")
        cls.app = QApplication.instance() or QApplication([])
        if sys.platform == "linux":
            QQuickWindow.setSceneGraphBackend("software")
        cls.window = CalculatorWindow()
        cls.window.show()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def open_page(self, key):
        self.window.select(key)
        page = self.window.pages[key]
        for _ in range(140):
            if all(field._ready for field in page.findChildren(MathInput)):
                break
            QTest.qWait(50)
        self.assertTrue(all(field._ready for field in page.findChildren(MathInput)), key)
        self.assertTrue(page.isVisible(), key)
        return page

    def calculate(self, page, expected):
        button = next(button for button in page.findChildren(QPushButton) if button.objectName() == "action")
        button.click()
        QTest.qWait(50)
        self.assertTrue(page.result.isVisible(), page.error.text())
        self.assertIn(expected, page.output.value())

    def test_catalog_and_matrix_operations(self):
        self.assertEqual(len(TOOLS), 11)
        page = self.open_page("operations")
        select = page.findChild(QComboBox)
        for index, expected in enumerate(("[ 6; 8 ]", "[ -4; -4 ]", "[ 19; 22 ]", "[ 1/2; 1 ]", "[ 1; 3 ]")):
            select.setCurrentIndex(index)
            self.assertFalse(page.result.isVisible())
            self.calculate(page, expected)
        matrix = page.findChild(MatrixInput)
        matrix.cols.setValue(3)
        self.calculate(page, "Dimensión: 3 × 2")
        self.assertEqual(matrix.matrix().size(), (2, 3))

    def test_catalog_links_adapt_to_window_width(self):
        self.window.select("home")
        home = self.window.pages["home"]
        for width, columns in ((960, 1), (1280, 2)):
            self.window.resize(width, 640)
            QTest.qWait(100)
            self.assertEqual(home._columns, columns)
        shortcut = next(button for button in home.findChildren(QPushButton)
                        if button.accessibleName() == "Abrir Regula Falsi")
        shortcut.click()
        self.assertTrue(self.window._nav["regula_falsi"].isChecked())
        self.assertTrue(self.window.pages["regula_falsi"].isVisible())

    def test_systems_and_echelon(self):
        page = self.open_page("gauss")
        method, entry = page.findChildren(QComboBox)
        self.calculate(page, "x = 113/34")
        self.assertTrue(page.walk.isVisible())
        page.walk.index.stepUp()
        self.assertIn("f", page.walk.output.value())
        method.setCurrentIndex(1)
        entry.setCurrentIndex(1)
        editor = next(field for field in page.findChildren(MathInput) if field.kind == "equations")
        editor.set_value("x + y = 3\n2x + 2y = 6")
        self.calculate(page, "Solución general")
        editor.set_value("x + y = 3\nx + y = 4")
        self.calculate(page, "Sistema Inconsistente")
        page = self.open_page("echelon")
        self.calculate(page, "Forma escalonada reducida: sí")
        page.findChild(MatrixInput).set_value("0;0\n2;3")
        self.calculate(page, "falla en la fila")

    def test_inverse_lu_and_determinant(self):
        for key, caption in (("inverse", "Ambos productos"), ("lu", "La comprobación exacta se cumple")):
            with self.subTest(key=key):
                page = self.open_page(key)
                self.calculate(page, caption)
                page.findChild(QComboBox).setCurrentIndex(1)
                self.calculate(page, "Comprobación A · x")
        page = self.open_page("determinant")
        page.findChild(MatrixInput).set_value("1;2;3\n0;4;5\n0;0;6")
        self.calculate(page, "det(A) = 24")
        self.assertTrue(page.walk.isVisible())
        page.findChild(QComboBox).setCurrentIndex(1)
        self.calculate(page, "Comprobación por cofactores: det(A) = 24")

    def test_vectors_bases_and_roman(self):
        page = self.open_page("vectors")
        operation = page.findChild(QComboBox)
        for index, expected in enumerate(("5/2", "7/2", "3/2", "La suma reproduce el vector objetivo")):
            operation.setCurrentIndex(index)
            self.calculate(page, expected)
        page = self.open_page("bases")
        direction, radix = page.findChildren(QComboBox)
        number = next(field for field in page.findChildren(QLineEdit) if field.accessibleName() == "Número")
        radix.setCurrentIndex(2)
        number.setText("-43")
        self.calculate(page, "-2B")
        self.assertGreater(page.table.rowCount(), 0)
        direction.setCurrentIndex(1)
        number.setText("-2B")
        self.calculate(page, "-43")
        radix.setCurrentIndex(4)
        number.setText("XIV")
        self.calculate(page, "14")
        page = self.open_page("roman")
        operation = page.findChild(QComboBox)
        for index, expected in enumerate(("XXIII", "V = 5", "CXXVI")):
            operation.setCurrentIndex(index)
            self.calculate(page, expected)
        self.assertIn("Suma repetida", page.walk.output.value())
