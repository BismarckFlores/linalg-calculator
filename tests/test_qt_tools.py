"""Pruebas gráficas de los modos migrados y su integración con MathLive."""

import os
import sys
import unittest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform != "linux"):
    raise unittest.SkipTest("Qt WebEngine requiere una sesión gráfica.")

try:
    from PySide6.QtCore import QPoint
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton
except ImportError as problem:
    raise unittest.SkipTest("Instala las dependencias de la interfaz Qt.") from problem

from desktop.tools.linear_algebra.core.inputs import MatrixInput
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl
from desktop.tools.registry import TOOLS
from desktop.window import CalculatorWindow


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
        visible_results = (editor.value() for editor in page.result.findChildren(MathInput) if editor.isVisible())
        self.assertIn(expected, "\n".join((*visible_results, page.result_title.text(), page.result_badge.text())))

    def test_catalog_and_matrix_operations(self):
        self.assertEqual(len(TOOLS), 12)
        page = self.open_page("operations")
        select = page.findChild(SegmentedControl)
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

    def test_calculus_modes_and_navigation(self):
        self.window.resize(960, 640)
        self.window.select("home")
        home = self.window.pages["home"]
        shortcut = next(button for button in home.findChildren(QPushButton)
                        if button.accessibleName() == "Abrir Derivadas e integrales")
        shortcut.click()
        page = self.open_page("calculus")
        self.assertTrue(self.window._nav["calculus"].isChecked())
        self.assertEqual(self.window._scroll["calculus"].horizontalScrollBar().maximum(), 0)
        mode = page.findChild(SegmentedControl)
        fields = {field.name: field for field in page.findChildren(MathInput)}
        point = fields["Evaluar en x (opcional)"]
        point.set_value("1.5")
        self.calculate(page, "23/4")
        rendered = []
        page.output.web.page().runJavaScript(
            "[...document.querySelectorAll('.result-formula math-field')]"
            ".filter(field => field.readOnly && field.value).length", rendered.append)
        for _ in range(30):
            if rendered:
                break
            QTest.qWait(20)
        self.assertEqual(rendered, [2.0])
        mode.setCurrentIndex(1)
        self.assertFalse(page.result.isVisible())
        self.assertFalse(point.isVisible())
        self.calculate(page, "+ C")
        mode.setCurrentIndex(2)
        fields["Función f(x)"].set_value("x^2")
        self.assertTrue(fields["Límite inferior"].isVisible())
        self.calculate(page, "1/3")
        fields["Función f(x)"].set_value("1/x")
        self.assertFalse(page.result.isVisible())
        submit = next(button for button in page.findChildren(QPushButton) if button.objectName() == "action")
        submit.click()
        self.assertTrue(page.error.isVisible())
        clear = next(button for button in page.findChildren(QPushButton)
                     if button.text() == "Limpiar" and button.isVisible())
        clear.click()
        self.assertFalse(page.error.isVisible())
        self.assertEqual(fields["Función f(x)"].value(), "")
        dark = self.window._dark
        try:
            for theme in (True, False):
                self.window._apply_theme(theme)
                self.window.select("home")
                self.window._nav["calculus"].click()
                self.assertTrue(page.isVisible())
                self.assertEqual(page.output._dark, theme)
        finally:
            self.window._apply_theme(dark)

    def test_systems_and_echelon(self):
        page = self.open_page("gauss")
        method, entry = page.findChildren(SegmentedControl)
        self.calculate(page, "x = 29")
        self.assertTrue(page.walk.isVisible())
        page.walk.all_steps.setChecked(True)
        for _ in range(30):
            if page.walk.output.web.height() > 264:
                break
            QTest.qWait(30)
        self.assertGreater(page.walk.output.web.height(), 264)
        expanded_height = page.walk.output.web.height()
        page.walk.all_steps.setChecked(False)
        for _ in range(30):
            if page.walk.output.web.height() < expanded_height:
                break
            QTest.qWait(30)
        self.assertLess(page.walk.output.web.height(), expanded_height)
        page.walk.index.stepUp()
        self.assertIn("f", page.walk.step_title.text())
        method.setCurrentIndex(1)
        entry.setCurrentIndex(1)
        editor = next(field for field in page.findChildren(MathInput) if field.kind == "equations")
        editor.set_value("x + y = 3\n2x + 2y = 6")
        self.calculate(page, "Solución general")
        editor.set_value("x + y = 3\nx + y = 4")
        self.calculate(page, "Sistema Inconsistente")
        page = self.open_page("echelon")
        page.findChild(MatrixInput).set_value("1;2;0\n0;0;1\n0;0;0")
        self.calculate(page, "Forma escalonada reducida: sí")
        page.findChild(MatrixInput).set_value("0;0\n2;3")
        self.calculate(page, "falla en la fila")

    def test_inverse_lu_and_determinant(self):
        for key, caption in (("inverse", "Ambos productos"), ("lu", "La comprobación exacta se cumple")):
            with self.subTest(key=key):
                page = self.open_page(key)
                self.calculate(page, caption)
                page.findChild(SegmentedControl).setCurrentIndex(1)
                self.calculate(page, "Comprobación A · x")
        page = self.open_page("determinant")
        page.findChild(MatrixInput).set_value("1;2;3\n0;4;5\n0;0;6")
        self.calculate(page, "det(A) = 24")
        self.assertTrue(page.walk.isVisible())
        method, mode = page.findChildren(SegmentedControl)
        method.setCurrentIndex(1)
        self.calculate(page, "Comprobación por cofactores: det(A) = 24")
        mode.setCurrentIndex(1)
        editor = next(field for field in page.findChildren(MathInput) if field.kind == "equations")
        editor.set_value("2x = 0\n3y = 0")
        self.calculate(page, "det(A) = 6")

    def test_matrix_controls_wrap_and_keep_entries(self):
        page = self.open_page("gauss")
        a, b = page.findChildren(MatrixInput)
        self.window.resize(1180, 800)
        QTest.qWait(100)
        self.assertEqual(a.mapTo(page, QPoint()).y(), b.mapTo(page, QPoint()).y())
        self.window.resize(960, 640)
        QTest.qWait(100)
        self.assertGreater(b.mapTo(page, QPoint()).y(), a.mapTo(page, QPoint()).y())
        self.assertEqual(self.window._scroll["gauss"].horizontalScrollBar().maximum(), 0)
        self.window.resize(1180, 800)
        b.rows.findChildren(QPushButton)[1].click()
        self.assertEqual(a.matrix().rows, 4)
        self.assertEqual(b.matrix().rows, 4)
        b.rows.stepDown()
        a.cols.stepDown()
        a.cols.stepUp()
        self.assertEqual(a.matrix().row(2), [0, 2, -8])

    def test_vectors_bases_and_roman(self):
        page = self.open_page("vectors")
        operation = page.findChild(SegmentedControl)
        for index, expected in enumerate(("5/2", "7/2", "3/2", "La suma reproduce el vector objetivo")):
            operation.setCurrentIndex(index)
            self.calculate(page, expected)
        page = self.open_page("bases")
        direction, radix = page.findChildren(SegmentedControl)
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
        operation = page.findChild(SegmentedControl)
        for index, expected in enumerate(("XXIII", "V = 5", "CXXVI")):
            operation.setCurrentIndex(index)
            self.calculate(page, expected)
        self.assertIn("Suma repetida", page.walk.output.value())
