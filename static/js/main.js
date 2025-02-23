document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();
    
    let formData = new FormData(this);
    fetch("/generator/upload_csv/", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
            return;
        }
        alert(data.message || "New timetable generated");
        updateTimetable(data.timetable);
    })
    .catch(error => console.error("Error:", error));
});

function updateTimetable(timetableData) {
    let timetable = document.getElementById("timetableOutput");
    let rows = timetable.getElementsByTagName("tr");

    for (let i = 1; i < rows.length; i++) {
        let cells = rows[i].getElementsByTagName("td");
        for (let j = 0; j < cells.length; j++) {
            cells[j].innerHTML = "";
            cells[j].className = "";
        }
    }

    let colors = ["subject-1", "subject-2", "subject-3"];
    let colorIndex = {};

    for (let day in timetableData) {
        let columnIndex = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].indexOf(day) + 1;
        
        for (let time in timetableData[day]) {
            let rowIndex = parseInt(time) - 7;
            let cell = rows[rowIndex].cells[columnIndex];

            let courses = timetableData[day][time]; // ✅ Now courses is an array

            if (!Array.isArray(courses)) continue; // Ensure it is an array

            let content = "";
            courses.forEach((entry) => {
                let course = entry.course;
                let lecturer = entry.lecturer;
                let classroom = entry.classroom;

                if (!colorIndex[course]) {
                    colorIndex[course] = colors[Object.keys(colorIndex).length % colors.length];
                }

                content += `<div class="subject ${colorIndex[course]}">
                                <span class="subject-title">${course}</span><br>
                                <span>${lecturer}</span> <br>
                                <span>${classroom}</span>
                            </div>`;
            });

            cell.innerHTML = content;
        }
    }
}

