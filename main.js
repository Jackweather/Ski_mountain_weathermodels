document.getElementById('showGoreBtn').addEventListener('click', function() {
    fetch('/HRRR/Gore/output/list_pngs')
        .then(response => response.json())
        .then(images => {
            const container = document.getElementById('goreImages');
            container.innerHTML = images.map(img =>
                `<img src="/HRRR/Gore/output/${img}" alt="${img}" class="fullscreenable">`
            ).join('');
            container.style.display = 'grid';
            // Add fullscreen click event to each image
            document.querySelectorAll('.fullscreenable').forEach(img => {
                img.addEventListener('click', function() {
                    if (img.requestFullscreen) {
                        img.requestFullscreen();
                    } else if (img.webkitRequestFullscreen) { /* Safari */
                        img.webkitRequestFullscreen();
                    } else if (img.msRequestFullscreen) { /* IE11 */
                        img.msRequestFullscreen();
                    }
                });
            });
        });
});
