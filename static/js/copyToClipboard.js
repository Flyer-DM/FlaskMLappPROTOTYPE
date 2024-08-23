document.getElementById("admin-email").addEventListener("click", function() {

    const tempInput = document.createElement("input");
    tempInput.value = this.textContent;
    document.body.appendChild(tempInput);

    tempInput.select();
    document.execCommand("copy");

    document.body.removeChild(tempInput);

    this.classList.add("copied");

    setTimeout(() => {
        this.classList.remove("copied");
        }, 1000);
});