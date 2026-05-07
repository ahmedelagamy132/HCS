document.addEventListener("DOMContentLoaded", async () => {
    // Determine ID
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (!id) {
        document.getElementById('horse-name-display').innerHTML = `Missing <em>ID</em>`;
        return;
    }

    try {
        // Fetch all horses and find the matching one, since there isn't an explicit get single horse API
        const res = await fetch("/api/horses");
        if (!res.ok) throw new Error("Could not fetch horses.");
        const horses = await res.json();

        const horse = horses.find(h => String(h.id) === String(id));

        if (!horse) {
            document.getElementById('horse-name-display').innerHTML = `Horse <em>Not Found</em>`;
            return;
        }

        // Update UI
        document.getElementById("horse-id-display").innerText = horse.horse_code || ('HR-' + horse.id.substring(0,4).toUpperCase());
        document.getElementById("horse-name-display").innerHTML = `${horse.name || 'Unnamed'} <em>Live</em>`;

        document.getElementById("inf-breed").innerText = horse.breed || 'Unknown';
        document.getElementById("inf-age").innerText = horse.age_years !== null ? horse.age_years + ' yrs' : '-';
        document.getElementById("inf-stable").innerText = horse.stable_name || 'Unassigned';
        document.getElementById("inf-owner").innerText = horse.owner_name || 'N/A';
        document.getElementById("inf-health").innerText = horse.health_status || 'Unknown';

    } catch (err) {
        console.error(err);
        document.getElementById('horse-name-display').innerHTML = `Error <em>Loading</em>`;
    }

    // Streaming Logic Mock
    const connBtn = document.getElementById("connect-btn");
    const streamSys = document.getElementById("stream-sys");
    const vSpinner = document.getElementById("v-spinner");
    const vText = document.getElementById("v-text");
    const statusLbl = document.getElementById("conn-status-lbl");

    let isConnected = false;

    connBtn.addEventListener("click", () => {
        if (!isConnected) {
            // "Connect" flow
            vSpinner.style.display = "block";
            vText.innerText = "Buffering Stream...";
            connBtn.innerText = "Connecting...";
            connBtn.disabled = true;

            // Mock load time
            setTimeout(() => {
                isConnected = true;
                connBtn.disabled = false;
                connBtn.innerText = "Disconnect Stream";
                connBtn.style.background = "var(--danger)";
                
                streamSys.classList.remove("disconnected");
                statusLbl.innerText = "Live - 30 FPS";

                // Swap placeholder visually
                vSpinner.style.display = "none";
                vText.style.display = "none";

                // Insert a placeholder video
                const vp = document.getElementById("video-player");
                const oldVid = document.getElementById("mock-vid");
                if (!oldVid) {
                    const video = document.createElement("video");
                    video.id = "mock-vid";
                    video.src = "https://www.w3schools.com/html/mov_bbb.mp4"; // Just a sample video for mocking
                    video.style.width = "100%";
                    video.style.height = "100%";
                    video.style.objectFit = "cover";
                    video.style.position = "absolute";
                    video.style.inset = "0";
                    video.style.zIndex = "0";
                    video.autoplay = true;
                    video.loop = true;
                    video.muted = true;
                    vp.appendChild(video);
                }

            }, 1200);
        } else {
            // Disconnect flow
            isConnected = false;
            connBtn.innerText = "Connect Stream";
            connBtn.style.background = "var(--amber)";
            
            streamSys.classList.add("disconnected");
            statusLbl.innerText = "Disconnected";

            // Remove video
            vSpinner.style.display = "none";
            vText.style.display = "block";
            vText.innerText = "Awaiting Source";

            const oldVid = document.getElementById("mock-vid");
            if (oldVid) {
                oldVid.remove();
            }
        }
    });

});