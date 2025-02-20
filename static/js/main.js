document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".upload-form");
    const fileInput = document.querySelector(".timetable-upload");
    const timetableTable = document.querySelector(".timetable");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append("timetable", fileInput.files[0]);

        fetch("/generator/generate_timetable/", {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }
            
            updateTimetable(data.timetable);
        })
        .catch(error => console.error("Error:", error));
    });

    function updateTimetable(timetable) {
        // Clear existing timetable (except headers)
        const rows = timetableTable.querySelectorAll("tr:not(.first-row)");
        rows.forEach(row => {
            const cells = row.querySelectorAll("td");
            cells.forEach(cell => cell.innerHTML = "");
        });

        // Populate timetable with new data
        for (const [hour, days] of Object.entries(timetable)) {
            for (const [day, session] of Object.entries(days)) {
                if (session) {
                    const dayIndex = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].indexOf(day) + 1;
                    const rowIndex = parseInt(hour) - 8 + 1; // Adjust for row positioning

                    const cell = timetableTable.rows[rowIndex].cells[dayIndex];
                    cell.classList.add("subject", `subject-${(rowIndex % 3) + 1}`);
                    cell.innerHTML = `
                        <span class="subject-title">${session.course}</span><br>
                        ${session.lecturer}<br>
                        ${session.classroom}
                    `;
                }
            }
        }
    }
});
