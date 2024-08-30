function sortTable(columnIndex) {
    var table, rows, switching, i, x, y, shouldSwitch, direction, switchcount = 0;
    table = document.getElementById("modelsTable");
    switching = true;
    direction = "asc"; // Устанавливаем направление сортировки по умолчанию на "asc"

    resetArrows(table); // Сброс стрелок перед сортировкой

    while (switching) {
        switching = false;
        rows = table.rows;

        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

            if (direction == "asc") {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            } else if (direction == "desc") {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount == 0 && direction == "asc") {
                direction = "desc";
                switching = true;
            }
        }
    }

    // Добавляем стрелку к отсортированному столбцу
    var th = table.getElementsByTagName("TH")[columnIndex];
    th.classList.add(direction === "asc" ? "sort-asc" : "sort-desc");
}

function resetArrows(table) {
    var ths = table.getElementsByTagName("TH");
    for (var i = 0; i < ths.length; i++) {
        ths[i].classList.remove("sort-asc", "sort-desc");
    }
} 