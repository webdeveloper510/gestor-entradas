const eventos = document.querySelectorAll('.evento');
eventos.forEach(evento => {
    evento.addEventListener('click', () => {
        const id = evento.dataset.id;
        let url = `/evento/${id}`;
        if ({{ rrpp }} !== null) {
            url += `?rrpp=${{ rrpp.id }}`;
        }
        console.log(`El evento seleccionado tiene el id ${id}`);
        // Aquí puedes hacer la petición para obtener más información del evento con el id selecc>
        window.location.href = url;
    });
});

