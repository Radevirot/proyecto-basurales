// Variables globales
let zoomActivo = true;
const imagenes = document.querySelectorAll('.SizeBox1');
const modal = document.getElementById('zoomModal');
const zoomedImg = document.getElementById('zoomedImage');
const toggleZoomBtn = document.getElementById('toggleZoom');
const CheckButton = document.getElementById('Check');
const RadioSi = document.getElementById('Si');
const RadioTalVez = document.getElementById('TalVez');
const RadioNo = document.getElementById('No');

CheckButton.checked = true;

// Función para activar/desactivar el modo zoom
toggleZoomBtn.addEventListener('click', function() {
    zoomActivo = !zoomActivo;
    this.textContent = zoomActivo ? 'Desactivar Lupa' : 'Activar Lupa';
});

if(CheckButton.checked == true){
    RadioSi.checked = false;
    RadioTalVez.checked = false;
    RadioNo.checked = false;
}

// Para cada imagen
imagenes.forEach(img => {
    let colorIndex = 0;
    const colores = ['green', 'orange', 'red'];

    img.addEventListener('click', function() {
        // Modo normal - cambiar color del borde
        if(CheckButton.checked == true){
            const box = this.parentElement.parentElement;
            box.style.borderColor = colores[colorIndex];
            colorIndex = (colorIndex + 1) % colores.length;
        }else{
            if(RadioSi.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "green"
            }
            if(RadioTalVez.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "orange"
            }
            if(RadioNo.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "red"
            }
        }
    });

    img.addEventListener('mousemove', function() {
        if (zoomActivo) {
            // Modo zoom activado - mostrar imagen en modal
            zoomedImg.src = this.src;
            modal.style.display = "block";
        }
    });
});

// Cerrar modal al hacer clic fuera de la imagen
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
    if(CheckButton.checked == true){
        RadioSi.checked = false;
        RadioTalVez.checked = false;
        RadioNo.checked = false;
    }
}