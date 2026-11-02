"""El mismo recorrido debe servir a matrices y biseccion sin cambiar controles."""

import unittest

from core.elimination import to_rref
from core.matrix import Matrix
from ui.presentation import pretty_label


class StepWalkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import customtkinter as ctk
        except ImportError:
            raise unittest.SkipTest("Las pruebas de ventana requieren CustomTkinter.") from None
        import tkinter
        try:
            cls.root = ctk.CTk()
        except tkinter.TclError:
            raise unittest.SkipTest("Las pruebas de ventana requieren una pantalla Tk.") from None
        from gui import theme
        cls.root.withdraw()
        theme.load_fonts()
        cls.ctk = ctk

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def tearDown(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def test_matrix_snapshots_and_both_views_are_preserved(self):
        from gui.widgets import ALL_STEPS, ONE_STEP, LinkButton, MatrixDisplay, StepWalker
        log = to_rref(Matrix([[1, -2, 1, 0], [0, 2, -8, 8], [-4, 5, 9, -9]])).log
        walker = StepWalker(self.root, log, first_caption="Matriz aumentada", bar_after=3)
        walker.pack()
        self.assertEqual(walker.total(), len(log) + 1)
        self.assertEqual(walker.caption(), "Matriz aumentada")
        self.assertIsInstance(walker._holder.winfo_children()[0], MatrixDisplay)
        self.assertIsInstance(walker._previous, LinkButton)
        self.assertEqual(walker._previous.cget("state"), "disabled")
        walker.go(1)
        self.assertEqual(walker.caption(), pretty_label(log[0].label))
        walker._toggle_all()
        self.assertEqual(len(walker._list.winfo_children()), walker.total())
        self.assertEqual(walker._unfold.cget("text"), ONE_STEP)
        walker._toggle_all()
        self.assertEqual(walker.caption(), pretty_label(log[0].label))
        self.assertEqual(walker._unfold.cget("text"), ALL_STEPS)

    def test_non_matrix_content_uses_the_same_navigation_and_list(self):
        from gui.widgets import LinkButton, StepWalker
        drawn = []
        seen = []

        def draw(master, index):
            drawn.append(index)
            self.ctk.CTkLabel(master, text=f"Estado {index}").pack()

        walker = StepWalker(
            self.root, captions=("Planteamiento", "Iteración 1", "Iteración 2"),
            draw_snapshot=draw, on_step=lambda index, total: seen.append((index, total)),
        )
        walker.pack()
        self.assertEqual(walker.caption(), "Planteamiento")
        self.assertEqual(drawn, [0])
        self.assertEqual(len(walker._dots.winfo_children()), 3)
        self.assertIsInstance(walker._next, LinkButton)
        walker.go(2)
        self.assertEqual(drawn[-1], 2)
        self.assertEqual(walker._next.cget("state"), "disabled")
        self.assertEqual(seen[-1], (2, 3))
        walker._toggle_all()
        self.assertEqual(drawn[-3:], [0, 1, 2])
        walker._toggle_all()
        self.assertEqual(walker.caption(), "Iteración 2")

    def test_bisection_reuses_widgets_and_disposes_them_on_input_change(self):
        from gui.pages.bisection import BisectionPage
        from gui.widgets import LinkButton, SegmentedControl, StepWalker
        page = BisectionPage(self.root)
        page.pack()
        page._calculate()
        self.assertIsInstance(page._criterion, SegmentedControl)
        self.assertIsInstance(page._examples, SegmentedControl)
        self.assertIsInstance(page._walker, StepWalker)
        self.assertEqual(page._walker.total(), len(page._result.steps) + 1)
        self.assertTrue(page._walker.caption().startswith("Intervalo inicial"))
        self.assertIsInstance(page._table_previous, LinkButton)
        self.assertIsInstance(page._table_next, LinkButton)
        page._walker.go(1)
        self.assertTrue(page._walker.caption().startswith("Iteración 1"))
        page._walker._toggle_all()
        self.assertEqual(len(page._walker._list.winfo_children()), page._walker.total())
        page._walker._toggle_all()
        result = page._result
        page._plot.zoom(0.7)
        page._plot.reset()
        self.assertIs(page._result, result)
        self.assertFalse(page._plot._plot_canvas.bind("<Motion>"))
        walker = page._walker
        page._function.insert("end", " + 0")
        self.assertIsNone(page._result)
        self.assertEqual(page._output, [])
        self.assertFalse(walker.winfo_exists())

    def test_table_format_changes_only_the_display_and_persists(self):
        from gui.pages.bisection import BisectionPage
        from gui.widgets import SegmentedControl, Stepper
        page = BisectionPage(self.root)
        page.pack()
        page._example("Polinomio del Excel")
        page._calculate()
        result = page._result

        def cell(row, column):
            return page._table.grid_slaves(row=row, column=column)[0].cget("text")

        self.assertIsInstance(page._format_choice, SegmentedControl)
        self.assertIsInstance(page._decimal_count, Stepper)
        self.assertEqual(cell(15, 0), "15")
        self.assertEqual(cell(15, 3), "0.76393")
        self.assertEqual(cell(15, 9), "0.00007")
        self.assertEqual(cell(1, 10), "—")
        page._format_choice.set("Científico")
        page._choose_table_format("Científico")
        self.assertEqual(cell(15, 9), "6.53825e-05")
        page._decimal_count._more.invoke()
        self.assertEqual(cell(15, 9), "6.538248e-05")
        self.assertIs(page._result, result)

        page._calculate()
        self.assertEqual(page._format_choice.get(), "Científico")
        self.assertEqual(page._decimal_count._value, 6)
        self.assertEqual(cell(15, 9), "6.538248e-05")
        page._example("Raíz de 2")
        page._tolerance.delete(0, "end")
        page._tolerance.insert(0, "1e-12")
        page._calculate()
        page._move_table(1)
        result = page._result
        self.assertEqual(page._table_page, 1)
        self.assertEqual(cell(1, 0), "16")
        page._decimal_count._less.invoke()
        self.assertEqual(page._table_page, 1)
        self.assertIs(page._result, result)
        self.assertIn("e+00", cell(1, 3))


if __name__ == "__main__":
    unittest.main()
