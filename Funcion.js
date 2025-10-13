// Variables globales
let zoomActivo = false;
const imagenes = document.querySelectorAll('.SizeBox1');
const modal = document.getElementById('zoomModal');
const zoomedImg = document.getElementById('zoomedImage');
const spanCerrar = document.getElementsByClassName('close')[0];
const toggleZoomBtn = document.getElementById('toggleZoom');

// Función para activar/desactivar el modo zoom
toggleZoomBtn.addEventListener('click', function() {
    zoomActivo = !zoomActivo;
    this.textContent = zoomActivo ? 'Desactivar Lupa' : 'Activar Lupa';
});

// Para cada imagen
imagenes.forEach(img => {
    let colorIndex = 0;
    const colores = ['green', 'orange', 'red'];
    
    img.addEventListener('click', function() {
        if (zoomActivo) {
            // Modo zoom activado - mostrar imagen en modal
            zoomedImg.src = this.src;
            modal.style.display = "block";
        } else {
            // Modo normal - cambiar color del borde
            const box = this.parentElement.parentElement;
            box.style.borderColor = colores[colorIndex];
            colorIndex = (colorIndex + 1) % colores.length;
        }
    });
});

// Cerrar modal
spanCerrar.onclick = function() {
    modal.style.display = "none";
}

// Cerrar modal al hacer clic fuera de la imagen
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}