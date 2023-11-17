// IIFE (Immediately-Invoked Function Expression)

(function () {
    let fileInput1 = document.getElementById("fileInput1");
    let fileInput2 = document.getElementById("fileInput2");

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
// # This code is an Immediately-Invoked Function Expression (IIFE) that is executed immediately after it is defined.
// # It creates an anonymous function that does the following:
// # - It assigns the DOM element with the id "fileInput1" to the variable fileInput1.
// # - It assigns the DOM element with the id "fileInput2" to the variable fileInput2.
// # - It checks if fileInput1 exists (is not null or undefined).
// #   - If fileInput1 exists, it adds an event listener to it for the "change" event.
// #     - When the "change" event is triggered on fileInput1, it calls the displayFileName function with fileInput1 as an argument.
// # - It checks if fileInput2 exists (is not null or undefined).
// #   - If fileInput2 exists, it adds an event listener to it for the "change" event.
// #     - When the "change" event is triggered on fileInput2, it calls the displayFileName function with fileInput2 as an argument.
//
// # The purpose of this code is to add event listeners to the file input elements with ids "fileInput1" and "fileInput2".
// # When the user selects a file using either of these input elements, the displayFileName function is called to display the selected file name.

function displayFileName(inputElement) {
    console.log("Function called.");
    let fileName = inputElement.files[0].name;
// This line of code declares a variable called "fileName" using the "let" keyword.
// It assigns the value of the "name" property of the first file in the "files" property of the "inputElement" object.
// The "inputElement" object represents a file input element in the DOM.
// The "files" property is an array-like object that contains the files selected by the user.
// By accessing the first file using the index [0], we can retrieve its name using the "name" property.
// The retrieved file name is then assigned to the "fileName" variable.
    console.log("Selected file:", fileName);
    let fileNameDisplay = inputElement.parentElement.nextElementSibling;
    fileNameDisplay.textContent = fileName;
}



