# Guía: Cómo usar tu Disco Duro Portable (MT Fitness Pro - Full Suite)

¡Felicidades! Has convertido tu disco duro en una **estación de trabajo completa y 100% portable**. Todo lo necesario para programar (Python, Flutter, Node.js y Git) está ahora en tu disco externo.

---

## 💻 Paso 1: Conectar el disco
Asegúrate de que el disco esté conectado. En esta guía asumiremos que Windows le asigna la letra **E:** (si es otra letra, solo cámbiala en las rutas de abajo).

## 🚀 Paso 2: Activar las herramientas (Path)
Para que el nuevo PC sepa dónde están tus programas sin instalar nada, añade estas rutas a tus **Variables de entorno (Path de usuario)**:

1. **Flutter**: `E:\MT_Fitness_Tools\flutter\bin`
2. **Python**: `E:\MT_Fitness_Tools\python`
3. **Python (Scripts/pip)**: `E:\MT_Fitness_Tools\python\Scripts`
4. **Node.js**: `E:\MT_Fitness_Tools\node`
5. **Git**: `E:\MT_Fitness_Tools\git\cmd`

*Tip: Para abrir las variables de entorno rápido, pulsa `Win + R` y escribe `rundll32.exe sysdm.cpl,EditEnvironmentVariables`*

---

## 🛠️ Herramientas Instaladas en el Disco:

### 🐍 Python (v3.12.9)
Ubicación: `E:\MT_Fitness_Tools\python`
He pre-instalado todas las librerías de tu proyecto (`Flask`, `openai`, `psycopg2`, etc.).
Para ejecutar tu servidor:
```powershell
python flask_app.py
```

### 📦 Node.js (v22.14.0) & npm
Ubicación: `E:\MT_Fitness_Tools\node`
Ideal para cualquier herramienta de frontend o despliegue que necesitemos en el futuro.

### 🌳 Git (v2.48.1)
Ubicación: `E:\MT_Fitness_Tools\git`
Tus repositorios y comandos git funcionarán en cualquier PC sin necesidad de instalar el Git oficial de Windows.

### 🐦 Flutter SDK
Ubicación: `E:\MT_Fitness_Tools\flutter`
Configurado para el desarrollo de la App Móvil.

---

## 🧠 Paso 3: Recuperar tu Memoria (Antigravity)
Si usas el asistente Antigravity en otro PC:
1. Instala Antigravity en el nuevo PC.
2. Copia tu "memoria" desde: `E:\MT_Fitness_Migration\antigravity` hacia la carpeta de AppData del sistema.
3. ¡Y listo! Recordaré todo nuestro progreso.

## 📂 Paso 4: Tus Proyectos
Están en: `E:\MT_Fitness_Migration\antigravity\playground\ancient-singularity`

---

### 💡 Consejo de Seguridad
Extrae siempre el disco de forma segura para evitar que la base de datos `mtfitness.db` se corrompa.
