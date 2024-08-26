document.addEventListener('DOMContentLoaded', function () {
    const customSelect = document.getElementById('customSelect');
    const selectedValues = document.getElementById('selectedValues');
    const submitButton = document.getElementById('submitButton');
    const hiddenSelectedValues = document.getElementById('hiddenSelectedValues');
    const maxSelections = 5;

    customSelect.addEventListener('click', function (event) {
        const clickedItem = event.target;

        if (clickedItem.tagName.toLowerCase() === 'li') {
            const selectedItems = customSelect.querySelectorAll('.selected');

            if (clickedItem.classList.contains('selected')) {
                clickedItem.classList.remove('selected');
            } else {
                if (selectedItems.length <= maxSelections) {
                    clickedItem.classList.add('selected');
                } else {
                    alert(`Можно выбрать не более ${maxSelections} значений!`);
                }
            }

            const updatedSelectedItems = customSelect.querySelectorAll('.selected');
            selectedValues.textContent = `Выбрано: ${updatedSelectedItems.length}`;
        }
    });

    submitButton.addEventListener('click', function () {
        const selectedItems = customSelect.querySelectorAll('.selected');
        const values = Array.from(selectedItems).map(item => item.getAttribute('data-value'));
        hiddenSelectedValues.value = values.join(',');

        document.getElementById('selectionForm').submit();
    });
});