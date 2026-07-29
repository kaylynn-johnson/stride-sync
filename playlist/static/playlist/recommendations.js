document.addEventListener("DOMContentLoaded", function() {
    const filterForm = document.querySelector("#recommendations-form");
    const songList = document.querySelector("#recommendations-results");
    const pagination = document.querySelector("#pagination");

    // fetch initial song list on page load
    const initialQueryString = new URLSearchParams(window.location.search).toString();
    fetch(`/api/songs/?${initialQueryString}`)
        .then(response => response.json())
        .then(data => {
            updateSongList(data);
            updatePagination(data);
            window.scrollTo({ top: document.querySelector('.body').offsetTop, behavior: 'smooth' });
        });

    filterForm.addEventListener("submit", function(event) {
        event.preventDefault();
        const formData = new FormData(filterForm);
        const queryString = new URLSearchParams(formData).toString();
        fetch(`/api/songs/?${queryString}`)
            .then(response => response.json())
            .then(data => {
                updateSongList(data);
                history.pushState(null, "", `?${queryString}`);
                updatePagination(data);
                window.scrollTo({ top: document.querySelector('#recommendations-results').offsetTop, behavior: 'smooth' });
            });
    });

    // Handle pagination clicks
    pagination.addEventListener("click", function(event) {
        if (event.target.tagName === "A") {
            event.preventDefault();
            const page = event.target.getAttribute("href").split("page=")[1];
            const formData = new FormData(filterForm);
            formData.set("page", page);
            const queryString = new URLSearchParams(formData).toString();
            fetch(`/api/songs/?${queryString}`)
                .then(response => response.json())
                .then(data => {
                    updateSongList(data);
                    history.pushState(null, "", `?${queryString}`);
                    updatePagination(data);
                    window.scrollTo({ top: document.querySelector('#recommendations-results').offsetTop, behavior: 'smooth' });
                });
        }
    }); 
});

function updateSongList(data) {
    const songList = document.querySelector("#recommendations-results");
    songList.innerHTML = "";
    data.recommended_songs.forEach(song => {
        const songItem = document.createElement("div");
        songItem.classList.add("song-item");
        songItem.innerHTML = `
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                <div style="font-weight: bold;">${song.title} by ${data.artists[song.id]}</div>
                <div style="font-size: 0.9em; color: #666;">
                    ${song.genre} | ${Math.round(song.pace * 10) / 10} min/mi | ${song.year}
                </div>
            </div>
        `;
        songList.appendChild(songItem);
    });
} 

function updatePagination(data) {
    const pagination = document.querySelector("#pagination");
    pagination.innerHTML = "";
    const firstPageLink = document.createElement("div");
    firstPageLink.innerHTML = `<a href="?page=1">&laquo;</a>`;
    pagination.appendChild(firstPageLink);
    for (let i = 1; i <= data.num_pages; i++) {
        const pageLink = document.createElement("div");
        pageLink.innerHTML = `<a href="?page=${i}">${i}</a>`;
        pagination.appendChild(pageLink);
    }
    const lastPageLink = document.createElement("div");
    lastPageLink.innerHTML = `<a href="?page=${data.num_pages}">&raquo;</a>`;
    pagination.appendChild(lastPageLink);
}