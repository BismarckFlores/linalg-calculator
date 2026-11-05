"""La distancia de rueda no depende de las unidades predeterminadas de CTk."""
import unittest
from types import SimpleNamespace


class ScrollTests(unittest.TestCase):
    def test_windows_units_and_wheel_direction(self):
        try:
            from gui.app import Application
            import tkinter
        except ImportError:
            self.skipTest("Requiere CustomTkinter")
        try:
            app = Application()
        except tkinter.TclError:
            self.skipTest("Requiere pantalla Tk")
        try:
            app.geometry("960x640")
            app.select("bisection")
            page = app._pages["bisection"]
            page._graph()
            app.update()
            for frame in (app._container, app._navigation):
                frame._parent_canvas.configure(yscrollincrement=1)
            app._wire_wheel()
            for frame in (app._container, app._navigation):
                self.assertEqual(float(frame._parent_canvas.cget("yscrollincrement")), 30)
            canvas = app._container._parent_canvas
            canvas.yview_moveto(0)
            app._wheel(SimpleNamespace(widget=page._function, num="??", delta=-120))
            after = canvas.yview()[0]
            self.assertGreater(after, 0)
            app._wheel(SimpleNamespace(widget=page._function, num="??", delta=120))
            self.assertLess(canvas.yview()[0], after)
            canvas.yview_moveto(0)
            app._wheel(SimpleNamespace(widget=page._function, num=5, delta=0))
            self.assertAlmostEqual(canvas.yview()[0], after)
        finally:
            app.destroy()
