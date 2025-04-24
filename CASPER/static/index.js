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

  monacoEditorInstance.onDidChangeModelContent(
    debounce(() => {
      const code = monacoEditorInstance.getValue();
      console.log("Editor content changed:", code);
      checkErrors(code);
    }, 500)
  );
});

async function checkErrors(code) {
  console.log("Requesting errors check...");
  try {
    const response = await fetch("/check_errors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
  const markers = errors.map((err) => ({
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
          /\b(?:birth|ghost|check|otherwise|otherwise_check|for|repeat|continue|while|stop|skip|swap|shift|revive|Day|Night|measure|function|function_int|function_str|function_bln|function_flt|function_chr|function_list_int|function_list_str|function_list_bln|function_list_flt|function_list_chr|input|display|to_int|to_str|to_bln|to_flt|int|flt|bln|chr|str)\b/,
          "keyword",
        ],
        [/'([^'\\]|\\.)*'/, "string"],
        [/"([^"\\]|\\.)*"/, "string"],
        [/\b(?:push|splice)\b/, "identifier"],
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


function openTab(evt, tabName) {
  const tabcontents = document.getElementsByClassName("tabcontent");
  for (let i = 0; i < tabcontents.length; i++) {
    tabcontents[i].style.display = "none";
  }

  const tablinks = document.getElementsByClassName("tablink");
  for (let i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.classList.add("active");
}

// Terminal input handling
document.addEventListener("DOMContentLoaded", function () {
  const terminalInput = document.getElementById("terminal-input");
  const outputElement = document.getElementById("output");
  const stopButton = document.getElementById("stopCodeButton");
  const runButton = document.querySelector(".run-button");

  // Ensure stop button is disabled on page load
  if (stopButton) {
    stopButton.disabled = true;
  }

  if (terminalInput) {
    // Set up polling for program status - check more frequently for better responsiveness
    let programStatusInterval = setInterval(checkProgramStatus, 500);

    terminalInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        const userInput = terminalInput.value;

        // Clear the input field
        terminalInput.value = "";

        // Send input to the backend
        submitUserInput(userInput);
      }
    });

    // Stop button functionality
    if (stopButton) {
      stopButton.addEventListener("click", function () {
        stopRunningProgram();
        // Immediately disable input field and stop button when clicked
        terminalInput.disabled = true;
        stopButton.disabled = true;
      });
    }

    // Check program status initially
    checkProgramStatus();
  }

  // Function to check if the program is waiting for input
  function checkProgramStatus() {
    fetch('/program_status')
      .then(response => response.json())
      .then(data => {
        // Find last non-empty line in the output
        const lines = data.output.trim().split('\n');
        const lastLine = lines[lines.length - 1] || '';

        // Only consider it a prompt if it matches exactly
        const promptInOutput = lastLine === data.prompt;

        // Update the output display with clean content
        outputElement.textContent = data.output;
        outputElement.scrollTop = outputElement.scrollHeight;

        // First, ensure stop button is disabled by default
        if (stopButton) {
          stopButton.disabled = true;
        }

        // Then only enable it when explicitly in running or waiting_for_input state
        if (data.status === 'waiting_for_input' || data.status === 'running') {
          // Enable stop button when the program is running
          if (stopButton) {
            stopButton.disabled = false;
          }

          if (data.status === 'waiting_for_input') {
            // Only append prompt if it's not exactly the last line
            if (data.prompt && !promptInOutput) {
              // Remove any partial prompt from the end of output
              let cleanOutput = data.output.trim();
              if (cleanOutput.endsWith(data.prompt)) {
                cleanOutput = cleanOutput.slice(0, -data.prompt.length).trim();
              }
              outputElement.textContent = cleanOutput + '\n' + data.prompt;
              outputElement.scrollTop = outputElement.scrollHeight;
            }

            // Enable input field
            terminalInput.disabled = false;
            terminalInput.focus();
            console.log("Input enabled - waiting for input");
          } else {
            // Disable input field when not waiting for input
            terminalInput.disabled = true;
            console.log("Input disabled - not waiting for input");
          }
        } else {
          // Program is not running or has finished, disable everything
          console.log("Program is idle or finished - disabling input and stop button");
          terminalInput.disabled = true;
          if (stopButton) {
            stopButton.disabled = true;
          }
        }
      })
      .catch(error => {
        console.error('Error checking program status:', error);
      });
  }

  // Function to stop the running program
  function stopRunningProgram() {
    fetch('/stop_program', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(response => response.json())
      .then(data => {
        // Update the output terminal with the stopped message
        outputElement.textContent = data.output;
        outputElement.scrollTop = outputElement.scrollHeight;

        // Disable the stop button
        if (stopButton) {
          stopButton.disabled = true;
        }

        console.log("Program stopped");
      })
      .catch(error => {
        console.error('Error stopping program:', error);
        outputElement.textContent += '\nError stopping the program. Please try again.';
        outputElement.scrollTop = outputElement.scrollHeight;
      });
  }

  // Function to submit user input to the backend
  function submitUserInput(input) {
    fetch('/provide_input', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ input: input })
    })
      .then(response => response.json())
      .then(data => {
        // Update the output terminal
        outputElement.textContent = data.output;
        // Scroll to the bottom
        outputElement.scrollTop = outputElement.scrollHeight;

        // Check if program is finished (including validation failures)
        if (data.status === "program_finished") {
          console.log("Program has finished executing - disabling input");
          terminalInput.disabled = true;
          stopButton.disabled = true;
        }
        // If still waiting for input, focus the input field
        else if (data.waiting_for_more) {
          terminalInput.focus();
        }
      })
      .catch(error => {
        console.error('Error submitting input:', error);
        // Display error message in the terminal
        outputElement.textContent += '\nError communicating with the server. Please try again.';
        outputElement.scrollTop = outputElement.scrollHeight;
      });
  }
});
