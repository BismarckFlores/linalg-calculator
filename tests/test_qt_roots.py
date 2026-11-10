"""Integración de los métodos por intervalo con la ventana Qt."""

import os
import sys
import unittest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform != "linux"):
    raise unittest.SkipTest("Las pruebas de Qt WebEngine requieren una sesión gráfica.")

try:
    from PySide6.QtCore import QPoint, QTimer, Qt
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialog, QPushButton
except ImportError as problem:
    raise unittest.SkipTest("Instala requirements.txt para probar Qt.") from problem

from core.root_bracket import RootCriterion, RootStop
from desktop.math_input import MathInput
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
        button = next(button for button in page.findChildren(QPushButton) if button.text().removesuffix("  →") == text)
        self.assertTrue(button.isVisible())
        button.click()
        QTest.qWait(40)

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
        self.assertEqual(page.table.item(3, 6).toolTip(), str(result.value))
        page.walk.index.setValue(4)
        self.assertIn("se detiene", page.walk.output.value())
        self.assertFalse(page.plot.grab().isNull())
        original = page.plot._range
        self.click(page, "+  Acercar")
        self.assertLess(page.plot._range[1] - page.plot._range[0], original[1] - original[0])
        original = page.plot._range
        point = page.plot.rect().center()
        QTest.mousePress(page.plot, Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(page.plot, point + QPoint(30, 0))
        QTest.mouseRelease(page.plot, Qt.MouseButton.LeftButton, pos=point + QPoint(30, 0))
        self.assertNotEqual(page.plot._range, original)
        self.window.theme_button.click()
        self.assertTrue(page.plot.dark)
        self.window.theme_button.click()

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
        self.assertIn("Sin convergencia", page.summary.text())
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
        self.assertIn("Paso 16", page.walk.output.value())

        def inspect_popup():
            popup = self.app.activeModalWidget()
            if isinstance(popup, QDialog):
                opened.append(popup.isVisible())
                popup.reject()

        opened = []
        QTimer.singleShot(100, inspect_popup)
        self.click(page, "Maximizar")
        self.assertEqual(opened, [True])
        page.tolerance.set_value("0.0001")
        self.assertFalse(page.result_card.isVisible())
        self.assertIsNone(page.plot.result)
        self.assertTrue(page.graph_card.isVisible())
