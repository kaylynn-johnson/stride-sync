document.addEventListener("DOMContentLoaded", function() {
    const songList = document.querySelector("#user-playlists");
    const username = document.querySelector('meta[name="username"]').content;
    const url_pieces = window.location.href.split('/[?#]/')[0].split('/').filter(segment => segment !== '');
    const target_username = url_pieces[url_pieces.length - 1];
    console.log(target_username);

    // Load playlists
    fetch(`/api/profile/?username=${target_username}`)
    .then(request => request.json())
    .then(data => {
        const playlistDiv = document.querySelector('#all-playlists');
        if (data.titles.length === 0) {
            // no playlists to show
            const playlistInfo = document.createElement('h3');
            if (target_username === username) {
                // Viewing own profile
                playlistInfo.innerHTML = 'No playlists yet!';
            } else {
                // Viewing other's profile
                playlistInfo.innerHTML = "User doesn't have any public playlists!";
            }
            playlistInfo.style.textAlign = 'center';
            playlistDiv.appendChild(playlistInfo);
        }
        for (let i = 0; i < (data.titles).length; i++) {
            const playlistItem = document.createElement('div');
            playlistItem.classList.add('playlist-item');
            playlistItem.id = `playlist-${data.ids[i]}`;
            console.log(`Owner: ${data.owners[i]}`);
            console.log(`Logged in user: ${username}`);
            if (data.owners[i] === username) {
                playlistItem.innerHTML = `
                    <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                        <div style="font-weight: bold; display: flex; justify-content: space-between;">
                            <div style="align-content: center; max-width: 70%;">${data.titles[i]} by ${data.owners[i]} &ensp; <button class="remove btn btn-sm btn-outline-danger" data-playlist-id="${data.ids[i]}"><strong>Remove</strong></button></div>
                            <div><button class="btn btn-primary btn-sm" onclick="goToPlaylist('${data.slugs[i]}')">View Playlist</button></div>
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            ${Math.round(data.target_paces[i] * 10) / 10} min/mi | ${data.num_songs[i]} songs
                        </div>
                    </div>
                `;
            } else {
                playlistItem.innerHTML = `
                    <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                        <div style="font-weight: bold; display: flex; justify-content: space-between;">
                            <div style="align-content: center;">${data.titles[i]} by ${data.owners[i]}</div>
                            <div><button class="btn btn-primary btn-sm" onclick="goToPlaylist('${data.slugs[i]}')">View Playlist</button></div>
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            ${Math.round(data.target_paces[i] * 10) / 10} min/mi | ${data.num_songs[i]} songs
                        </div>
                    </div>
                `;
            }
            playlistDiv.appendChild(playlistItem);
        }
        addRemoveAction();
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

function goToPlaylist(slug) {
    window.location.href = `/playlists/${slug}`;
}

function addRemoveAction() {
    document.querySelectorAll(".remove").forEach((button) => {
        button.onclick = () => {
            console.log('Remove button clicked!');
            const playlistId = button.dataset.playlistId;
            fetch(`/api/playlists/`, {
                method: "PUT",
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    playlist_id: playlistId,
                    remove: true
                })
            })
            .then(request => request.json())
            .then(result => {
                if (result.error !== undefined) {
                    // Error
                    alert(`Could not remove playlist. Error: ${result.error}`);
                } else {
                    alert(`Successfully removed playlist!`);
                    // remove the song-info-{{ song.id }} div element
                    document.querySelector(`#playlist-${playlistId}`).remove();
                    window.scrollTo({ top: document.querySelector('#all-playlists').offsetTop, behavior: 'smooth' });
                }
            })
        }
    });
}