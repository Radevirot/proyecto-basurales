// Variables globales
let zoomActivo = true;
const imagenes = document.querySelectorAll('.SizeBox1');
const modal = document.getElementById('zoomModal');
const zoomedImg = document.getElementById('zoomedImage');
let toggleZoomBtn = true;
const RadioCiclico = document.getElementById('Ciclico');
const RadioSi = document.getElementById('Si');
const RadioTalVez = document.getElementById('TalVez');
const RadioNo = document.getElementById('No');
const submitBtn = document.getElementById('submitBtn');

submitBtn.disabled = true; // inicio deshabilitado

//restaurar selección guardada
const savedRadio = localStorage.getItem('Radio1_selected');
if (savedRadio) {
    const radio = document.querySelector(`input[name="Radio1"][value="${savedRadio}"]`);
    if (radio) {
        radio.checked = true;
    }
} else {
    // si querés que por defecto sea Cíclico:
    RadioNo.checked = true;
}

// cuando el usuario cambia de radio, lo guardamos
const radios = document.querySelectorAll('input[name="Radio1"]');
radios.forEach(radio => {
    radio.addEventListener('change', () => {
        localStorage.setItem('Radio1_selected', radio.value);
    });
});

function actualizarEstadoSubmit() {
    const boxes = document.querySelectorAll('.Box');
  
    const todasEtiquetadas = Array.from(boxes).every(box => {
      const raw = box.dataset.etiqueta;
      // consideramos "etiquetada" si tiene algún valor definido o es distinto de -1
      return raw !== undefined && raw !== '' && raw !== '-1';
    });
  
    submitBtn.disabled = !todasEtiquetadas;
  }


// Para cada imagen
imagenes.forEach(img => {
    let colorIndex = 0;
    const colores = ['orange', 'gray', 'blue'];
    const valores = [1, 0.5, 0]; // Valores correspondientes a los colores

    img.addEventListener('click', function() {
        const box = this.parentElement.parentElement;
        let colorIndex = parseInt(box.getAttribute('data-color-index')) || 0;

        if(RadioCiclico.checked == true){
            // Modo cíclico
            colorIndex = (colorIndex + 1) % colores.length;
            box.style.borderColor = colores[colorIndex];
            box.setAttribute('data-etiqueta', valores[colorIndex]);
            box.setAttribute('data-color-index', colorIndex);
        }
        if(RadioSi.checked == true){
            box.style.borderColor = "orange";
            box.setAttribute('data-etiqueta', 1);
        }
        if(RadioTalVez.checked == true){
            box.style.borderColor = "gray";
            box.setAttribute('data-etiqueta', 0.5);
        }
        if(RadioNo.checked == true){
            box.style.borderColor = "blue";
            box.setAttribute('data-etiqueta', 0);
        }
        
        // Para verificar en consola
        console.log(`Imagen ${this.alt} - Valor: ${box.getAttribute('data-etiqueta')}`);

        actualizarEstadoSubmit();
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
}



submitBtn.addEventListener('click', async (e) => {
    e.preventDefault(); //evitamos el comportamiento normal del botón
    submitBtn.disabled = true; //deshabilitamos el botón

    const datos = [];

    document.querySelectorAll('.Box').forEach((box) => {
    const raw = box.dataset.etiqueta;
    const num = raw === undefined || raw === '' ? NaN : Number(raw);

    datos.push(Number.isFinite(num) ? num : -1);
    });

    //acá hacemos un fetch para mandarle los datos a flask
    //lo hacemos con manejo de errores

    try {
      const res = await fetch('/ia-basurales/enviar_etiquetas', {
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

  actualizarEstadoSubmit();