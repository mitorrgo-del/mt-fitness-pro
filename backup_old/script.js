document.addEventListener('DOMContentLoaded', () => {
    // Navbar Scroll Effect
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Mobile Menu Toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    // In a real app we would toggle a class to show/hide the menu, 
    // but for simplicity we'll just toggle display here or add a class in CSS.
    // Let's implement a simple alert for the demo or just scroll to section.
    mobileMenuBtn.addEventListener('click', () => {
        if (navLinks.style.display === 'flex') {
            navLinks.style.display = 'none';
        } else {
            navLinks.style.display = 'flex';
            navLinks.style.flexDirection = 'column';
            navLinks.style.position = 'absolute';
            navLinks.style.top = '100%';
            navLinks.style.left = '0';
            navLinks.style.width = '100%';
            navLinks.style.background = 'rgba(13, 15, 20, 0.95)';
            navLinks.style.backdropFilter = 'blur(10px)';
            navLinks.style.padding = '1rem';
            navLinks.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        }
    });

    // Close mobile menu when clicking a link
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) {
                navLinks.style.display = 'none';
            }
        });
    });

    // Intersection Observer for Reveal Animations
    const revealElements = document.querySelectorAll('.reveal');
    
    const revealOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealOnScroll = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, revealOptions);

    revealElements.forEach(el => {
        revealOnScroll.observe(el);
    });

    // Form Submission Handling
    const contactForm = document.getElementById('contactForm');
    const successMsg = document.querySelector('.form-success');
    const submitBtn = document.querySelector('.form-submit');

    contactForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevent standard form submission
        
        // Change button text to indicate loading
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = 'Enviando...';
        submitBtn.disabled = true;

        // Simulate an API call / Email sending
        setTimeout(() => {
            // Hide form fields
            const formFields = contactForm.querySelectorAll('.form-group');
            formFields.forEach(field => field.style.display = 'none');
            
            // Hide button
            submitBtn.style.display = 'none';
            
            // Show success message
            successMsg.classList.remove('hidden');
        }, 1500);
    });
});
