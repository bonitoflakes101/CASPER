document.addEventListener("DOMContentLoaded", updateLineNumbers);

function updateLineNumbers() {
    let codeEditor = document.getElementById("codeEditor");
    let lineNumbers = document.getElementById("lineNumbers");
    let lines = codeEditor.value.split("\n").length;
    
    let lineText = "";
    for (let i = 1; i <= lines; i++) {
        lineText += i + "\n";
    }
    
    lineNumbers.textContent = lineText;
}

function syncScroll() {
    let codeEditor = document.getElementById("codeEditor");
    let lineNumbers = document.getElementById("lineNumbers");
    lineNumbers.scrollTop = codeEditor.scrollTop;
}
