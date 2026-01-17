document.addEventListener("DOMContentLoaded", function() {
    console.log("Insight Script Loaded...");

    fetch('/insight_api')
    .then(response => response.json())
    .then(apiResponse => {
        if (apiResponse.success) {
            updateDashboard(apiResponse.data);
        } else {
            console.error("No data found.");
        }
    })
    .catch(error => console.error("Error fetching insights:", error));

    function updateDashboard(data) {
        // A. MOOD METER
        const score = data.current_score; 
        let percentage = score * 10; 
        
        let moodColor = "#f1c40f"; 
        let iconClass = "fas fa-meh";
        let tipText = "Staying balanced.";

        const moodText = document.getElementById("mood-text-display");
        const moodIcon = document.getElementById("main-mood-icon");
        const pointer = document.getElementById("mood-pointer");
        const pointerScore = document.getElementById("pointer-score");
        const tipBox = document.getElementById("daily-tip");

        if (score >= 7) {
            moodColor = "#2ecc71"; iconClass = "fas fa-smile-beam"; tipText = "Keep smiling!";
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#2ecc71'>Great!</span>";
        } 
        else if (score <= 4) {
            moodColor = "#3498db"; iconClass = "fas fa-cloud-rain"; tipText = "Take a break.";
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#3498db'>Down</span>";
        }
        else {
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#f1c40f'>Neutral</span>";
        }

        setTimeout(() => {
            if(pointer) pointer.style.left = percentage + "%";
            if(pointerScore) { pointerScore.innerText = percentage + "%"; pointerScore.style.background = moodColor; }
            if(moodIcon) { moodIcon.className = iconClass; moodIcon.style.color = moodColor; }
            if(tipBox) tipBox.innerText = "Tip: " + tipText;
        }, 500);

        // B. COUNTS
        if(document.getElementById("happy-count")) document.getElementById("happy-count").innerText = data.counts.Happy || 0;
        if(document.getElementById("sad-count")) document.getElementById("sad-count").innerText = data.counts.Sad || 0;
        if(document.getElementById("anxious-count")) document.getElementById("anxious-count").innerText = (data.counts.Anxious || 0) + (data.counts.Stressed || 0);

        // C. LINE CHART
        const ctx1 = document.getElementById('trendChart');
        if (ctx1) {
            new Chart(ctx1.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.trend_labels,
                    datasets: [{
                        label: 'Mood Score', data: data.trend_data,
                        borderColor: '#9b59b6', backgroundColor: 'rgba(155, 89, 182, 0.2)',
                        borderWidth: 3, fill: true, tension: 0.4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 10 } } }
            });
        }

        // D. PIE CHART
        const ctx2 = document.getElementById('pieChart');
        if (ctx2) {
            new Chart(ctx2.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Happy', 'Sad', 'Stress/Anxious', 'Neutral', 'Angry'],
                    datasets: [{
                        data: [
                            data.counts.Happy || 0, 
                            data.counts.Sad || 0, 
                            (data.counts.Anxious || 0) + (data.counts.Stressed || 0),
                            data.counts.Neutral || 0,
                            data.counts.Angry || 0
                        ],
                        backgroundColor: ['#2ecc71', '#3498db', '#9b59b6', '#95a5a6', '#e74c3c'],
                        borderWidth: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, cutout: '70%' }
            });
        }
    }
});