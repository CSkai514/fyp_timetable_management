
function updateTimetable(timetableData) {
    let timetable = document.getElementById("timetableOutput");
    let rows = timetable.getElementsByTagName("tr");

    // Clear previous timetable entries
    for (let i = 1; i < rows.length; i++) {
        let cells = rows[i].getElementsByTagName("td");
        for (let j = 0; j < cells.length; j++) {
            cells[j].innerHTML = "";
            cells[j].className = "";
        }
    }

    let colors = ["subject-1", "subject-2", "subject-3"];
    let colorIndex = {};
    let timeSlots = {
        8: 1, 9: 2, 10: 3, 11: 4, 12: 5,
        13: 6, 14: 7, 15: 8, 16: 9, 17: 10
    };

    for (let day in timetableData) {
        let columnIndex = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].indexOf(day) + 1;
        
        for (let time in timetableData[day]) {
            if (!timeSlots[time]) continue;  // Skip invalid time keys
            
            let rowIndex = timeSlots[parseInt(time)];  // Map time to row index
            
            if (!rows[rowIndex]) continue;  // Ensure row exists
            let cell = rows[rowIndex].cells[columnIndex];

            let courses = timetableData[day][time];

            if (!Array.isArray(courses)) continue;

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

