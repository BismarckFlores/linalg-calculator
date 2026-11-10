function groupFractions(latex) {
  // AsciiMath exports a fraction as (a)/(b). Group it before a power or product.
  const fractions = /\\(?:frac|dfrac|tfrac)\s*(?=\{)/g;
  let result = "";
  let offset = 0;
  for (const match of latex.matchAll(fractions)) {
    if (match.index < offset) continue;
    const start = match.index + match[0].length;
    let end = start;
    for (let argument = 0; argument < 2; argument++) {
      while (/\s/.test(latex[end] || "")) end++;
      if (latex[end] !== "{") return latex;
      let depth = 1;
      while (depth && ++end < latex.length) {
        if (latex[end] === "{") depth++;
        if (latex[end] === "}") depth--;
      }
      if (depth) return latex;
      end++;
    }
    result += latex.slice(offset, match.index) +
      "\\left(" + match[0] + groupFractions(latex.slice(start, end)) + "\\right)";
    offset = end;
  }
  return result + latex.slice(offset);
}

customElements.whenDefined("math-field").then(() => {
  MathfieldElement.fontsDirectory = new URL("vendor/fonts/", document.baseURI).href;
  MathfieldElement.soundsDirectory = null;
  const field = document.createElement("math-field");
  field.id = "expression";
  field.setAttribute("aria-label", "Función");
  field.smartFence = true;
  field.mathVirtualKeyboardPolicy = "manual";
  document.querySelector("#editor").appendChild(field);
  field.keybindings = field.keybindings.filter(({command}) => command !== "toggleVirtualKeyboard");
  const matrixStyle = document.createElement("style");
  // MathLive 0.111.4 representa la matriz como columnas de celdas en el shadow DOM.
  // El fondo es decorativo y deja que MathLive reciba el clic y la selección.
  matrixStyle.textContent = `
    :host([data-matrix]) .ML__mtable .ML__arraycolsep { width: 6px !important; }
    :host([data-matrix]) .ML__mtable > .col-align-c > .ML__vlist-t >
    .ML__vlist-r:first-child > .ML__vlist > span > span[style*="inline-block"] {
      position: relative;
      min-width: 54px;
      text-align: center;
      isolation: isolate;
    }
    :host([data-matrix]) .ML__mtable > .col-align-c > .ML__vlist-t >
    .ML__vlist-r:first-child > .ML__vlist > span > span[style*="inline-block"]::before {
      content: "";
      position: absolute;
      inset: -7px 0 13px;
      border: 1px solid var(--app-border);
      border-radius: var(--app-radius);
      background: var(--app-field);
      pointer-events: none;
      z-index: -1;
    }
  `;
  field.shadowRoot.append(matrixStyle);
  new QWebChannel(qt.webChannelTransport, ({objects: {editorBridge}}) => {
    let kind = "function";
    let lastLatex = field.value;
    const ascii = MathLive.convertLatexToAsciiMath;

    function asInput(latex) {
      if (kind === "matrix") {
        const matrix = /^\\begin\{([pbBvV]?matrix)\}([\s\S]*)\\end\{\1\}$/.exec(latex);
        if (!matrix) return "";
        return matrix[2].split("\\\\").map(row => row.split("&").map(cell => ascii(cell)).join(";")).join("\n");
      }
      return ascii(kind === "function" ? groupFractions(latex) : latex);
    }

    function sendValue() {
      if (field.readOnly) return;
      const latex = field.value;
      if (latex === lastLatex) return;
      lastLatex = latex;
      const incomplete = latex.includes("\\placeholder") || latex.includes("^{}") || field.errors.length > 0;
      editorBridge.changed(incomplete ? "" : asInput(latex));
    }

    window.configureEditor = (format, name) => {
      kind = format;
      document.documentElement.dataset.kind = format;
      field.readOnly = format === "output";
      field.setAttribute("aria-label", name || "Resultado");
      if (format === "matrix") {
        field.setAttribute("data-matrix", "");
        field.registers.arraystretch = 2.25;
        field.maxMatrixCols = 1000;
      }
    };
    window.setFormula = (latex) => {
      field.setValue(latex, {silenceNotifications: true});
      lastLatex = field.value;
    };
    window.setEditorTheme = (mode, colors) => {
      const root = document.documentElement;
      root.setAttribute("theme", mode);
      for (const [name, value] of Object.entries(colors)) {
        root.style.setProperty(`--app-${name}`, value);
      }
    };
    window.focusFormula = () => field.focus({preventScroll: true});
    window.editFormula = (command) => field.executeCommand(command);
    field.addEventListener("keydown", (event) => {
      if (kind !== "equations" || event.key !== "Enter" || event.ctrlKey || event.altKey ||
          event.shiftKey || event.metaKey || field.mode !== "math") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if (field.value.startsWith("\\displaylines{") &&
          field.position === field.lastOffset && field.selectionIsCollapsed) {
        field.executeCommand("moveToPreviousChar");
      }
      field.executeCommand("addRowAfter");
    }, true);
    field.addEventListener("paste", (event) => {
      const clipboard = event.clipboardData;
      if (!clipboard || field.readOnly || field.mode !== "math" ||
          clipboard.getData("application/x-latex") || clipboard.getData("application/json+mathlive")) return;
      const text = clipboard.getData("text/plain").trim();
      if (!text || /[\\$]/.test(text)) return;

      event.preventDefault();
      event.stopImmediatePropagation();
      const value = field.value;
      const selection = JSON.stringify(field.selection);
      editorBridge.latexForPaste(text, (latex) => {
        if (field.value !== value || JSON.stringify(field.selection) !== selection) return;
        const whole = latex.startsWith("\\begin{bmatrix}") || latex.startsWith("\\displaylines{");
        field.insert(latex || text, {
          format: latex ? "latex" : "auto",
          insertionMode: latex && whole ? "replaceAll" : "replaceSelection",
        });
      });
    }, true);
    new ResizeObserver(() => {
      editorBridge.viewHeight(Math.ceil(field.getBoundingClientRect().height) + 2);
    }).observe(field);
    field.addEventListener("input", sendValue);
    // MathLive puede abrir un exponente al mover el cursor sin emitir input.
    field.addEventListener("selection-change", sendValue);
    editorBridge.ready();
  });
});
