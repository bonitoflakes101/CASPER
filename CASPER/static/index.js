
function updateLineNumbers() {}
function syncScroll() {}

console.log("index.js loaded. Setting up a custom Monaco theme...");


function defineCasperMonacoTheme(monaco) {
  monaco.editor.defineTheme('casperDark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: 'C586C0' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
      { token: 'variable', foreground: '9CDCFE' },
      { token: 'identifier', foreground: '4FC1FF' },
      { token: 'delimiter', foreground: 'FFFFFF' },
      { token: 'operator', foreground: 'D4D4D4' }
    ],
    colors: {
      'editor.background': '#1E1E1E',
      'editor.foreground': '#CCCCCC',
      'editorCursor.foreground': '#AEAFAD',
      'editor.lineHighlightBackground': '#2C2C2C',
      'editorLineNumber.foreground': '#858585',
      'editor.selectionBackground': '#264F78'
    }
  });
}


