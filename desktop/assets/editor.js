function groupEnd(latex, start) {
  if (latex[start] !== "{") return -1;
  let depth = 1;
  for (let index = start + 1; index < latex.length; index++) {
    if (latex[index] === "{") depth++;
    if (latex[index] === "}" && --depth === 0) return index + 1;
  }
  return -1;
}

function exportFunction(latex) {
  // Convierte la base en subíndice al primer argumento de log(base, argumento).
  const logs = /\\log\s*_\s*(?=(\{|\\[a-zA-Z]+|[a-zA-Z0-9]))/g;
  let result = "";
  let offset = 0;
  for (const match of latex.matchAll(logs)) {
    if (match.index < offset) continue;
    const start = match.index + match[0].length;
    const grouped = match[1] === "{";
    const end = grouped ? groupEnd(latex, start) : start + match[1].length;
    if (end === -1) return latex;
    const opening = /^\s*(?:\\(?:mleft|left)\s*)?\(/.exec(latex.slice(end));
    if (!opening) continue;
    const base = grouped ? exportFunction(latex.slice(start + 1, end - 1)) : match[1];
    result += latex.slice(offset, match.index) + "\\log" + opening[0] + base + ",";
    offset = end + opening[0].length;
  }
  return (result + latex.slice(offset))
    .replace(/\\(?:mleft|left)\s*(?:\||\\lvert\b)/g, "\\operatorname{abs}\\left(")
    .replace(/\\(?:mright|right)\s*(?:\||\\rvert\b)/g, "\\right)");
}

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
      end = groupEnd(latex, end);
      if (end === -1) return latex;
    }
    result += latex.slice(offset, match.index) +
      "\\left(" + match[0] + groupFractions(latex.slice(start, end)) + "\\right)";
    offset = end;
  }
  return result + latex.slice(offset);
}

function renderResult(host, blocks) {
  function element(tag, style, text) {
    const node = document.createElement(tag);
    node.className = style;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function math(value) {
    const formula = document.createElement("math-field");
    formula.readOnly = true;
    formula.value = value;
    return formula;
  }

  function render(parent, items) {
    let section = parent;
    let group;
    let groupKind;
    for (const [kind, value] of items) {
      if (kind !== groupKind) group = undefined;
      groupKind = kind;

      if (kind === "step") {
        const [number, title, body] = value;
        const step = element("section", "result-step");
        const header = element("div", "result-step-header");
        header.append(element("span", "result-step-index", number));
        const caption = element("div", "result-step-caption");
        render(caption, title);
        header.append(caption);
        const content = element("div", "result-step-body");
        render(content, body);
        step.append(header, content);
        parent.append(step);
      } else if (kind === "heading" || kind === "math-heading") {
        section = element("section", "result-section");
        const heading = element("div", "result-section-title");
        heading.append(kind === "math-heading" ? math(value) : value);
        section.append(heading);
        parent.append(section);
      } else if (kind === "fact" || kind === "solution") {
        if (!group) {
          group = element("div", "result-group");
          section.append(group);
        }
        const chip = element("div", `result-chip result-${kind}`);
        if (kind === "solution") {
          chip.append(math(value));
        } else {
          const [name, detail, nameLatex, isMath] = value;
          const title = element("span", "result-fact-name");
          title.append(nameLatex ? math(nameLatex) : name);
          chip.append(title, isMath ? math(detail) : detail);
        }
        group.append(chip);
      } else if (kind === "augmented") {
        const row = element("div", "result-augmented");
        row.append(math(value[0]), element("span", "result-augmented-divider"), math(value[1]));
        section.append(row);
      } else if (kind === "latex") {
        const row = element("div", "result-formula");
        row.append(math(value));
        section.append(row);
      } else if (kind === "status" || kind === "verdict") {
        const row = element("div", `result-${kind}`, value);
        row.dataset.status = value === "correcto" || value.includes("Única") ? "unique" :
          value.includes("Infinitas") ? "infinite" : "none";
        section.append(row);
      } else if (!value) {
        section = parent;
      } else {
        section.append(element("div", "result-line", value));
      }
    }
  }

  const content = document.createDocumentFragment();
  render(content, blocks);
  host.replaceChildren(content);
}

customElements.whenDefined("math-field").then(() => {
  MathfieldElement.fontsDirectory = new URL("vendor/fonts/", document.baseURI).href;
  MathfieldElement.soundsDirectory = null;
  const field = document.createElement("math-field");
  field.id = "expression";
  field.setAttribute("aria-label", "Función");
  field.smartFence = true;
  field.mathVirtualKeyboardPolicy = "manual";
  const editor = document.querySelector("#editor");
  editor.appendChild(field);
  const result = document.createElement("div");
  result.className = "result";
  result.hidden = true;
  editor.appendChild(result);
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

    function asNumber(latex, convert = ascii) {
      const scientific = /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\\times\s*10\^\{([+-]?\d+)\}$/.exec(latex.trim());
      return scientific ? scientific[1] + "e" + scientific[2] : convert(latex);
    }

    function asInput(latex) {
      if (kind === "matrix") {
        const matrix = /^\\begin\{([pbBvV]?matrix)\}([\s\S]*)\\end\{\1\}$/.exec(latex);
        if (!matrix) return "";
        return matrix[2].split("\\\\").map(row => row.split("&").map(cell => asNumber(cell)).join(";")).join("\n");
      }
      if (kind === "number") return asNumber(latex);
      if (kind === "constant") {
        return asNumber(latex, expression => ascii(groupFractions(exportFunction(expression))));
      }
      return ascii(kind === "function" ? groupFractions(exportFunction(latex)) : latex);
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
      field.hidden = format === "output";
      result.hidden = format !== "output";
      field.setAttribute("aria-label", name || "Resultado");
      if (format === "matrix") {
        field.setAttribute("data-matrix", "");
        field.registers.arraystretch = 2.25;
        field.maxMatrixCols = 1000;
      }
    };
    window.setResult = (blocks) => renderResult(result, blocks);
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
      const view = kind === "output" ? result : field;
      editorBridge.viewHeight(Math.ceil(view.getBoundingClientRect().height) + 2);
    }).observe(editor);
    field.addEventListener("input", sendValue);
    // MathLive puede abrir un exponente al mover el cursor sin emitir input.
    field.addEventListener("selection-change", sendValue);
    editorBridge.ready();
  });
});
