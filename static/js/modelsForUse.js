document.getElementById('compareButton').addEventListener('click', function() {
            var table = document.getElementById('metricsTable');
            var formContainer = document.getElementById('formContainer');
            table.style.display = 'table';
            formContainer.style.display = 'block';

            var rows = table.rows;

            for (var i = 1; i < rows.length; i++) {
                var cell1 = rows[i].cells[1];
                var cell2 = rows[i].cells[2];
                if (cell1.innerText !== cell2.innerText) {
                    cell1.classList.add('highlight');
                    cell2.classList.add('highlight');
                } else {
                    cell1.classList.remove('highlight');
                    cell2.classList.remove('highlight');
                }
            }
        });

        document.getElementById('settingsForm').addEventListener('submit', function(event) {
            event.preventDefault();
            var param1 = document.getElementById('param1').value;
            var param2 = document.getElementById('param2').value;
            var param3 = document.getElementById('param3').value;

            document.getElementById('confirmParam1').value = param1;
            document.getElementById('confirmParam2').value = param2;
            document.getElementById('confirmParam3').value = param3;

            document.getElementById('formContainer').style.display = 'none';
            document.getElementById('confirmationContainer').style.display = 'block';
        });

        document.getElementById('confirmButton').addEventListener('click', function() {
            alert('Параметры обновлены!');
            document.getElementById('confirmationContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            document.getElementById('checkButton').style.display = 'block';
        });

        document.getElementById('checkButton').addEventListener('click', function() {
            var discrepancyHeader = document.getElementById('discrepancyHeader');
            var discrepancyTable = document.getElementById('discrepancyTable');
            var tbody = discrepancyTable.querySelector('tbody');

            // Пример проверки значений
            var param1 = document.getElementById('param1').value;
            var param2 = document.getElementById('param2').value;
            var param3 = document.getElementById('param3').value;

            // Ожидаемые значения (пример)
            var expectedParam1 = 333;
            var expectedParam2 = 123;
            var expectedParam3 = 2;

            // Очистка предыдущих данных
            tbody.innerHTML = "";

            if (param1 !== expectedParam1) {
                var row = tbody.insertRow();
                row.insertCell(0).innerText = "Параметр 1";
                row.insertCell(1).innerText = param1;
                row.insertCell(2).innerText = expectedParam1;
            }

            if (param2 !== expectedParam2) {
                var row = tbody.insertRow();
                row.insertCell(0).innerText = "Параметр 2";
                row.insertCell(1).innerText = param2;
                row.insertCell(2).innerText = expectedParam2;
            }
            if (param3 !== expectedParam3) {
            var row = tbody.insertRow();
            row.insertCell(0).innerText = "Параметр 3";
            row.insertCell(1).innerText = param3;
            row.insertCell(2).innerText = expectedParam3;
            }

            // Показываем таблицу с несоответствиями
            if (tbody.rows.length > 0) {
                discrepancyHeader.style.display = 'block';
                discrepancyTable.style.display = 'table';
            } else {
                discrepancyHeader.style.display = 'none';
                discrepancyTable.style.display = 'none';
            }
        });