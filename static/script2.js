document.addEventListener("DOMContentLoaded", function() {
    console.log("Insight Script Loaded...");

    // 🔥 Flask route /insight_api se data fetch ho raha hai
    fetch('/insight_api')
    .then(response => response.json())
    .then(apiResponse => {
        if (apiResponse.success) {
            console.log("Data Received:", apiResponse.data);
            updateDashboard(apiResponse.data);
        } else {
            console.error("No data found:", apiResponse.message);
            const tipBox = document.getElementById("daily-tip");
            if(tipBox) tipBox.innerText = "Start chatting with Zen AI to see your emotional journey!";
        }
    })
    .catch(error => console.error("Error fetching insights:", error));

    function updateDashboard(data) {
        // --- A. MOOD METER LOGIC ---
        const score = data.current_score; 
        let percentage = score * 10; // 0-10 score converts to 0-100%
        
        let moodColor = "#f1c40f"; 
        let iconClass = "fas fa-meh";
        let tipText = "Staying balanced.";

        const moodText = document.getElementById("mood-text-display");
        const moodIcon = document.getElementById("main-mood-icon");
        const pointer = document.getElementById("mood-pointer");
        const pointerScore = document.getElementById("pointer-score");
        const tipBox = document.getElementById("daily-tip");

        // UI Updates based on Mood Score
        if (score >= 7) {
            moodColor = "#2ecc71"; iconClass = "fas fa-smile-beam"; tipText = "You're doing great! Keep up the positive energy.";
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#2ecc71'>Great!</span>";
        } 
        else if (score <= 4) {
            moodColor = "#3498db"; iconClass = "fas fa-cloud-rain"; tipText = "It's okay to feel down. Try a breathing exercise.";
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#3498db'>Down</span>";
        }
        else {
            if(moodText) moodText.innerHTML = "Feeling <span style='color:#f1c40f'>Neutral</span>";
        }

        // Pointer Animation
        setTimeout(() => {
            if(pointer) pointer.style.left = percentage + "%";
            if(pointerScore) { 
                pointerScore.innerText = percentage + "%"; 
                pointerScore.style.background = moodColor; 
            }
            if(moodIcon) { 
                moodIcon.className = iconClass; 
                moodIcon.style.color = moodColor; 
            }
            if(tipBox) tipBox.innerText = "Insight: " + tipText;
        }, 500);

        // --- B. STAT CARDS COUNTS ---
        if(document.getElementById("happy-count")) 
            document.getElementById("happy-count").innerText = data.counts.Happy || 0;
        
        if(document.getElementById("sad-count")) 
            document.getElementById("sad-count").innerText = data.counts.Sad || 0;
        
        if(document.getElementById("anxious-count")) 
            document.getElementById("anxious-count").innerText = (data.counts.Anxious || 0) + (data.counts.Stressed || 0);

        // --- C. TREND LINE CHART ---
        const ctx1 = document.getElementById('trendChart');
        if (ctx1) {
            new Chart(ctx1.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.trend_labels,
                    datasets: [{
                        label: 'Mood Level', 
                        data: data.trend_data,
                        borderColor: '#9b59b6', 
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        borderWidth: 3, 
                        fill: true, 
                        tension: 0.4,
                        pointBackgroundColor: '#fff',
                        pointBorderColor: '#9b59b6',
                        pointRadius: 5
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: { legend: { display: false } },
                    scales: { 
                        y: { beginAtZero: true, max: 10, ticks: { stepSize: 2 } },
                        x: { grid: { display: false } }
                    } 
                }
            });
        }

        // --- D. DISTRIBUTION PIE CHART ---
        const ctx2 = document.getElementById('pieChart');
        if (ctx2) {
            new Chart(ctx2.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Happy', 'Sad', 'Anxious/Stress', 'Neutral', 'Angry'],
                    datasets: [{
                        data: [
                            data.counts.Happy || 0, 
                            data.counts.Sad || 0, 
                            (data.counts.Anxious || 0) + (data.counts.Stressed || 0),
                            data.counts.Neutral || 0,
                            data.counts.Angry || 0
                        ],
                        backgroundColor: ['#2ecc71', '#3498db', '#9b59b6', '#95a5a6', '#e74c3c'],
                        hoverOffset: 10,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    cutout: '70%',
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12, padding: 15 } }
                    }
                }
            });
        }
    }
});