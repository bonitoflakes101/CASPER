document.addEventListener("DOMContentLoaded", function () {
    let codeEditor = document.getElementById("codeEditor");
    let lineNumbers = document.getElementById("lineNumbers");

    function updateLineNumbers() {
        let lines = codeEditor.value.split("\n").length;
        lineNumbers.innerHTML = Array.from({ length: lines }, (_, i) => i + 1).join("<br>");
    }

    function syncScroll() {
        lineNumbers.scrollTop = codeEditor.scrollTop;
    }

    function adjustHeight() {
        codeEditor.style.height = codeEditor.scrollHeight + "px";
    }

    // Ensure everything is updated on page load
    updateLineNumbers();
    adjustHeight();

    // Attach event listeners
    codeEditor.addEventListener("input", () => {
        updateLineNumbers();
        adjustHeight();
    });

    codeEditor.addEventListener("scroll", syncScroll);
});
