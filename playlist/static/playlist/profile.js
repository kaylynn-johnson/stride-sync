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
                    <div class="list-card">
                        <div class="list-card-header">
                            <div class="list-card-title-actionable">${escapeHtml(data.titles[i])} by ${escapeHtml(data.owners[i])} &ensp; <button class="remove btn btn-sm btn-outline-danger" data-playlist-id="${data.ids[i]}"><strong>Remove</strong></button></div>
                            <div><button class="btn btn-primary btn-sm view-playlist-btn">View Playlist</button></div>
                        </div>
                        <div class="list-card-meta">
                            ${Math.round(data.target_paces[i] * 10) / 10} min/mi | ${data.num_songs[i]} songs
                        </div>
                    </div>
                `;
            } else {
                playlistItem.innerHTML = `
                    <div class="list-card">
                        <div class="list-card-header">
                            <div class="list-card-title-actionable">${escapeHtml(data.titles[i])} by ${escapeHtml(data.owners[i])}</div>
                            <div><button class="btn btn-primary btn-sm view-playlist-btn">View Playlist</button></div>
                        </div>
                        <div class="list-card-meta">
                            ${Math.round(data.target_paces[i] * 10) / 10} min/mi | ${data.num_songs[i]} songs
                        </div>
                    </div>
                `;
            }
            playlistItem.querySelector(".view-playlist-btn").addEventListener("click", () => goToPlaylist(data.slugs[i]));
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

// Escape untrusted text before interpolating into innerHTML
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
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