"""Inicio refleja el registro y navega sin perder el estado de las herramientas."""
import unittest


class HomeTests(unittest.TestCase):
    def test_catalog_navigation_and_responsive_layout(self):
        try:
            from gui.app import Application, MODULES, HOME
            import tkinter
        except ImportError:
            self.skipTest("Requiere CustomTkinter")
        try:
            app = Application()
        except tkinter.TclError:
            self.skipTest("Requiere pantalla Tk")
        try:
            app.update()
            self.assertEqual(app._open, HOME.key)
            home = app._pages[HOME.key]
            self.assertEqual(set(home._shortcuts), {module.key for module in MODULES})
            for module in MODULES:
                self.assertTrue(module.description)
                home._shortcuts[module.key].invoke()
                self.assertEqual(app._open, module.key)
                page = app._pages[module.key]
                app.select(HOME.key)
                home._shortcuts[module.key].invoke()
                self.assertIs(app._pages[module.key], page)
                app.select(HOME.key)
            app.geometry("960x640")
            app.update()
            self.assertEqual(home._columns, 1)
            app.geometry("1400x800")
            app.update()
            self.assertEqual(home._columns, 2)
            app._toggle_theme()
            app.update()
        finally:
            app.destroy()
            # CTk deja tareas periodicas en el interprete; esta prueba crea
            # otra raiz despues, en vez de cerrar el proceso como la app real.
            for callback in app.tk.call("after", "info"):
                app.tk.call("after", "cancel", callback)
