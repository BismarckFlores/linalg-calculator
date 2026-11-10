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
  field.mathVirtualKeyboardPolicy = "manual";
  document.querySelector("#editor").appendChild(field);
  field.keybindings = field.keybindings.filter(({command}) => command !== "toggleVirtualKeyboard");
  new QWebChannel(qt.webChannelTransport, ({objects: {editorBridge}}) => {
    let lastLatex = field.value;
    function sendValue() {
      const latex = field.value;
      if (latex === lastLatex) return;
      lastLatex = latex;
      const incomplete = latex.includes("\\placeholder") || latex.includes("^{}") || field.errors.length > 0;
      editorBridge.changed(incomplete ? "" : MathLive.convertLatexToAsciiMath(groupFractions(latex)));
    }

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
    field.addEventListener("paste", (event) => {
      const clipboard = event.clipboardData;
      if (!clipboard || field.mode !== "math" ||
          clipboard.getData("application/x-latex") || clipboard.getData("application/json+mathlive")) return;
      const text = clipboard.getData("text/plain").trim();
      if (!text || /[\\$]/.test(text)) return;

      event.preventDefault();
      event.stopImmediatePropagation();
      const value = field.value;
      const selection = JSON.stringify(field.selection);
      editorBridge.latexForPaste(text, (latex) => {
        if (field.value !== value || JSON.stringify(field.selection) !== selection) return;
        field.insert(latex || text, {format: latex ? "latex" : "auto"});
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
