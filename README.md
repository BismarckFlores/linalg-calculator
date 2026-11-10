<p align="center">
  <img src="desktop/assets/icon.svg" width="76" height="76" alt="Logotipo de linalg-calculator">
</p>

<h1 align="center">linalg-calculator</h1>

<p align="center">
  <strong>Álgebra lineal y métodos numéricos, paso a paso.</strong><br>
  Resuelve sistemas con fracciones exactas y explora raíces con gráficas interactivas.
</p>

<p align="center">
  <a href="#inicio-rápido"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.12 o posterior"></a>
  <a href="requirements.txt"><img src="https://img.shields.io/badge/PySide6-6.12.0-25804F?style=flat-square&amp;logo=qt&amp;logoColor=white" alt="PySide6 6.12.0"></a>
  <a href="docs/gui.md#editor-de-funciones"><img src="https://img.shields.io/badge/MathLive-0.111.4-6355A4?style=flat-square" alt="MathLive 0.111.4"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-316B85?style=flat-square" alt="Licencia MIT"></a>
  <a href="https://github.com/BismarckFlores/linalg-calculator/commits/main/"><img src="https://img.shields.io/badge/Desarrollo-En%20curso-2869A5?style=flat-square" alt="Desarrollo en curso"></a>
</p>

<p align="center">
  <a href="#inicio-rápido"><strong>🚀 Probar la app</strong></a> ·
  <a href="#características">Características</a> ·
  <a href="docs/README.md">Documentación</a>
</p>

---

<table>
  <tr>
    <th>Eliminación gaussiana · Tema claro</th>
    <th>Regula Falsi · Tema oscuro</th>
  </tr>
  <tr>
    <td><a href="docs/images/eliminacion-gaussiana.png"><img src="docs/images/eliminacion-gaussiana.png" width="450" alt="Operación por filas, sistema equivalente y solución exacta"></a></td>
    <td><a href="docs/images/regula-falsi.png"><img src="docs/images/regula-falsi.png" width="450" alt="Editor MathLive y gráfica de cos(x) menos x con el intervalo y la aproximación"></a></td>
  </tr>
</table>

## Características

- **Sistemas lineales.** Ingresa coeficientes o ecuaciones, aplica Gauss o Gauss–Jordan y revisa las operaciones por filas, los pivotes y la clasificación de la solución.
- **Matrices y vectores.** Calcula inversas, factorizaciones LU, determinantes y combinaciones lineales. Las operaciones de álgebra lineal conservan las fracciones exactas.
- **Búsqueda de raíces.** Usa Bisección o Regula Falsi, explora la gráfica con zoom y arrastre, y revisa la tabla de iteraciones.
- **Conversiones.** Convierte entre decimal, bases de 2 a 36 y números romanos. La aritmética romana incluye suma, resta y multiplicación.
- **Escritorio en español.** Once herramientas con temas claro, oscuro y automático. El editor y sus fuentes se cargan localmente, por lo que puedes usar la app sin conexión después de instalarla.

## Inicio rápido

Necesitas **Python 3.12 o posterior** y una sesión gráfica.

```bash
git clone https://github.com/BismarckFlores/linalg-calculator.git
cd linalg-calculator
```

**Linux y macOS**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

**Windows · PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Para probarla, abre **Eliminación Gaussiana**, pulsa **Calcular** con el ejemplo
precargado y usa **Siguiente** para recorrer las operaciones.

## Cómo funciona

La interfaz oficial usa **PySide6** y ejecuta el editor **MathLive** en
**Qt WebEngine**. El motor de **Python** valida las entradas, calcula con
`Fraction` en álgebra lineal y usa punto flotante para aproximar raíces.
El registro de operaciones e iteraciones alimenta el paso a paso y las tablas.
La versión **CustomTkinter** se conserva como referencia histórica en la
[guía de la interfaz heredada](docs/legacy-gui.md).

## 📚 Documentación

- [Índice de documentación](docs/README.md) · Guías, ejercicios y referencia.
- [Guía de uso](docs/usage.md) · Primeros ejercicios e instalación.
- [Un sistema resuelto de principio a fin](docs/how-it-works.md) · Eliminación, despeje y comprobación.
- [Bisección y Regula Falsi](docs/bisection.md) · Criterios de parada y ejemplos.
- [Diseño y arquitectura](docs/design.md) · Motor, interfaz y registro de operaciones.

El código del proyecto está bajo la [licencia MIT](LICENSE).
Los recursos incluidos conservan sus avisos de [MathLive](desktop/assets/vendor/LICENSE.txt)
y [KaTeX](desktop/assets/vendor/LICENSE-KaTeX.txt).
