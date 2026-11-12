"""Integración de los métodos por intervalo con la ventana Qt."""

import os
import sys
import unittest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform != "linux"):
    raise unittest.SkipTest("Las pruebas de Qt WebEngine requieren una sesión gráfica.")

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QPushButton
except ImportError as problem:
    raise unittest.SkipTest("Instala requirements.txt para probar Qt.") from problem

from core.numerical_methods.handlers.root_bracket import RootCriterion, RootStop
from core.numerical_methods.handlers.real_function import RealFunction
from desktop.core.number_display import scientific_notation
from desktop.core.math_input import MathInput
from desktop.tools.numerical_methods.core.plot import FunctionPlot, PlotOverlay, _grid_ticks
from desktop.window import CalculatorWindow


class QtRootTests(unittest.TestCase):
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
        self.window._nav[key].click()
        page = self.window.pages[key]
        for _ in range(100):
            if all(field._ready for field in page.findChildren(MathInput)):
                break
            QTest.qWait(50)
        self.assertTrue(page.editor._ready, "MathLive no cargó")
        self.assertTrue(page.isVisible())
        return page

    def click(self, page, text):
        button = next(button for button in page.findChildren(QPushButton)
                      if text in (button.text().removesuffix("  →"), button.accessibleName()))
        self.assertTrue(button.isVisible())
        button.click()
        QTest.qWait(40)

    def test_newton_raphson_graph_selection_and_stopping(self):
        self.window.resize(960, 640)
        self.window.select("home")
        shortcut = next(button for button in self.window.pages["home"].findChildren(QPushButton)
                        if button.accessibleName() == "Abrir Métodos Abiertos")
        shortcut.click()
        page = self.open_page("open_methods")
        self.assertFalse(page.controls.isVisible())
        self.click(page, "Graficar función")
        self.assertTrue(page.controls.isVisible())
        self.click(page, "Calcular raíz")
        self.assertTrue(page.solve_error.isVisible())
        rect = page.plot._plot_rect()
        QTest.mouseClick(page.plot, Qt.MouseButton.LeftButton, pos=rect.center().toPoint())
        self.assertAlmostEqual(float(page.initial.value()), 0, delta=0.05)
        self.assertEqual(page.plot.markers, ((float(page.initial.value()), "x₀"),))
        self.assertFalse(page.solve_error.isVisible())
        marker = page.plot.markers
        center = rect.center().toPoint()
        QTest.mousePress(page.plot, Qt.MouseButton.LeftButton, pos=center)
        QTest.mouseMove(page.plot, center + QPoint(35, 0))
        QTest.mouseRelease(page.plot, Qt.MouseButton.LeftButton, pos=center + QPoint(35, 0))
        self.assertEqual(page.plot.markers, marker)

        self.click(page, "Maximizar")
        overlay = self.window.findChild(PlotOverlay)
        expanded = overlay.findChild(FunctionPlot)
        self.assertEqual(expanded.markers, marker)
        QTest.mouseClick(expanded, Qt.MouseButton.LeftButton,
                         pos=expanded._plot_rect().center().toPoint() + QPoint(50, 0))
        self.assertNotEqual(page.plot.markers, marker)
        self.assertIs(expanded, page.plot)
        self.assertTrue(page.initial.web.isVisible())
        self.assertEqual(expanded.markers, ((float(page.initial.value()), "x₀"),))
        self.click(overlay, "Cerrar")

        self.click(page, "Cargar ejemplo de Semana 13")
        self.click(page, "Graficar función")
        self.assertEqual(page.plot.markers, ((1.5, "x₀"),))
        self.click(page, "Calcular raíz")
        self.assertIn("1.5213797068", page.answer.value())
        self.assertIn("Iteraciones: 3", page.answer.value())
        self.assertIn("Se alcanzó la tolerancia", page.answer.value())
        self.assertEqual(page.table.rowCount(), 3)
        self.assertIn("− (-0.125) / (5.75)", page.walk.output.value())
        self.assertEqual(self.window._scroll["open_methods"].horizontalScrollBar().maximum(), 0)
        page.limit.setValue(1)
        self.assertFalse(page.result_card.isVisible())
        self.click(page, "Calcular raíz")
        self.assertIn("Se alcanzó el máximo", page.answer.value())
        self.assertEqual(page.table.rowCount(), 1)

        page.editor.set_value("x^2+1")
        self.assertFalse(page.graph_card.isVisible())
        self.assertFalse(page.result_card.isVisible())
        page.initial.set_value("0")
        self.click(page, "Graficar función")
        self.click(page, "Calcular raíz")
        self.assertIn("La derivada vale cero", page.answer.value())
        self.assertFalse(page.table_card.isVisible())
        dark = self.window._dark
        try:
            for theme in (True, False):
                self.window._apply_theme(theme)
                self.window.select("home")
                self.window._nav["open_methods"].click()
                self.assertTrue(page.result_card.isVisible())
                self.assertEqual(page.plot.dark, theme)
        finally:
            self.window._apply_theme(dark)
        clear = next(button for button in page.findChildren(QPushButton)
                     if button.text() == "Limpiar" and button.isVisible())
        clear.click()
        self.assertEqual(page.editor.value(), "")
        self.assertEqual(page.plot.markers, ())
        self.assertFalse(page.graph_card.isVisible())
        self.click(page, "Graficar función")
        self.assertTrue(page.graph_error.isVisible())

    def test_secant_selection_and_guided_examples(self):
        page = self.open_page("open_methods")
        page.method.setCurrentIndex(1)
        self.click(page, "Cargar ejemplo de Semana 13")
        page.initial.clear()
        page.second.clear()
        self.click(page, "Graficar función")
        self.assertTrue(page.second.isVisible())
        self.assertTrue(page.point.isVisible())
        rect = page.plot._plot_rect()
        for dx in (35, 70):
            QTest.mouseClick(page.plot, Qt.MouseButton.LeftButton, pos=rect.center().toPoint() + QPoint(dx, 0))
        self.assertEqual([label for _, label in page.plot.markers], ["x₀", "x₁"])

        self.click(page, "Cargar ejemplo de Semana 13")
        self.click(page, "Graficar función")
        self.assertEqual(page.plot.markers, ((1.0, "x₀"), (2.0, "x₁")))
        self.click(page, "Calcular raíz")
        self.assertIn("1.5213797068", page.answer.value())
        self.assertIn("1.33333333333", page.walk.output.value())
        self.assertEqual(page.table.rowCount(), 7)
        self.assertEqual(page.table.horizontalHeaderItem(7).text(), "|f(xₙ₊₁)|")

        self.click(page, "Práctica integradora")
        self.click(page, "Graficar función")
        self.assertEqual(page.plot.markers, ((2.0, "x₀"), (3.0, "x₁")))
        self.click(page, "Calcular raíz")
        self.assertIn("2.09455148154", page.answer.value())
        page.method.setCurrentIndex(0)
        self.assertFalse(page.second.isVisible())
        self.assertFalse(page.result_card.isVisible())

    def test_1_regula_falsi_flow_and_plot(self):
        page = self.open_page("regula_falsi")
        self.click(page, "Graficar función")
        self.assertTrue(page.controls.isVisible())
        self.click(page, "Calcular raíz")
        result = page.plot.result
        self.assertIs(result.stop, RootStop.TOLERANCE)
        self.assertAlmostEqual(result.root, 5.236050508, places=9)
        self.assertEqual(page.table.rowCount(), len(result.steps))
        self.assertEqual(page.table.item(3, 3).toolTip(), str(result.root))
        self.assertEqual(page.table.item(3, 6).toolTip(), scientific_notation(str(result.value)))
        page.walk.index.setValue(4)
        self.assertIn("se detiene", page.walk.output.value())
        self.assertFalse(page.plot.grab().isNull())
        x0, x1, y0, y1 = page.plot._view
        rect = page.plot._plot_rect()
        self.assertAlmostEqual((x1 - x0) / rect.width(), (y1 - y0) / rect.height())
        self.assertEqual([tick for tick, major in _grid_ticks(-10, 10, 700) if major and -8 < tick < 8],
                         [tick for tick, major in _grid_ticks(-9.7, 10.3, 700) if major and -8 < tick < 8])
        original = page.plot._range
        self.click(page, "Acercar")
        self.assertLess(page.plot._range[1] - page.plot._range[0], original[1] - original[0])
        original = page.plot._range
        point = page.plot.rect().center()
        QTest.mousePress(page.plot, Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(page.plot, point + QPoint(30, 0))
        QTest.mouseRelease(page.plot, Qt.MouseButton.LeftButton, pos=point + QPoint(30, 0))
        self.assertNotEqual(page.plot._range, original)
        original = page.plot._view
        QTest.mousePress(page.plot, Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(page.plot, point + QPoint(0, 30))
        QTest.mouseRelease(page.plot, Qt.MouseButton.LeftButton, pos=point + QPoint(0, 30))
        self.assertEqual(page.plot._view[:2], original[:2])
        self.assertGreater(page.plot._view[2], original[2])
        self.assertAlmostEqual(page.plot._view[3] - page.plot._view[2], original[3] - original[2])
        original_mode = self.window.theme_button.mode
        try:
            self.window.theme_button.actions_by_mode["dark"].trigger()
            self.assertTrue(page.plot.dark)
            self.window.theme_button.actions_by_mode["light"].trigger()
            self.assertFalse(page.plot.dark)
            self.window.theme_button.actions_by_mode["auto"].trigger()
            self.assertEqual(page.plot.dark, self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        finally:
            self.window.theme_button.set_mode(original_mode)

    def test_2_regula_falsi_errors_and_fallback(self):
        page = self.open_page("regula_falsi")
        page.editor._offer_text_fallback()
        page.editor.text_button.click()
        self.assertIs(page.editor.stack.currentWidget(), page.editor.text)
        page.editor.set_value("funcion_invalida(x)")
        self.click(page, "Graficar función")
        self.assertTrue(page.graph_error.isVisible())
        page.editor.set_value("sqrt(x) - 1")
        self.click(page, "Graficar función")
        page.a.set_value("-1")
        page.b.set_value("2")
        self.click(page, "Calcular raíz")
        self.assertTrue(page.solve_error.isVisible())
        page.a.set_value("1")
        self.click(page, "Calcular raíz")
        self.assertIs(page.plot.result.stop, RootStop.ZERO)
        self.assertEqual(page.table.rowCount(), 0)
        self.assertFalse(page.walk.index.isEnabled())
        self.click(page, "Potencia décima")
        self.click(page, "Graficar función")
        page.limit.setValue(2)
        self.click(page, "Calcular raíz")
        self.assertIs(page.plot.result.stop, RootStop.LIMIT)
        self.assertIn("Sin convergencia", page.answer.value())
        self.click(page, "Raíz de 2")
        self.click(page, "Graficar función")
        self.click(page, "Calcular raíz")
        self.assertIs(page.plot.result.criterion, RootCriterion.RESIDUAL)
        self.assertLess(abs(page.plot.result.value), 0.0001)

    def test_3_bisection_keeps_width_default(self):
        page = self.open_page("bisection")
        self.click(page, "Graficar función")
        self.click(page, "Calcular raíz")
        self.assertIs(page.plot.result.criterion, RootCriterion.WIDTH)
        self.assertAlmostEqual(page.plot.result.root, 0.763916015625)

    def test_4_bisection_table_walk_and_expanded_plot(self):
        page = self.open_page("bisection")
        self.click(page, "Graficar función")
        page.tolerance.set_value("0.00000001")
        self.click(page, "Calcular raíz")
        original = page.plot.result
        self.assertEqual(page.table.rowCount(), 15)
        page.walk.index.setValue(16)
        self.assertEqual(page.table_page.value(), 2)
        self.assertEqual(page.table.item(0, 0).text(), "16")
        original_value = page.table.item(0, 3).toolTip()
        page.format.setCurrentIndex(1)
        page.decimals.setValue(3)
        self.assertEqual(page.table.item(0, 3).toolTip(), original_value)
        self.assertEqual(page.table.item(0, 3).text(), f"{original.steps[15].c:.3f}")
        page.walk.all_steps.setChecked(True)
        self.assertIn("Iteración 16", page.walk.output.value())

        visible_editors = [editor for editor in page.findChildren(MathInput) if editor.web.isVisible()]
        self.assertIn(page.editor, visible_editors)
        values = [editor.value() for editor in visible_editors]
        self.click(page, "Maximizar")
        overlay = self.window.findChild(PlotOverlay)
        self.assertTrue(overlay.isVisible())
        self.assertFalse(page.editor.web.isVisible())
        self.assertTrue(overlay.isAncestorOf(page.controls))
        self.assertTrue(page.tolerance.web.isVisible())
        self.assertTrue(all(not editor.web.isVisible() for editor in visible_editors
                            if not page.controls.isAncestorOf(editor)))
        self.assertIs(overlay.window(), self.window)
        self.assertEqual(overlay.geometry(), self.window.rect())
        expanded = overlay.findChild(FunctionPlot)
        expanded.zoom(0.8)
        expanded_range = expanded._range
        QTest.keyClick(overlay, Qt.Key.Key_Escape)
        QTest.qWait(50)
        self.assertIsNone(self.window.findChild(PlotOverlay))
        self.assertTrue(all(editor.web.isVisible() for editor in visible_editors))
        self.assertEqual([editor.value() for editor in visible_editors], values)
        self.assertEqual(page.plot._range, expanded_range)
        self.click(page, "Maximizar")
        overlay = self.window.findChild(PlotOverlay)
        self.click(overlay, "Cerrar")
        self.assertIsNone(self.window.findChild(PlotOverlay))
        self.assertTrue(all(editor.web.isVisible() for editor in visible_editors))
        page.tolerance.set_value("0.0001")
        self.assertFalse(page.result_card.isVisible())
        self.assertIsNone(page.plot.result)
        self.assertTrue(page.graph_card.isVisible())

    def test_5_math_keyboard_exports_log_base_and_absolute_value(self):
        editor = self.open_page("bisection").editor
        editor.web.setFocus()
        keyboard = self.window.math_keyboard
        keyboard.toggle.setChecked(True)
        keys = {button.text(): button for button in keyboard.keys.findChildren(QPushButton)}
        editor.set_value("")
        keys["log"].click()
        editor.web.page().runJavaScript('''
            {
                const field = document.querySelector("math-field");
                field.insert("2", {format: "latex"});
                field.executeCommand("moveToNextPlaceholder");
                field.insert("x", {format: "latex"});
            }
        ''')
        QTest.qWait(150)
        self.assertAlmostEqual(RealFunction(editor.value())(8), 3)

        editor.set_value("")
        keys["|x|"].click()
        editor.web.page().runJavaScript('''
            document.querySelector("math-field").insert("x-4", {format: "latex"});
        ''')
        QTest.qWait(150)
        self.assertEqual(RealFunction(editor.value())(1), 3)
        keyboard.toggle.setChecked(False)

    def test_6_graph_accepts_trigonometric_superscripts_from_mathlive(self):
        page = self.open_page("bisection")
        editor = page.editor
        editor.set_value("")
        editor.web.page().runJavaScript(r'''
            document.querySelector("math-field").insert(
                "e^x-\\sin^{-1}(x)+\\cos^{2}(2x)", {format: "latex"}
            );
        ''')
        QTest.qWait(150)
        self.click(page, "Graficar función")
        self.assertFalse(page.graph_error.isVisible(), page.graph_error.text())
        self.assertAlmostEqual(page.plot.function(0), 2)

    def test_7_clear_from_form_and_math_keyboard(self):
        page = self.open_page("bisection")
        page.examples.findChildren(QPushButton)[0].click()
        self.click(page, "Graficar función")
        self.click(page, "Calcular raíz")
        self.assertTrue(page.result_card.isVisible())
        clear_form = next(button for button in page.findChildren(QPushButton, "link")
                          if button.text() == "Limpiar")
        clear_form.click()
        QTest.qWait(40)
        self.assertEqual(page.examples.currentIndex(), -1)
        for field in (page.editor, page.a, page.b, page.tolerance):
            self.assertEqual(field.value(), "")
        self.assertIsNone(page.plot.function)
        self.assertFalse(page.graph_card.isVisible())
        self.assertFalse(page.result_card.isVisible())

        page.examples.findChildren(QPushButton)[0].click()
        self.assertTrue(page.a.value())
        page.editor.web.setFocus()
        keyboard = self.window.math_keyboard
        keyboard.toggle.setChecked(True)
        self.click(keyboard.keys, "Limpiar")
        keyboard.toggle.setChecked(False)
        self.assertEqual(page.editor.value(), "")
        self.assertTrue(page.a.value())
