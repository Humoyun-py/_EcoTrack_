// =====================
// ENERGIYA SOTIB OLISH
// =====================
document.querySelectorAll('.buy-energy').forEach(button => {
    button.addEventListener('click', function() {
        const energy = this.dataset.energy;
        const price = this.dataset.price;

        if (confirm(`${energy} energiya sotib olish uchun ${price} coin to'lashni tasdiqlaysizmi?`)) {
            fetch(`/buy_energy`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    energy: parseInt(energy),
                    price: parseInt(price)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ ' + data.message);
                    location.reload();
                } else {
                    alert('❌ ' + data.error);
                }
            })
            .catch(error => {
                alert('❌ Xatolik yuz berdi: ' + error);
            });
        }
    });
});

// =================
// ITEM SOTIB OLISH
// =================
document.querySelectorAll('.buy-item').forEach(button => {
    button.addEventListener('click', function() {
        const itemId = this.dataset.itemId;
        const itemName = this.closest('.card').querySelector('.card-title').textContent;

        if (confirm(`${itemName} sotib olishni tasdiqlaysizmi?`)) {
            fetch(`/buy_item/${itemId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ ' + data.message);
                    location.reload();
                } else {
                    alert('❌ ' + data.error);
                }
            })
            .catch(error => {
                alert('❌ Xatolik yuz berdi: ' + error);
            });
        }
    });
});

// ======================
// KATEGORIYA FILTRLAR
// ======================
document.querySelectorAll('.filter-btn').forEach(button => {
    button.addEventListener('click', function() {
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active', 'btn-success');
            btn.classList.add('btn-outline-success');
        });

        this.classList.add('active', 'btn-success');
        this.classList.remove('btn-outline-success');

        const filter = this.dataset.filter;
        const items = document.querySelectorAll('.item-card');

        items.forEach(item => {
            const type = item.dataset.type;

            if (filter === 'all' || filter === type) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
});
