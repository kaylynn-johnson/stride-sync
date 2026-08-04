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
                if (queryString.includes('page')) {
                    // page already included
                    history.pushState(null, "", `?${queryString}`);
                } else {
                    history.pushState(null, "", `?${queryString}&page=1`);
                }
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

// Fetch CSRF Token from meta tag in header
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        // Successfully found tag
        return metaTag.content;
    }
    throw new Error('CSRF token meta tag not found');
}

function updateSongList(data) {
    const songList = document.querySelector("#recommendations-results");
    songList.innerHTML = "";
    data.recommended_songs.forEach(song => {
        console.log(song);
        const timeString = convertDuration(song.duration);
        const songItem = document.createElement("div");
        songItem.classList.add("song-item");
        songItem.id = `song-${song.id}`;
        songItem.innerHTML = `
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                <div style="font-weight: bold; display: flex; justify-content: space-between;">
                    <div style="align-content: center; max-width: 70%;">${song.title} by ${data.artists[song.id]} &ensp; <button class="btn btn-sm btn-outline-success" id="add-${song.id}"><strong>Add</strong></button></div>
                    <div><button id="more-info-${song.id}" class="btn btn-primary btn-sm">More info</button></div>
                </div>
                <div style="font-size: 0.9em; color: #666;">
                    ${song.genre} | ${Math.round(song.pace * 10) / 10} min/mi | ${song.year}
                </div>
            </div>
            <div id="modal-content-${song.id}" style="display: none; margin-left: 10px;">
                <span class="close btn" id="close-${song.id}" style="padding-right: 10px;">&times;</span>
                <p><strong>${song.title}</strong> by ${data.artists[song.id]}</p>
                <ul>
                    <li><strong>Album:</strong> ${song.album}</li>
                    <li><strong>Year:</strong> ${song.year}</li>
                    <li><strong>Genre:</strong> ${song.genre}</li>
                    <li><strong>Popularity:</strong> ${song.popularity}/100</li>
                    <li><strong>Pace:</strong> <span id="pace-${song.id}">${Math.round(song.pace * 10) / 10}</span> min/mi</li>
                    <li><strong>Duration:</strong> ${timeString}</li>
                </ul>
            </div>
            <div id="modal-add-${song.id}" style="display: none; margin-left: 10px">
                <span class="close btn" id="close-add-${song.id}" style="padding-right: 10px;">&times;</span>
                <p><strong>Playlists</strong></p>
                <ul id="playlists-${song.id}"></ul>
            </div>
            <div class="form-popup" id="new-playlist-${song.id}" style="display: none;">
                <form class="form-container" id="playlist-form-${song.id}" style="margin-left: 10px; margin-bottom: 10px;">
                    <h1 style="text-align: left;">Create Playlist</h1>
                    <label for="name"><b>Name</b> <input type="text" placeholder="Enter Playlist Name" name="name" id="playlist-name-${song.id}" required></label>
                    <label for="pace"><b>Target Pace</b> <input type="number" name="pace" value="${Math.round(song.pace * 10) / 10}" id="playlist-pace-${song.id}" disabled></label>
                    <div>
                        <button type="submit" class="btn btn-outline-secondary" style="margin-right: 10px;">Create</button>
                        <button type="button" class="btn btn-outline-secondary cancel" onclick="closeForm('new-playlist-${song.id}')">Close</button>
                    </div>
                </form>
            </div>
        `;
        songList.appendChild(songItem);
        modalControl(song.id);
        addControl(song.id);
        createPlaylist(song.id);
    });
} 

function updatePagination(data) {
    const pagination = document.querySelector("#pagination");
    pagination.innerHTML = "";
    const firstPageLink = document.createElement("div");
    const initialQueryString = new URLSearchParams(window.location.search).toString().split("&page=")[0];
    firstPageLink.innerHTML = `<a href="?${initialQueryString}&page=1"><i class="fa-regular fa-backward"></i></a>`;
    firstPageLink.style.fontSize = '20px';
    pagination.appendChild(firstPageLink);
    for (let i = 1; i <= data.num_pages; i++) {
        const pageLink = document.createElement("div");
        pageLink.innerHTML = `<a href="?${initialQueryString}&page=${i}"><i class="fa-regular fa-square-${i}"></i></a>`;
        pageLink.style.fontSize = '20px';
        pagination.appendChild(pageLink);
    }
    const lastPageLink = document.createElement("div");
    lastPageLink.innerHTML = `<a href="?${initialQueryString}&page=${data.num_pages}"><i class="fa-regular fa-forward"></i></a>`;
    lastPageLink.style.fontSize = '20px';
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
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }
}

