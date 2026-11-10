# linalg-calculator

Calculadora de escritorio para MTM0120, Álgebra Lineal y Métodos Numéricos, Universidad Americana. Prioriza resultados comprobables y procedimientos que puedan explicarse en una defensa académica.

## Arquitectura y código

- `core/` es el motor Python compartido. Mantén allí el cálculo, la validación matemática y los registros de operaciones. Usa fracciones exactas para álgebra lineal y punto flotante para búsqueda de raíces.
- PySide6 es la interfaz oficial en desarrollo. Actualmente se ejecuta con `revamp.py` y vive en `revamp_poc/`. MathLive y sus recursos locales se cargan mediante Qt WebEngine. Conserva el funcionamiento sin conexión, las licencias, los temas y la entrada de texto alternativa.
- `main.py` y `gui/` ejecutan temporalmente la interfaz heredada CustomTkinter. Úsala como referencia funcional hasta completar y validar las once herramientas de escritorio.
- Mantén nombres de módulos y funciones en `snake_case`, clases en `PascalCase` y textos visibles en español. Conserva las APIs compartidas y las convenciones del módulo que modifiques.
- Compón páginas con los widgets existentes. Centraliza formularios, gráficas, tablas y pasos cuando los comparta más de una herramienta. Agrupa responsabilidades cohesionadas y extrae módulos cuando simplifiquen el mantenimiento.
- Al agregar una página, registra su navegación y tema, conecta el algoritmo de `core/` y presenta sus errores, resultados y procedimientos. Comprueba los estados al editar entradas o cambiar de herramienta.

## Verificación y publicación

- Ejecuta `python check.py` y `python -m unittest discover -s tests -v`. Comprueba también el flujo visible de cada página modificada, incluyendo ejemplos, errores, edición, navegación y representación de resultados.
- Trabaja en `Bismarck/ui-revamp` y conserva `main` demostrable. Antes de integrar, revisa los cambios, sincroniza el remoto y prueba el resultado del merge. Respeta las restricciones de GitHub y el trabajo ajeno. Evita reescrituras destructivas y líneas de coautoría o de sesión en commits y PR.
- Para entregas académicas, genera el Word editable y su PDF equivalente en `deliverables/out/`. Usa resultados y capturas obtenidos del programa, verifica ambos formatos y confirma el enlace al código publicado. Conserva los informes históricos.
- Retira CustomTkinter solo tras verificar equivalencia de las once herramientas y auditar dependencias, pruebas, documentación y puntos de entrada.

## Continuidad

Al comenzar, revisa la rama, los cambios pendientes y el estado en [la guía de PySide6](docs/revamp-poc.md). Actualiza ese estado tras cada etapa con lo verificado, lo pendiente y el estado de los merges. Consulta la [referencia del motor](docs/reference.md), el [diseño](docs/design.md) y la [guía de la interfaz heredada](docs/gui.md).
