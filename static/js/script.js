(function () {
    var fileInput1 = document.getElementById("fileInput1");
    var fileInput2 = document.getElementById("fileInput2");

    if (fileInput1) {
        fileInput1.addEventListener("change", function () {
            displayFileName(fileInput1);
        });
    }

    if (fileInput2) {
        fileInput2.addEventListener("change", function () {
            displayFileName(fileInput2);
        });
    }
})();

function displayFileName(inputElement) {
    console.log("Function called.");
    var fileName = inputElement.files[0].name;
    console.log("Selected file:", fileName);
    var fileNameDisplay = inputElement.parentElement.nextElementSibling;
    fileNameDisplay.textContent = fileName;
}
