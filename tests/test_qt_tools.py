"""Pruebas gráficas de los modos migrados y su integración con MathLive."""

import os
import sys
import unittest
from fractions import Fraction

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform != "linux"):
    raise unittest.SkipTest("Qt WebEngine requiere una sesión gráfica.")

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton
except ImportError as problem:
    raise unittest.SkipTest("Instala las dependencias de la interfaz Qt.") from problem

from desktop.tools.linear_algebra.core.inputs import MatrixInput, read_equations
from desktop.core.math_input import MathInput
from desktop.core.math_notation import from_ascii
from core.linear_algebra.handlers.equations import parse_equation
from desktop.core.widgets import SegmentedControl, Stepper
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
        self.assertEqual(len(TOOLS), 14)
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
            grid, tiles = home._grids[-1]
            spans = [grid.getItemPosition(grid.indexOf(tile))[3] for tile in tiles]
            self.assertEqual(spans, [1, 1, columns])
        shortcut = next(button for button in home.findChildren(QPushButton)
                        if button.accessibleName() == "Abrir Regula Falsi")
        shortcut.click()
        self.assertTrue(self.window._nav["regula_falsi"].isChecked())
        self.assertTrue(self.window.pages["regula_falsi"].isVisible())

    def test_iterative_systems_modes_and_validation(self):
        self.window.select("home")
        shortcut = next(button for button in self.window.pages["home"].findChildren(QPushButton)
                        if button.accessibleName() == "Abrir Jacobi y Gauss–Seidel")
        shortcut.click()
        page = self.open_page("iterative")
        controls = {control.accessibleName(): control for control in page.findChildren(SegmentedControl)}
        method = controls["Método iterativo"]
        mode = controls["Forma de entrada"]
        examples = controls["Cargar ejemplo iterativo"]
        examples.activated.emit(1)
        self.calculate(page, "Jacobi")
        self.assertEqual(page.table.columnCount(), 7)
        self.assertIn("2.272727", page.walk.output.value())
        method.setCurrentIndex(1)
        self.assertFalse(page.result.isVisible())
        self.calculate(page, "Gauss–Seidel")
        self.assertIn("2.327272", page.walk.output.value())
        mode.setCurrentIndex(1)
        self.assertFalse(page.result.isVisible())
        self.calculate(page, "Gauss–Seidel")
        initial = next(field for field in page.findChildren(MathInput) if field.kind == "vector")
        initial.set_value("1,2,-1,1")
        self.calculate(page, "residuo del sistema es cero")
        self.assertEqual(page.table.rowCount(), 1)
        initial.set_value("0,0")
        button = next(button for button in page.findChildren(QPushButton) if button.objectName() == "action")
        button.click()
        self.assertTrue(page.error.isVisible())
        dark = self.window._dark
        try:
            for theme in (True, False):
                self.window._apply_theme(theme)
                self.window.select("home")
                self.window._nav["iterative"].click()
                self.assertTrue(page.isVisible())
            self.window.resize(960, 640)
            QTest.qWait(100)
            self.assertEqual(self.window._scroll["iterative"].horizontalScrollBar().maximum(), 0)
        finally:
            self.window._apply_theme(dark)
        clear = next(button for button in page.findChildren(QPushButton)
                     if button.text() == "Limpiar" and button.isVisible())
        clear.click()
        self.assertFalse(page.result.isVisible())
        self.assertFalse(page.error.isVisible())
        self.assertEqual(initial.value(), "")
        examples.activated.emit(0)
        mode.setCurrentIndex(0)
        limit = next(field for field in page.findChildren(Stepper)
                     if field.accessibleName() == "Máximo de iteraciones")
        limit.setValue(1)
        self.calculate(page, "No convergió. Se detuvo en la iteración 1")
        self.assertIn("Error absoluto máximo", page.output.value())
        self.assertIn("Residuo máximo", page.output.value())
        page.iterations.format.setCurrentIndex(1)
        self.assertTrue(page.iterations.decimals.isVisible())
        self.assertEqual(page.table.item(1, 1).text(), "0.70000")
        controls["Criterio de parada"].setCurrentIndex(1)
        self.assertFalse(page.result.isVisible())

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

    def test_universal_keyboard_routes_to_the_current_field(self):
        page = self.open_page("calculus")
        page.findChild(SegmentedControl).setCurrentIndex(2)
        fields = {field.name: field for field in page.findChildren(MathInput)}
        function = fields["Función f(x)"]
        function.set_value("sin(x)")
        fields["Límite inferior"].set_value("0")
        upper = fields["Límite superior"]
        upper.clear()
        upper.web.setFocus()
        keyboard = self.window.math_keyboard
        keyboard.toggle.setChecked(True)
        self.assertTrue(keyboard.isVisible())
        pi = next(button for button in keyboard.keys.findChildren(QPushButton) if button.text() == "π")
        pi.click()
        QTest.qWait(150)
        self.assertEqual(upper.value().strip(), "pi")
        self.assertEqual(function.value(), "sin(x)")
        self.calculate(page, "Integral de 0 a pi = 2")

        self.window.select("home")
        self.assertTrue(keyboard.isVisible())
        self.assertFalse(pi.isEnabled())
        self.assertTrue(all(not field.accepts_math_keys() for field in fields.values()))
        keyboard.toggle.setChecked(False)

    def test_enter_keeps_equation_symbols_on_their_original_line(self):
        for key in ("gauss", "echelon", "inverse", "lu", "determinant", "iterative"):
            with self.subTest(page=key):
                page = self.open_page(key)
                field = next(field for field in page.findChildren(MathInput) if field.kind == "equations")
                field.set_value("x_1 + x_2 = 6\nx_1 - x_2 = 2")
                QTest.qWait(30)
                exported = []
                field.web.page().runJavaScript("""
                    (() => {
                        const field = document.querySelector('math-field');
                        field.position = field.lastOffset;
                        field.dispatchEvent(new KeyboardEvent('keydown', {
                            key: 'Enter', bubbles: true, cancelable: true
                        }));
                        field.insert('x_1=4', {format: 'latex'});
                        return MathLive.convertLatexToAsciiMath(field.value);
                    })()
                """, exported.append)
                for _ in range(60):
                    if exported:
                        break
                    QTest.qWait(20)
                self.assertTrue(exported)
                lines = from_ascii(exported[0], "equations").strip().splitlines()
                self.assertEqual(len(lines), 3)
                self.assertEqual([parse_equation(line).constant for line in lines], [6, 2, 4])
                self.assertEqual(parse_equation(lines[-1]).terms, {"x_1": 1})

    def test_system_modes_convert_in_both_directions(self):
        for key in ("gauss", "iterative", "inverse", "lu", "determinant", "echelon"):
            with self.subTest(page=key):
                page = self.open_page(key)
                mode = next(control for control in page.findChildren(SegmentedControl)
                            if control.accessibleName() == "Forma de entrada")
                field = next(field for field in page.findChildren(MathInput) if field.kind == "equations")
                matrices = page.findChildren(MatrixInput)
                a = matrices[0]
                original_matrices = [matrix.value() for matrix in matrices]
                original_equations = field.value()
                original_names = list(a.variable_names)
                original_mode = mode.currentIndex()
                mode.setCurrentIndex(1)
                self.assertEqual(mode.currentIndex(), 1)
                field.set_value("(1/3)u_1 - 2u_2 = 5\n3u_1 + u_2 = -7")
                mode.setCurrentIndex(0)
                self.assertEqual(mode.currentIndex(), 0)
                self.assertEqual(a.matrix().row(1)[:2], [Fraction(1, 3), -2])
                self.assertEqual(a.matrix().row(2)[:2], [3, 1])
                if len(matrices) > 1:
                    self.assertEqual(matrices[1].matrix().data, [[5], [-7]])
                before = a.matrix().data
                mode.setCurrentIndex(1)
                self.assertIn("u_1", field.value())
                parsed = [parse_equation(line) for line in field.value().splitlines()]
                self.assertEqual([equation.constant for equation in parsed], [5, -7])
                field._changed_visual("u_1 + =")
                mode.setCurrentIndex(0)
                self.assertEqual(mode.currentIndex(), 1)
                self.assertEqual(field.value(), "u_1 + =")
                self.assertEqual(a.matrix().data, before)
                field.set_value("0u_1 + u_2 = 2\n0u_1 + 2u_2 = 4")
                mode.setCurrentIndex(0)
                self.assertEqual(mode.currentIndex(), 0)
                self.assertEqual(a.matrix().cols, 3 if key == "echelon" else 2)
                mode.setCurrentIndex(1)
                self.assertIn("0u_1", field.value())
                matrix, names = read_equations(field, 10)
                self.assertEqual(names, ["u_1", "u_2"])
                self.assertEqual(matrix.data, [[0, 1, 2], [0, 2, 4]])
                mode.setCurrentIndex(0)
                for editor, value in zip(matrices, original_matrices):
                    editor.set_value(value)
                a.variable_names = original_names
                if original_mode == 1:
                    mode.setCurrentIndex(1)
                field.set_value(original_equations)

    def test_docked_keyboard_stays_at_bottom_when_resized(self):
        self.window.select("open_methods")
        keyboard = self.window.math_keyboard
        original_size = self.window.size()
        keyboard.toggle.setChecked(True)
        try:
            area = self.window.stack.parentWidget()

            def assert_docked():
                QTest.qWait(80)
                bottom = area.mapTo(self.window, area.contentsRect().bottomLeft())
                self.assertEqual(keyboard.geometry().bottomLeft(), bottom)
                self.assertEqual(keyboard.width(), area.width())
                stack_bottom = self.window.stack.mapTo(self.window, self.window.stack.rect().bottomLeft()).y()
                self.assertLess(stack_bottom, keyboard.geometry().top())

            self.window.resize(1440, 990)
            assert_docked()
            keyboard.mode_button.click()
            QTest.qWait(80)
            before = keyboard.pos()
            handle = keyboard._handle
            QTest.mousePress(handle, Qt.MouseButton.LeftButton, pos=QPoint(30, 10))
            QTest.mouseMove(handle, QPoint(-10, -70))
            QTest.mouseRelease(handle, Qt.MouseButton.LeftButton, pos=QPoint(30, 10))
            self.assertEqual(keyboard.pos(), before - QPoint(40, 80))
            keyboard.mode_button.click()
            assert_docked()
            keyboard.toggle.click()
            keyboard.toggle.click()
            assert_docked()
            for width, height in ((960, 640), (1918, 1015), (1160, 780)):
                self.window.resize(width, height)
                assert_docked()
        finally:
            keyboard.toggle.setChecked(False)
            self.window.resize(original_size)

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
        self.assertIn("→", page.walk.output.value())
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
