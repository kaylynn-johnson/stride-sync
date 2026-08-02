document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to either make public or private button if they exist
    const public = document.querySelector("#make-public");
    const private = document.querySelector("#make-private");

    if (public) {
        // the make public button exists
        public.onclick = () => {
            fetch(`/api/playlists/`, {
                method: "PUT",
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    playlist_id: public.dataset.playlistId,
                    public: true
                })
            })
            .then(request => request.json())
            .then(result => {
                if (result.error !== undefined) {
                    // Error
                    alert(`Could not make this playlist public`);
                } else {
                    alert(`Playlist was made public`);
                    public.innerHTML = 'Make Private';
                    public.id = 'make-private';
                    public.classList = 'btn btn-outline-danger';
                }
            })
        }
    } else if (private) {
        // the make public button exists
        private.onclick = () => {
            fetch(`/api/playlists/`, {
                method: "PUT",
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    playlist_id: private.dataset.playlistId,
                    public: false
                })
            })
            .then(request => request.json())
            .then(result => {
                if (result.error !== undefined) {
                    // Error
                    alert(`Could not make this playlist private`);
                } else {
                    alert(`Playlist was made private`);
                    private.innerHTML = 'Make Public';
                    private.id = 'make-public';
                    private.classList = 'btn btn-outline-success';
                }
            })
        }
    }

    // Add event listener to copy playlist link to clipboard
    document.querySelector(".copy").onclick = (button) => {
        alert(`Shareable link is: \n${window.location.href}`);
    }

    // Add event listeners for more info and close buttons
    document.querySelectorAll(".more-info").forEach((button) => {
        button.onclick = () => {
            console.log(button);
            console.log(this);
            const song_id = button.dataset.songId;
            console.log(song_id);
            document.querySelector(`#modal-content-${song_id}`).style.display = 'block';
            window.scrollTo({ top: document.querySelector(`#modal-content-${song_id}`).offsetTop, behavior: 'smooth' });
        }
    })

    document.querySelectorAll(".close").forEach((button) => {
        button.onclick = () => {
            const songID = button.dataset.songId;
            document.querySelector(`#modal-content-${songID}`).style.display = 'none';
            window.scrollTo({ top: document.querySelector(`#song-info-${songID}`).offsetTop, behavior: 'smooth'});
        }
    })

    // Add event listeners to each song remove button
    document.querySelectorAll(".remove").forEach((button) => {
        button.onclick = () => {
            const songID = button.dataset.songId;
            const playlistName = button.dataset.playlistName;
            fetch(`/api/playlists/songs/`, {
                method: "POST",
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    playlist_name: playlistName,
                    song_id: songID,
                    add: false
                })
            })
            .then(request => request.json())
            .then(result => {
                if (result.error !== undefined) {
                    // Error
                    alert(`Could not remove song from ${playlistName}. Error: ${result.error}`);
                } else {
                    alert(`Song successfully removed from ${playlistName}!`);
                    // remove the song-info-{{ song.id }} div element
                    document.querySelector(`#song-info-${songID}`).remove();
                    window.scrollTo({ top: document.querySelector('.header').offsetTop, behavior: 'smooth' });
                }
            })
        }
    })
})

// Fetch CSRF Token from meta tag in header
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        // Successfully found tag
        return metaTag.content;
    }
    throw new Error('CSRF token meta tag not found');
}