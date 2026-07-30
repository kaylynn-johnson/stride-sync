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
        console.log(song);
        const timeString = convertDuration(song.duration);
        const songItem = document.createElement("div");
        songItem.classList.add("song-item");
        songItem.innerHTML = `
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                <div style="font-weight: bold; display: flex; justify-content: space-between;">
                    <div style="content-align: center;">${song.title} by ${data.artists[song.id]} &ensp; <button class="btn btn-sm" id="add-${song.id}"><strong>+</strong></button></div>
                    <div><button id="more-info-${song.id}" class="btn btn-primary btn-sm">More info</button></div>
                </div>
                <div style="font-size: 0.9em; color: #666;">
                    ${song.genre} | ${Math.round(song.pace * 10) / 10} min/mi | ${song.year}
                </div>
            </div>
            <div id="modal-content-${song.id}" style="display: none;">
                <span class="close btn" id="close-${song.id}" style="padding-right: 10px;">&times;</span>
                <p><strong>${song.title}</strong> by ${data.artists[song.id]}</p>
                <ul>
                    <li><strong>Album:</strong> ${song.album}</li>
                    <li><strong>Year:</strong> ${song.year}</li>
                    <li><strong>Genre:</strong> ${song.genre}</li>
                    <li><strong>Popularity:</strong> ${song.popularity}/100</li>
                    <li><strong>Pace:</strong> ${Math.round(song.pace * 10) / 10} min/mi</li>
                    <li><strong>Duration:</strong> ${timeString}</li>
                </ul>
            </div>
            <div id="modal-add-${song.id}" style="display: none;">
                <span class="close btn" id="close-add-${song.id}" style="padding-right: 10px;">&times;</span>
                <p><strong>Playlists</strong></p>
                <ul id="playlists-${song.id}"></ul>
            </div>
        `;
        songList.appendChild(songItem);
        modalControl(song.id);
        addControl(song.id);
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

function convertDuration(ms) {
    const given_seconds = ms / 1000;
    let minutes = Math.floor((given_seconds) / 60);
    let seconds = Math.floor(given_seconds - (minutes * 60));
    let timeString =  minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
    console.log(`ms: ${ms}; given_seconds: ${given_seconds}; minutes: ${minutes}; seconds: ${seconds}`);
    return timeString;
}

function modalControl(song_id) {
    // Modified from https://www.w3schools.com/howto/howto_css_modals.asp
    // Get the modal
    let modal = document.querySelector(`#modal-content-${song_id}`);

    // Get the button that opens the modal
    let btn = document.querySelector(`#more-info-${song_id}`);

    // Get the <span> element that closes the modal
    let close = document.querySelector(`#close-${song_id}`);

    // When the user clicks the button, open the modal 
    btn.onclick = function() {
        modal.style.display = "block";
    }

    // When the user clicks on <span> (x), close the modal
    close.onclick = function() {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}

function addControl(song_id) {
    // Add the onclick event listener
    let addBtn = document.querySelector(`#add-${song_id}`);
    let addModal = document.querySelector(`#modal-add-${song_id}`);
    let addClose = document.querySelector(`#close-add-${song_id}`);

    addBtn.onclick = function() {
        // fetch the playlist for the logged in user
        console.log('Button clicked!');
        fetch(`/api/playlists/`)
            .then(request => request.json())
            .then(data => {
                const playlistList = document.querySelector(`#playlists-${song_id}`);
                playlistList.innerHTML = "";
                for (let i = 0; i < (data.titles).length; i++) {
                    playlistList.innerHTML += `
                        <li><a href="#">${data.titles[i]}<a> (${data.target_paces[i]} min/mi pace)</li>`
                }
                playlistList.innerHTML += '<li><a href="#">Add to new playlist</li>'
                addModal.style.display = "block";
            })
    }

    // When the user clicks on <span> (x), close the modal
    addClose.onclick = function() {
        addModal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == addModal) {
            addModal.style.display = "none";
        }
    }
}