document.addEventListener("DOMContentLoaded", function() {
    const songList = document.querySelector("#user-playlists");
    const pagination = document.querySelector("#pagination");
    const username = document.querySelector('meta[name="username"]').content;

    // Load playlists
    fetch('/api/playlists')
    .then(request => request.json())
    .then(data => {
        console.log(data);
        const playlistDiv = document.querySelector('#all-playlists');
        console.log(data.titles.length);
        if (data.titles.length === 0) {
            // no playlists to show
            const playlistInfo = document.createElement('h3');
            playlistInfo.innerHTML = 'No public playlists yet!';
            playlistInfo.style.textAlign = 'center';
            playlistDiv.appendChild(playlistInfo);
        }
        for (let i = 0; i < (data.titles).length; i++) {
            const playlistItem = document.createElement('div');
            playlistItem.classList.add('playlist-item');
            playlistItem.id = `playlist-${data.ids[i]}`;
            console.log(`Owner: ${data.owners[i]}`);
            console.log(`Logged in user: ${username}`);
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
            playlistItem.querySelector(".view-playlist-btn").addEventListener("click", () => goToPlaylist(data.slugs[i]));
            playlistDiv.appendChild(playlistItem);
        }
    });
});

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
