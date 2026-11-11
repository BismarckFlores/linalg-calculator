"""Catálogo de herramientas, etiquetas y fábricas de páginas."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

from .calculus import calculus_page

from .linear_algebra.determinant import determinant_page
from .linear_algebra.echelon import echelon_page
from .linear_algebra.gauss import gauss_page
from .linear_algebra.inverse import inverse_page
from .linear_algebra.lu import lu_page
from .linear_algebra.operations import operations_page
from .linear_algebra.vectors import vectors_page
from .number_systems.conversions import bases_page
from .number_systems.roman import roman_page
from .numerical_methods.bisection import BisectionPage
from .numerical_methods import newton_raphson as newton
from .numerical_methods.regula_falsi import RegulaFalsiPage


@dataclass(frozen=True)
class Tool:
    key: str
    section: str
    glyph: str
    title: str
    detail: str
    create: Callable[[], QWidget]


TOOLS = (
    Tool("gauss", "Sistemas Lineales", "▦", "Eliminación Gaussiana",
         "Resuelve sistemas por Gauss o Gauss–Jordan y verifica la solución.", gauss_page),
    Tool("echelon", "Sistemas Lineales", "▧", "Formas Escalonadas",
         "Comprueba las propiedades de una matriz y localiza sus pivotes.", echelon_page),
    Tool("operations", "Matrices", "⊞", "Operaciones Matriciales",
         "Suma, resta, multiplica, escala y transpone matrices.", operations_page),
    Tool("inverse", "Matrices", "⁻¹", "Matriz Inversa",
         "Calcula la inversa y resuelve sistemas con ella.", inverse_page),
    Tool("lu", "Matrices", "LU", "Factorización LU",
         "Descompón la matriz y resuelve sistemas por sustitución.", lu_page),
    Tool("determinant", "Matrices", "|A|", "Determinante",
         "Calcula por cofactores o factorización LU y compara ambos métodos.", determinant_page),
    Tool("vectors", "Vectores", "↗", "Operaciones Vectoriales",
         "Opera por componente y estudia combinaciones lineales.", vectors_page),
    Tool("bases", "Sistemas Numéricos", "⇄", "Conversiones",
         "Convierte enteros entre decimal, otras bases y romano.", bases_page),
    Tool("roman", "Sistemas Numéricos", "Ⅻ", "Aritmética Romana",
         "Suma, resta y multiplica numerales romanos con su procedimiento.", roman_page),
    Tool("calculus", "Cálculo", "∫", "Derivadas e integrales",
         "Obtén la derivada, la antiderivada o la integral definida de f(x).", calculus_page),
    Tool("bisection", "Métodos Numéricos", "½", "Método de Bisección",
         "Escribe con el editor matemático, grafica y aproxima una raíz.", BisectionPage),
    Tool("regula_falsi", "Métodos Numéricos", "RF", "Regula Falsi",
         "Aproxima una raíz por el cruce de la secante con el eje x.", RegulaFalsiPage),
    Tool("newton_raphson", "Métodos Numéricos", newton.GLYPH, newton.TITLE, newton.SUBTITLE,
         newton.NewtonRaphsonPage),
)
