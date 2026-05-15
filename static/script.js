

        // Add smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
        const dropArea = document.getElementById("drop-area");
const input = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const loader = document.getElementById("loader");

input.addEventListener("change", () => {
    const file = input.files[0];
    preview.src = URL.createObjectURL(file);
});

dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
});

dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    input.files = e.dataTransfer.files;
    preview.src = URL.createObjectURL(input.files[0]);
});

document.querySelector("form").addEventListener("submit", () => {
    loader.style.display = "block";
});
        // Add hover effects for condition items
        document.querySelectorAll('.condition-item').forEach(item => {
            item.addEventListener('click', function() {
                const icon = this.querySelector('.expand-icon');
                if (icon.textContent === '∨') {
                    icon.textContent = '∧';
                } else {
                    icon.textContent = '∨';
                }
            });
        });

        // Add animation on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.querySelectorAll('.stat-card, .step-card, .tech-card, .condition-item, .prevention-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(el);
        });

        // Floating cards animation
        const floatingCards = document.querySelectorAll('.floating-card');
        floatingCards.forEach((card, index) => {
            card.style.animation = `float ${3 + index * 0.5}s ease-in-out infinite`;
        });

        // Add float animation keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
        `;
        document.head.appendChild(style);
    function searchHospitals() {
    const location = document.getElementById("locationInput").value;

    if (!location) {
        alert("Enter location");
        return;
    }

    fetch(`/search_hospitals?location=${location}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("results");
            container.innerHTML = "";

            if (data.error) {
                container.innerHTML = `<p>${data.error}</p>`;
                return;
            }

            data.hospitals.forEach(h => {
                container.innerHTML += `
                    <div class="card">
                        <h3>${h.name}</h3>
                        <p>Lat: ${h.lat}, Lon: ${h.lon}</p>
                    </div>
                `;
            });
        });
}
```
