// Calendar JS for journal and goals pages
const currentDate = new Date();
let selectedDate = new Date();
const entryDays = window.entryDays || [];

function renderCalendar() {
    const monthYearDisplay = document.getElementById('monthYear');
    const daysContainer = document.querySelector('.days');
    if (!monthYearDisplay || !daysContainer) return;
    daysContainer.innerHTML = '';

    const month = selectedDate.getMonth();
    const year = selectedDate.getFullYear();
    monthYearDisplay.innerHTML = `${selectedDate.toLocaleString('default', { month: 'long' })} ${year}`;

    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const lastDateOfMonth = new Date(year, month + 1, 0).getDate();
    const adjustedFirstDay = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1;

    for (let i = 0; i < adjustedFirstDay; i++) {
        const emptyDay = document.createElement('div');
        daysContainer.appendChild(emptyDay);
    }
    for (let i = 1; i <= lastDateOfMonth; i++) {
        const dayElement = document.createElement('div');
        dayElement.innerHTML = i;
        dayElement.className = 'days li';
        if (i === currentDate.getDate() && month === currentDate.getMonth() && year === currentDate.getFullYear()) {
            dayElement.classList.add('current-day');
        }
        if (entryDays.includes(i)) {
            dayElement.classList.add('entry-day');
        }
        dayElement.onclick = () => selectDate(i);
        daysContainer.appendChild(dayElement);
    }
}
function selectDate(day) {
    selectedDate.setDate(day);
    const formattedDate = selectedDate.toISOString().split('T')[0];
    alert(`Selected date: ${formattedDate}`);
}
function prevMonth() {
    selectedDate.setMonth(selectedDate.getMonth() - 1);
    renderCalendar();
}
function nextMonth() {
    selectedDate.setMonth(selectedDate.getMonth() + 1);
    renderCalendar();
}
document.addEventListener('DOMContentLoaded', function() {
    renderCalendar();
});
