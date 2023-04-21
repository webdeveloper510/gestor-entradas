// Obtener todos los botones de entrada en la página
const entradaButtons = document.querySelectorAll('.entrada');

// Asignar un controlador de eventos de clic a cada botón
entradaButtons.forEach((button) => {
  button.addEventListener('click', () => {
    // Obtener el id del evento y el id de la entrada del atributo de datos
    const eventoId = button.getAttribute('data-evento-id');
    const entradaId = button.getAttribute('data-entrada-id');
    const restantes = button.getAttribute('data-restantes');

    // Si restantes es igual a 0, deshabilitar el botón y cambiar su estilo
      if (restantes === "0") {
        button.disabled = true;
        button.classList.add("agotada");
        button.innerText = "Agotada";
      }
    // Construir la URL de redirección
    const url = `direccion/evento/${eventoId}/${entradaId}`;

    // Redirigir a la nueva página
    window.location.href = url;
  });
