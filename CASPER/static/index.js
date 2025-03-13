require.config({
  paths: {
    vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.33.0/min/vs",
  },
});

let monacoEditorInstance = null;

require(["vs/editor/editor.main"], function () {
  defineCasperLanguage(monaco);
  defineCasperMonacoTheme(monaco);

  monacoEditorInstance = monaco.editor.create(
    document.getElementById("monacoEditor"),
    {
      value: window.initialCode || "",
      language: "casper",
      theme: "casperDark",
      automaticLayout: true,
      lineNumbers: "on",
    }
  );


  monacoEditorInstance.onDidChangeModelContent(debounce(() => {
    const code = monacoEditorInstance.getValue();
    console.log("Editor content changed:", code);
    checkErrors(code);
  }, 500));
});


async function checkErrors(code) {
  console.log("Requesting errors check...");
  try {
    const response = await fetch("/check_errors", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });

    const data = await response.json();
    console.log("Backend response:", data);
    updateMonacoDiagnostics(data.errors || []);
  } catch (error) {
    console.error("Fetch error:", error);
  }
}


function updateMonacoDiagnostics(errors) {
  const markers = errors.map(err => ({
    severity: monaco.MarkerSeverity.Error,
    startLineNumber: err.line,
    startColumn: err.startColumn,
    endLineNumber: err.line,
    endColumn: err.endColumn,
    message: err.message,
  }));

  monaco.editor.setModelMarkers(monacoEditorInstance.getModel(), "casper", markers);
}


function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}


function copyMonacoToTextarea() {
  const hiddenTextarea = document.getElementById("codeEditor");
  if (monacoEditorInstance) {
    hiddenTextarea.value = monacoEditorInstance.getValue();
  }
}

// Define Casper language
function defineCasperLanguage(monaco) {
  monaco.languages.register({ id: "casper" });
  monaco.languages.setMonarchTokensProvider("casper", {
    tokenizer: {
      root: [

        [/<<.*/, "comment"],
  
        [/---/, { token: "comment", next: "@multiLineComment" }],
  
        [
          /\b(?:birth|ghost|check|otherwise|otherwise_check|for|repeat|until|stop|skip|swap|shift|revive|Day|Night|measure|function|function_int|function_str|function_bln|function_flt|function_chr|function_list_int|function_list_str|function_list_bln|function_list_flt|function_list_chr|input|display|to_int|to_str|to_bln|to_flt|int|flt|bln|chr|str)\b/,
          "keyword",
        ],
        [/'([^'\\]|\\.)*'/, "string"],
        [/"([^"\\]|\\.)*"/, "string"],
        [/@[a-zA-Z_]\w*/, "identifier"],
        [/\$[a-zA-Z_]\w*/, "variable"],
        [/\b\d+(\.\d+)?\b/, "number"],
        [/[+\-*/=<>!%]+/, "operator"],
        [/[{}()\[\]]/, "delimiter"],
      ],
  
      multiLineComment: [
        [/---/, { token: "comment", next: "@pop" }],
        [/.|\n/, "comment"],
      ],
    },
  });
}

// Define custom Monaco theme for Casper
function defineCasperMonacoTheme(monaco) {
  monaco.editor.defineTheme("casperDark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "C586C0" },
      { token: "number", foreground: "B5CEA8" },
      { token: "string", foreground: "CE9178" },
      { token: "comment", foreground: "6A9955", fontStyle: "italic" },
      { token: "variable", foreground: "9CDCFE" },
      { token: "identifier", foreground: "4FC1FF" },
      { token: "delimiter", foreground: "FFFFFF" },
      { token: "operator", foreground: "D4D4D4" },
    ],
    colors: {
      "editor.background": "#1E1E1E",
      "editor.foreground": "#CCCCCC",
      "editorCursor.foreground": "#AEAFAD",
      "editor.lineHighlightBackground": "#2C2C2C",
      "editorLineNumber.foreground": "#858585",
      "editor.selectionBackground": "#264F78",
    },
  });
}

