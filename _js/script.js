const searchInput = document.getElementById('searchInput');
const filtros = document.querySelectorAll('input');
const cards = document.querySelectorAll('.card');

function filtrar() {
    const valor = document.querySelector('input[name="valor"]:checked')?.value;
    const tipos = Array.from(document.querySelectorAll('input[name="tipo"]:checked')).map(e => e.value);
    const quartos = Array.from(document.querySelectorAll('input[name="quartos"]:checked')).map(e => e.value);
    const extras = Array.from(document.querySelectorAll('input[name="extras"]:checked')).map(e => e.value);
    const search = searchInput.value.toLowerCase();

    cards.forEach(card => {
        let show = true;

        const cardValor = parseInt(card.dataset.valor);
        const cardTipo = card.dataset.tipo;
        const cardQuartos = parseInt(card.dataset.quartos);
        const cardExtras = card.dataset.extras.split(',');
        const cardEndereco = card.dataset.endereco.toLowerCase();

        if (valor && valor !== 'todos') {
            if (valor === '500' && cardValor > 500) show = false;
            if (valor === '1000' && (cardValor <= 500 || cardValor > 1000)) show = false;
            if (valor === 'acima' && cardValor <= 1000) show = false;
        }

        if (tipos.length && !tipos.includes(cardTipo)) show = false;

        if (quartos.length && !quartos.includes(cardQuartos >= 3 ? '3' : String(cardQuartos))) show = false;

        if (extras.length && !extras.every(extra => cardExtras.includes(extra))) show = false;

        if (search && !cardEndereco.includes(search)) show = false;

        card.style.display = show ? 'block' : 'none';
    });
}

filtros.forEach(input => {
    input.addEventListener('input', filtrar);
});

searchInput.addEventListener('input', filtrar);

// Inicializa tudo mostrando
filtrar();
