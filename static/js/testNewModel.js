function startTest() {
    let progressBar = document.getElementById("progress-bar");
    let metricsTable = document.getElementById("metrics-table");
    let metric1 = document.getElementById("metric1");
    let metric2 = document.getElementById("metric2");
    let metric3 = document.getElementById("metric3");
    let width = 0;

    let interval = setInterval(function() {
        if (width >= 100) {
            clearInterval(interval);
            metricsTable.style.display = "table";
        } else {
            width++;
            progressBar.style.width = width + '%';
            progressBar.innerHTML = width + '%';

            metric1.innerHTML = 0.72;
            metric2.innerHTML = 0.23;
            metric3.innerHTML = 0.3;
        }
    }, 100);
}