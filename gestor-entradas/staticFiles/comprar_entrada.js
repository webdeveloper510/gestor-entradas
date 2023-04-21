// Selecciona el formulario y el botón de envío
const compraEntradasForm = document.getElementById('compra-entradas-form');
const comprarEntradasBtn = document.getElementById('comprar-entradas-btn');

// Agrega un controlador de eventos al botón de envío
comprarEntradasBtn.onclick = (event) => {
  // Detiene el envío predeterminado del formulario
  event.preventDefault();

  // Obtiene los datos del formulario
  const formData = new FormData(compraEntradasForm);

  // Realiza una solicitud POST al servidor
  fetch('/evento/{{ evento.id }}/{{ entrada.id }}', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    // Maneja la respuesta del servidor
    if (response.ok) {
      console.log('¡La compra fue exitosa!');
    } else {
      console.log('Error al comprar las entradas');
    }
  })
  .catch(error => console.error(error));
};
