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
                <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                    <div style="font-weight: bold; display: flex; justify-content: space-between;">
                        <div style="align-content: center; max-width: 70%">${data.titles[i]} by ${data.owners[i]}</div>
                        <div><button class="btn btn-primary btn-sm" onclick="goToPlaylist('${data.slugs[i]}')">View Playlist</button></div>
                    </div>
                    <div style="font-size: 0.9em; color: #666;">
                        ${Math.round(data.target_paces[i] * 10) / 10} min/mi | ${data.num_songs[i]} songs
                    </div>
                </div>
            `;
            playlistDiv.appendChild(playlistItem);
        }
    });
});

function goToPlaylist(slug) {
    window.location.href = `/playlists/${slug}`;
}
