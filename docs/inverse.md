# Matriz inversa

**Matrices → Matriz Inversa** usa la entrada **Coeficientes / Ecuaciones**.
Puedes redimensionar la cuadrícula o escribir una ecuación por línea. En
**Calcular A⁻¹**, la app usa la matriz de coeficientes A de las ecuaciones.
Los enteros, decimales y fracciones se conservan exactamente. El tamaño de la
matriz está limitado en la práctica por el tiempo de cálculo y la memoria.

El recorrido muestra la reducción con fracciones apiladas y permite ir a
cualquier paso o verlos todos. La app reduce `[A | Iₙ]` por Gauss–Jordan.
Si la parte izquierda llega a `Iₙ`, la parte derecha es `A⁻¹`. Comprueba
`A A⁻¹ = Iₙ` y `A⁻¹ A = Iₙ` con la matriz original. Si A es rectangular,
tiene una entrada ilegible o tiene menos de n pivotes, explica el motivo.

**Resolver A x = b** acepta A y b en cuadrículas separadas o los obtiene de
las ecuaciones. Cada modo conserva sus datos al cambiar al otro. Calcula
`x = A⁻¹b` y comprueba `Ax = b` con la A original. Este método requiere
que A sea invertible. Para una A singular, usa Eliminación Gaussiana
para clasificar el sistema.

## Teoremas y condiciones

- **Definición.** Una matriz cuadrada A de orden n es invertible si existe una
  matriz C del mismo orden con `AC = Iₙ` y `CA = Iₙ`. Esa C es `A⁻¹`.
- **Orden dos.** Para `A = [[a,b],[c,d]]`, si `ad − bc ≠ 0`, entonces
  `A⁻¹ = (1/(ad − bc)) [[d,−b],[−c,a]]`. Si `ad − bc = 0`, A es singular.
  Esta fórmula es para matrices 2×2. La app usa Gauss–Jordan para cualquier orden.
- **Sistemas lineales.** Si A es invertible de orden n, para todo `b ∈ ℝⁿ`
  hay una única solución de `Ax = b`, dada por `x = A⁻¹b`.
- **Inversa de la inversa.** Si A es invertible, también lo es `A⁻¹` y
  `(A⁻¹)⁻¹ = A`.
- **Producto.** Si A y B son invertibles y del mismo orden, AB es invertible
  y `(AB)⁻¹ = B⁻¹A⁻¹`.
- **Transpuesta.** Si A es invertible, Aᵀ es invertible y `(Aᵀ)⁻¹ = (A⁻¹)ᵀ`.

Para una matriz cuadrada de orden n, el **teorema de la matriz invertible**
establece que estas afirmaciones son equivalentes.

| Letra | Afirmación |
| --- | --- |
| a | A es invertible. |
| b | A es equivalente por filas a `Iₙ`. |
| c | A tiene n posiciones pivote. |
| d | `Ax = 0` solo tiene la solución trivial. |
| e | Las columnas de A son linealmente independientes. |
| f | La transformación `x ↦ Ax` es inyectiva. |
| g | `Ax = b` tiene solución para todo `b ∈ ℝⁿ`. |
| h | Las columnas de A generan `ℝⁿ`. |
| i | `x ↦ Ax` aplica `ℝⁿ` sobre `ℝⁿ`. |
| j | Existe una C de orden n con `CA = Iₙ`. |
| k | Existe una D de orden n con `AD = Iₙ`. |
| l | Aᵀ es invertible. |

La condición de que A sea cuadrada es parte del teorema.

## Ejercicios de clase

1. **Calcular una inversa.** Para `A = [[3,4],[5,6]]`, `ad − bc = −2` y
   `A⁻¹ = [[−3,2],[5/2,−3/2]]`. Comprueba ambos productos con `I₂`.
2. **Práctica 2.2.** Introduce `[[1,−2,−1],[−1,5,6],[5,−4,5]]`. Tiene
   rango 2. La parte izquierda de `[A | I₃]` no puede reducirse a `I₃`.
3. **Aplicar la inversa a un sistema.** Con `A = [[3,4],[5,6]]` y
   `b = [3,7]ᵀ`, calcula `x = A⁻¹b = [5,−3]ᵀ` y verifica `Ax = b`.
   Con `A = [[1,0,−2],[3,1,−2],[−5,−1,9]]` y `b = [3,7,−16]ᵀ`,
   se obtiene `x = [1,2,−1]ᵀ`.
4. **Usar el teorema.** La matriz `[[2,3,4],[2,3,4],[2,3,4]]` tiene filas
   repetidas y menos de tres pivotes. Es singular, sus columnas son
   dependientes y algunos sistemas `Ax = b` son incompatibles. La matriz
   `[[1,0,−2],[3,1,−2],[−5,−1,9]]` tiene tres pivotes.

Referencia de las fórmulas y ejercicios: `Materiales de estudio/Inversa de una Matriz.pptx`.
