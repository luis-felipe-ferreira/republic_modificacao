
document.addEventListener("DOMContentLoaded", function () {
    const celularInput = document.querySelector('input[name="celular"]');

    celularInput.addEventListener('input', function (e) {
        let x = celularInput.value.replace(/\D/g, '').slice(0, 11); // só números

        if (x.length === 0) {
            celularInput.value = "";
        } else if (x.length <= 2) {
            celularInput.value = `(${x}`;
        } else if (x.length <= 6) {
            celularInput.value = `(${x.slice(0, 2)}) ${x.slice(2)}`;
        } else if (x.length <= 10) {
            celularInput.value = `(${x.slice(0, 2)}) ${x.slice(2, 6)}-${x.slice(6)}`;
        } else {
            celularInput.value = `(${x.slice(0, 2)}) ${x.slice(2, 7)}-${x.slice(7, 11)}`;
        }
    });

    // Permite apagar completamente com Backspace
    celularInput.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace') {
            let x = celularInput.value.replace(/\D/g, '');
            if (x.length === 1) {
                celularInput.value = '';
                e.preventDefault();
            }
        }
    });
});

