document.addEventListener('DOMContentLoaded', function () {
    const customSelect1 = document.getElementById('customSelect1');
    const customSelect2 = document.getElementById('customSelect2');
    const submitButton = document.getElementById('submitButton');
    const hiddenSelectedValues = document.getElementById('hiddenSelectedValues');

    customSelect1.addEventListener('click', function (event) {
        const clickedItem = event.target;

        if (clickedItem.tagName.toLowerCase() === 'li') {

            if (clickedItem.classList.contains('selected')) {
                clickedItem.classList.remove('selected');
            } else {
                clickedItem.classList.add('selected');
            }
        }
    });

    customSelect2.addEventListener('click', function (event) {
        const clickedItem = event.target;

        if (clickedItem.tagName.toLowerCase() === 'li') {

            if (clickedItem.classList.contains('selected')) {
                clickedItem.classList.remove('selected');
            } else {
                clickedItem.classList.add('selected');
            }
        }
    });

    submitButton.addEventListener('click', function () {
        const selectedItems1 = customSelect1.querySelectorAll('.selected');
        const selectedItems2 = customSelect2.querySelectorAll('.selected');
        const values1 = Array.from(selectedItems1).map(item => item.getAttribute('data-value'));
        const values2 = Array.from(selectedItems2).map(item => item.getAttribute('data-value'));
        const values = values1.concat(values2)
        hiddenSelectedValues.value = values.join(',');
        document.getElementById('selectionForm').submit();
    });
});