function addControl(song_id) {
    // Add the onclick event listener
    let addBtn = document.querySelector(`#add-${song_id}`);
    let addModal = document.querySelector(`#modal-add-${song_id}`);
    let addClose = document.querySelector(`#close-add-${song_id}`);
    const username = document.querySelector('meta[name="username"]').content;

    addBtn.onclick = function() {
        // fetch the playlist for the logged in user
        console.log('Button clicked!');
        if (addModal.style.display === "none") {
            // user has not yet hit the add button
            // Call profile api to get user's playlists instead of public playlists
            fetch(`/api/profile/?username=${username}`)
            .then(request => request.json())
            .then(data => {
                const playlistList = document.querySelector(`#playlists-${song_id}`);
                playlistList.innerHTML = "";
                for (let i = 0; i < (data.titles).length; i++) {
                    playlistList.innerHTML += `
                        <li><a href="#song-${song_id}" onclick="addSongControl(${song_id},'${data.titles[i]}',${data.target_paces[i]})">${data.titles[i]}<a> (${data.target_paces[i]} min/mi pace)</li>`;
                }
                playlistList.innerHTML += `<li><a href="#song-${song_id}" onclick="openForm('new-playlist-${song_id}')">Add to new playlist</li>`;
                addModal.style.display = "block";
            })
        }
        
    }

    // When the user clicks on <span> (x), close the modal
    addClose.addEventListener ("click", function() {
        console.log('Clicking close');
        addModal.style.display = "none";
    });
}

function openForm(element_id) {
    document.querySelector(`#${element_id}`).style.display = 'block';
    window.scrollTo({ top: document.querySelector(`#${element_id}`).offsetTop, behavior: 'smooth' });
}

function closeForm(element_id) {
    document.querySelector(`#${element_id}`).style.display = 'none';
    // Assume the last bit is the song ID
    const song_id = element_id.split("-").at(-1);
    console.log(song_id);
    window.scrollTo({ top: document.querySelector(`#song-${song_id}`).offsetTop, behavior: 'smooth' });
}

function createPlaylist(song_id) {
    const playlistForm = document.querySelector(`#playlist-form-${song_id}`);

    playlistForm.addEventListener("submit", function(event) {
        event.preventDefault();
        const playlistName = document.querySelector(`#playlist-name-${song_id}`).value;
        const playlistPace = document.querySelector(`#playlist-pace-${song_id}`).value;

        console.log(`Adding ${playlistName} playlist at ${playlistPace} min/mi pace`);

        fetch(`/api/playlists/`, {
            method: "POST",
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                name: playlistName,
                pace: playlistPace,
                song_id: song_id
            })
        })
        .then(request => request.json())
        .then(result => {
            // should get a success
            console.log(result);
            if (result.error !== undefined) {
                // error
                alert(`Could not create ${playlistName} playlist. Error: ${result.error}`);
            } else {
                alert(`${playlistName} playlist successfully created!`);
                document.querySelector(`#new-playlist-${song_id}`).style.display = 'none';
                window.scrollTo({ top: document.querySelector(`#song-${song_id}`).offsetTop, behavior: 'smooth' });
            }
        })
    })
}

function addSong(song_id, playlist_name) {
    // API call to add song to playlist
    fetch(`/api/playlists/songs/`, {
        method: "POST",
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            playlist_name: playlist_name,
            song_id: song_id,
            add: true
        })
    })
    .then(request => request.json())
    .then(result => {
        if (result.error !== undefined) {
            // Error
            alert(`Could not add song to ${playlist_name}. Error: ${result.error}`);
        } else {
            alert(`Song successfully added to ${playlist_name}!`);
        }
    })
}

function addSongControl(song_id, playlist_name, target_pace) {
    // Find pace of song
    const song_pace = parseFloat(document.querySelector(`#pace-${song_id}`).innerHTML);
    if (Math.abs(song_pace - target_pace) > 1) {
        // Alert that the song is outside +/- 1min of playlist target pace
        const song_div = document.querySelector(`#song-${song_id}`);
        //const song_warning = document.createElement('div');
        // Add modal to warn user of mis-match pace and allow to override
        song_div.innerHTML += `
            <div class="form-popup" id="warning-playlist-${song_id}" style="display: block; margin: 10px">
                <form class="form-container" id="warning-form-${song_id}">
                    <h1 style="text-align: left;">WARNING</h1>

                    <div>The song you are trying to add is more than 1 minute outside the target pace of the playlist.</div>

                    <div><strong>Would you still like to add it?</strong></div> 

                    <button type="submit" class="btn btn-danger" style="margin-right: 10px;">Add Anyways</button>
                    <button type="button" class="btn btn-outline-primary" style="margin-right: 10px;" onclick="closeForm('warning-playlist-${song_id}')">No</button>
                    <button type="button" class="btn btn-outline-secondary cancel" onclick="closeForm('warning-playlist-${song_id}')">Close</button>
                </form>
            </div>
        `;
        //song_div.appendChild(song_warning);

        // add onsubmit action to Add Anyways
        document.querySelector(`#warning-form-${song_id}`).addEventListener("submit", function(event) {
            event.preventDefault();
            // No fields to find
            // Call add song
            addSong(song_id, playlist_name);
            document.querySelector(`#warning-playlist-${song_id}`).style.display = "none";
            window.scrollTo({ top: document.querySelector(`#song-${song_id}`).offsetTop, behavior: 'smooth' });
        });

    } else {
        // Pacing of song matches up so add it
        addSong(song_id, playlist_name);
        window.scrollTo({ top: document.querySelector(`#song-${song_id}`).offsetTop, behavior: 'smooth' });
    }
}