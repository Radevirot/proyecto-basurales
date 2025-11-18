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
    const valores = [1, 0.5, 0]; // Valores correspondientes a los colores

    img.addEventListener('click', function() {
        const box = this.parentElement.parentElement;
        let colorIndex = parseInt(box.getAttribute('data-color-index')) || 0;

        if(CheckButton.checked == true){
            // Modo cíclico
            colorIndex = (colorIndex + 1) % colores.length;
            box.style.borderColor = colores[colorIndex];
            box.setAttribute('data-etiqueta', valores[colorIndex]);
            box.setAttribute('data-color-index', colorIndex);
        } else {
            // Modo con radios
            if(RadioSi.checked == true){
                box.style.borderColor = "green";
                box.setAttribute('data-etiqueta', 1);
            }
            if(RadioTalVez.checked == true){
                box.style.borderColor = "orange";
                box.setAttribute('data-etiqueta', 0.5);
            }
            if(RadioNo.checked == true){
                box.style.borderColor = "red";
                box.setAttribute('data-etiqueta', 0);
            }
        }
        
        // Para verificar en consola
        console.log(`Imagen ${this.alt} - Valor: ${box.getAttribute('data-etiqueta')}`);
    });


    /*img.addEventListener('click', function() {
        // Modo normal - cambiar color del borde
        if(CheckButton.checked == true){
            const box = this.parentElement.parentElement;
            box.style.borderColor = colores[colorIndex];
            if(colores[colorIndex] == "green"){
                ValorEtiqueta = 1;
            }
            if(colores[colorIndex] == "orange"){
                ValorEtiqueta = 0.5;
            }
            if(colores[colorIndex] == "red"){
                ValorEtiqueta = 0;
            }
            colorIndex = (colorIndex + 1) % colores.length;
        }else{
            if(RadioSi.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "green"
                ValorEtiqueta = 1;
            }
            if(RadioTalVez.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "orange"
                ValorEtiqueta = 0.5;
            }
            if(RadioNo.checked == true){
                const box = this.parentElement.parentElement;
                box.style.borderColor = "red"
                ValorEtiqueta = 0;
            }
        }
        console.log(ValorEtiqueta);
    });*/

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



submitBtn.addEventListener('click', async (e) => {
    e.preventDefault(); //evitamos el comportamiento normal del botón
    submitBtn.disabled = true; //deshabilitamos el botón
    
    //versión lista [1, 0.5...]

    const datos = [];

    document.querySelectorAll('.Box').forEach((box) => {
    const raw = box.dataset.etiqueta;
    const num = raw === undefined || raw === '' ? NaN : Number(raw);

    datos.push(Number.isFinite(num) ? num : -1);
    });

    //acá hacemos un fetch para mandarle los datos a flask
    //lo hacemos con manejo de errores

    try {
      const res = await fetch('/enviar_etiquetas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
      });
  
      if (!res.ok) throw new Error(`El servidor respondió ${res.status}`);

  
      window.location.reload();  // recargamos la página
      
    } catch (err) {
      console.error('error de enviar_etiquetas:', err);
      
      alert('Error al subir las etiquetas, revise la consola para más información.');
    } finally {
      submitBtn.disabled = false;
    }
  });