document.addEventListener('DOMContentLoaded', () => {
    
    // --- UI Helpers ---
    const showToast = (msg) => {
        let t = document.getElementById('toast');
        if(!t) {
            t = document.createElement('div');
            t.id = 'toast';
            t.className = 'toast';
            document.body.appendChild(t);
        }
        t.innerText = msg;
        t.style.display = 'block';
        t.style.position = 'fixed';
        t.style.bottom = '20px';
        t.style.right = '20px';
        t.style.background = 'var(--primary)';
        t.style.color = 'white';
        t.style.padding = '12px 24px';
        t.style.borderRadius = '12px';
        t.style.zIndex = '10000';
        t.style.boxShadow = '0 10px 30px var(--primary-glow)';
        setTimeout(() => t.style.display = 'none', 3000);
    };

    const getView = id => document.getElementById(id);
    let currentActiveView = 'view-landing';

    const switchView = (viewId) => {
        currentActiveView = viewId;
        document.querySelectorAll('.view').forEach(v => {
            v.style.display = 'none';
            v.classList.remove('active');
        });
        const target = getView(viewId);
        if(target) {
            if(viewId === 'view-auth') target.style.display = 'flex';
            else target.style.display = 'block';
            setTimeout(() => target.classList.add('active'), 10);
        }
        
        // --- Navbar visibility ---
        const nav = document.getElementById('mainNav');
        if(nav) {
            // Only hide nav in Auth or App view (sometimes)
            // But for Blog/Landing we want it
            nav.style.display = (viewId === 'view-landing' || viewId === 'view-blog') ? 'block' : 'none';
        }
        
        if(viewId === 'view-blog') loadArticles();
        window.scrollTo(0, 0);
    };

    // --- State & API ---
    const API_URL = '/api';
    let state = {
        token: localStorage.getItem('mt_token') || null,
        role: localStorage.getItem('mt_role') || null,
        name: localStorage.getItem('mt_name') || null
    };
    const headers = () => ({ 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` });

    // --- Navigation ---
    const mobileToggle = document.getElementById('mobile-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMobile = document.getElementById('close-mobile');
    if(mobileToggle) mobileToggle.onclick = () => mobileMenu.classList.add('active');
    if(closeMobile) closeMobile.onclick = () => mobileMenu.classList.remove('active');
    
    window.onscroll = () => {
        const nav = document.getElementById('mainNav');
        if(nav) window.scrollY > 50 ? nav.classList.add('scrolled') : nav.classList.remove('scrolled');
    };

    document.getElementById('show-login-btn').onclick = () => state.token ? initApp() : switchView('view-auth');
    document.getElementById('mobile-login-btn').onclick = () => { mobileMenu.classList.remove('active'); document.getElementById('show-login-btn').click(); };
    
    // Blog navigation
    document.getElementById('nav-blog').onclick = (e) => { e.preventDefault(); switchView('view-blog'); };
    document.getElementById('mobile-nav-blog').onclick = (e) => { e.preventDefault(); mobileMenu.classList.remove('active'); switchView('view-blog'); };

    // Common back button
    document.querySelectorAll('.back-to-landing').forEach(btn => btn.onclick = (e) => { 
        e.preventDefault(); 
        if(mobileMenu) mobileMenu.classList.remove('active');
        switchView('view-landing'); 
    });

    // Handle ALL nav links that are anchors
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if(href === '#') return;
            
            // If it's the blog link, switchView handles it above, so we skip here or handle it specifically
            if(href === '#blog') return;

            if(currentActiveView !== 'view-landing') {
                e.preventDefault();
                if(mobileMenu) mobileMenu.classList.remove('active');
                switchView('view-landing');
                setTimeout(() => {
                    const id = href.replace('#', '');
                    const el = document.getElementById(id);
                    if(el) el.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            } else {
                // Already on landing, if mobile menu open, close it
                if(mobileMenu) mobileMenu.classList.remove('active');
            }
        });
    });

    // --- Auth View ---
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    document.getElementById('goRegister').onclick = (e) => { e.preventDefault(); loginForm.style.display = 'none'; registerForm.style.display = 'block'; };
    document.getElementById('goLogin').onclick = (e) => { e.preventDefault(); registerForm.style.display = 'none'; loginForm.style.display = 'block'; };

    const initApp = () => {
        if(state.token) {
            buildAppDashboard();
            switchView('view-app');
            if(state.role === 'ADMIN') { loadAdminData(); loadCatalogsAdmin(); }
            loadDashboardData();
            loadClientData();
        } else { switchView('view-landing'); }
    };

    loginForm.onsubmit = async (e) => {
        e.preventDefault();
        const payload = { email: getView('loginEmail').value, password: getView('loginPassword').value };
        try {
            const res = await fetch(`${API_URL}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const data = await res.json();
            if(!res.ok) throw new Error(data.error);
            localStorage.setItem('mt_token', data.token);
            localStorage.setItem('mt_role', data.role);
            localStorage.setItem('mt_name', data.name);
            state = { token: data.token, role: data.role, name: data.name };
            showToast(`Bienvenido, ${state.name}`);
            initApp();
        } catch(err) { showToast(err.message); }
    };

    // --- Dashboard Builder ---
    function buildAppDashboard() {
        const container = getView('app-content-container');
        container.innerHTML = `
            <header class="navbar scrolled" style="position: sticky; top:0; z-index:100; background: var(--bg-card); padding: 15px 0;">
                <div class="container nav-container">
                    <div class="nav-logo" onclick="window.location.reload()" style="cursor:pointer">
                        <img src="logo.png" style="width:32px; height:32px;">
                        <span class="logo-font" style="font-size:16px;">MT <span class="text-gradient">PRO</span></span>
                    </div>
                </div>
            </header>
            <div id="view-admin-inner" style="margin-top:60px; padding-top:40px; border-top: 1px solid var(--border);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 class="text-gradient">Gabinete del Coach</h2>
                    <button class="btn btn-secondary btn-sm" onclick="triggerAiGeneration()"><i data-lucide="sparkles"></i> Generar Artículos IA</button>
                </div>
                <div id="usersList" style="margin-top:20px;"></div>
            </div>
            <div class="container" style="padding-top:30px; padding-bottom:100px;">
                <h2 style="margin-bottom:20px;">Hola, <span class="text-gradient">${state.name}</span></h2>
                <div id="measurementsGrid" class="features-grid" style="margin-bottom:30px;"></div>
                <div id="dietPlanDedicated"></div>
                <div id="exerciseList"></div>
            </div>
        `;
        lucide.createIcons();
    }

    // --- Data Loaders ---
    async function loadDashboardData() {
        try {
            const res = await fetch(`${API_URL}/measurements`, { headers: headers() });
            const data = await res.json();
            const grid = getView('measurementsGrid');
            if(grid) grid.innerHTML = data.slice(0, 4).map(m => `
                <div class="glass-card" style="padding:20px; text-align:center;">
                    <div class="text-dim" style="font-size:11px;">${m.date}</div>
                    <div style="font-size:20px; font-weight:800; color:var(--primary);">${m.weight} kg</div>
                </div>
            `).join('') || '<p class="text-muted">No hay mediciones aún.</p>';
        } catch(e) {}
    }

    async function loadClientData() {
        try {
            const resD = await fetch(`${API_URL}/client/my_plan`, { headers: headers() });
            const diet = await resD.json();
            const dietDiv = getView('dietPlanDedicated');
            if(dietDiv) dietDiv.innerHTML = diet.length ? '<div class="badge-new">TU DIETA</div>' + diet.map(f => `
                <div class="glass-card" style="padding:15px; margin-bottom:10px; display:flex; justify-content:space-between;">
                    <span><strong>${f.grams}g</strong> ${f.name}</span>
                    <span class="text-muted">${f.calc_kcal.toFixed(0)} kcal</span>
                </div>
            `).join('') : '';

            const resW = await fetch(`${API_URL}/client/my_workout`, { headers: headers() });
            const work = await resW.json();
            const workDiv = getView('exerciseList');
            if(workDiv) workDiv.innerHTML = work.length ? '<div class="badge-new" style="margin-top:30px;">TU RUTINA</div>' + work.map(ex => `
                <div class="glass-card" style="padding:20px; margin-bottom:15px; border-left: 4px solid var(--primary);">
                    <div style="font-weight:800; font-size:18px;">${ex.name}</div>
                    <div class="text-muted">${ex.sets} x ${ex.reps} | ${ex.muscle_group}</div>
                </div>
            `).join('') : '';
        } catch(e) {}
        lucide.createIcons();
    }

    initApp();
    loadArticles();

    // --- AI ADVISOR LOGIC ---
    const aiFab = document.getElementById('ai-advisor-fab');
    const aiModal = document.getElementById('ai-modal');
    const closeAiModal = document.getElementById('close-ai-modal');
    const aiInput = document.getElementById('ai-input');
    const sendAiBtn = document.getElementById('send-ai-btn');
    const aiChatBody = document.getElementById('ai-chat-body');

    if(aiFab) aiFab.onclick = () => aiModal.classList.add('active');
    if(closeAiModal) closeAiModal.onclick = () => aiModal.classList.remove('active');

    const appendAiMessage = (role, text) => {
        const msg = document.createElement('div');
        msg.className = `ai-message ${role}`;
        msg.innerHTML = text;
        aiChatBody.appendChild(msg);
        aiChatBody.scrollTop = aiChatBody.scrollHeight;
    };

    let aiHistory = [];

    const handleAiSend = async () => {
        const text = aiInput.value.trim();
        if(!text) return;

        appendAiMessage('user', text);
        aiInput.value = '';
        aiHistory.push(text);

        // Show Loading
        const loaderId = 'loader-' + Date.now();
        appendAiMessage('bot', `<span id="${loaderId}"><i data-lucide="sparkles" class="spin"></i> Consultando base de datos biomecánica...</span>`);
        lucide.createIcons();

        try {
            const res = await fetch(`/api/ai/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal: text, history: aiHistory })
            });
            const data = await res.json();
            
            // Remove loader
            const loader = document.getElementById(loaderId);
            if(loader) loader.parentElement.remove();

            // Simple markdown to HTML conversion
            let html = data.analysis
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/### (.*?)\n/g, '<h4 style="color:var(--primary); margin:10px 0;">$1</h4>')
                .replace(/\n\n/g, '<br><br>');

            if (aiHistory.length >= 2) {
                html += `<br><br><div class="glass-card" style="padding:15px; border:1px solid var(--primary);"><p style="font-size:12px; margin-bottom:10px;">¡Últimas plazas disponibles!</p><button class="btn btn-primary btn-full" onclick="document.getElementById('ai-modal').classList.remove('active'); window.location.href='#planes';">Reservar mi plaza PRO (80€)</button></div>`;
            }

            appendAiMessage('bot', html);

            // LEAD GENERATION: If user just sent an email (step 3), save it
            if (aiHistory.length === 3 && text.includes('@')) {
                fetch('/api/marketing/save_lead', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: text, goal: aiHistory[0] })
                });
            }

        } catch(err) {
            const loader = document.getElementById(loaderId);
            if(loader) loader.parentElement.remove();
            appendAiMessage('bot', 'Vaya, mi cerebro IA está sobrecalentado. Por favor, inténtalo en un momento.');
        }
    };

    if(sendAiBtn) sendAiBtn.onclick = handleAiSend;
    if(aiInput) aiInput.onkeypress = (e) => { if(e.key === 'Enter') handleAiSend(); };

    // --- SOCIAL PROOF LOGIC ---
    const proofToast = document.getElementById('social-proof');
    const proofText = document.getElementById('proof-text');
    const fakeEvents = [
        "Alex de Madrid acaba de unirse al Plan PRO",
        "Marta reservó su plaza de Asesoría IA",
        "Juan perdió 4kg en su primera semana PRO",
        "Alguien de Barcelona está viendo los planes ahora",
        "Última plaza de Marzo asignada..."
    ];

    function showProof() {
        if(!proofToast) return;
        const event = fakeEvents[Math.floor(Math.random() * fakeEvents.length)];
        proofText.innerText = event;
        proofToast.classList.add('active');
        setTimeout(() => {
            proofToast.classList.remove('active');
            setTimeout(showProof, 15000 + Math.random() * 20000); // Wait 15-35s
        }, 5000);
    }
    setTimeout(showProof, 5000);
});

async function triggerAiGeneration() {
    showToast("IA Generando contenido...");
    try {
        const res = await fetch('/api/admin/generate_articles', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('mt_token')}` }
        });
        if(res.ok) {
            showToast("¡Blog actualizado con IA!");
            loadArticles();
        }
    } catch(e) { showToast("Error en la conexión IA"); }
}

async function loadArticles() {
    try {
        const res = await fetch('/api/articles');
        const articles = await res.json();
        const grid = document.getElementById('blog-grid-main');
        if(grid && articles.length > 0) {
            grid.innerHTML = articles.map(art => `
                <div class="glass-card" style="padding:0; overflow:hidden; display:flex; flex-direction:column;">
                    <img src="${art.image_url}" style="width:100%; height:200px; object-fit:cover;">
                    <div style="padding:20px;">
                        <span class="badge-new" style="font-size:10px;">${art.category}</span>
                        <h3 style="margin:10px 0; font-size:18px;">${art.title}</h3>
                        <p class="text-muted" style="font-size:14px; line-height:1.6;">${art.content}</p>
                        <div style="margin-top:20px; font-size:12px; color:var(--text-dim);">${art.date}</div>
                    </div>
                </div>
            `).join('');
        }
    } catch(e) {
        console.error("Error cargando blog:", e);
    }
}
