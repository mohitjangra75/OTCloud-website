/* Live character counts under the SEO fields, turning amber past the length Google shows. */
document.addEventListener('DOMContentLoaded', function () {
    [['id_meta_title', 60], ['id_meta_description', 160]].forEach(function (pair) {
        var input = document.getElementById(pair[0]);
        if (!input) return;
        var note = document.createElement('div');
        note.className = 'help';
        input.insertAdjacentElement('afterend', note);
        function update() {
            var n = input.value.length;
            note.textContent = n + ' / ' + pair[1] + ' characters';
            note.style.color = n > pair[1] ? '#b45309' : '';
        }
        input.addEventListener('input', update);
        update();
    });
});
