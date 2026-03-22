import os
import sqlite3
import uuid

# In a real scenario, use: 
# import openai
# openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_goal_with_ai(user_input, history=[]):
    """
    Simulates a consultative AI expert.
    """
    text = user_input.lower()
    
    # Check if we are in a follow-up or initial phase
    if len(history) < 2:
        return (
            f"Interesante objetivo: **{user_input}**. Para darte una respuesta de precisión científica, "
            "necesito saber un detalle más: ¿Cuántos días a la semana puedes dedicarle al entrenamiento real? "
            "(Dime un número del 1 al 7)"
        )
    
    # Step 3: Ask for email to "send the report" (Lead Generation)
    if len(history) == 2:
        return (
            "Análisis casi listo. Para enviarte este informe detallado a tu correo y guardarlo en tu perfil, "
            "**¿cuál es tu email?** (Prometo no hacer spam, solo ciencia fitness 🧬)"
        )

    # Final Pitch Logic (If history >= 3, they presumably sent an email)
    days = "3-4" if any(x in history[1] for x in ["3", "4"]) else "varios"
    
    analysis = (
        f"### 🧬 Análisis de Potencial Genético: COMPLETADO\n\n"
        f"Con {days} días de entreno y tu meta de *{history[0]}*, he calculado tu hoja de ruta:\n\n"
        "1. **Déficit Metabólico**: Necesitarás un ajuste del 15% en carbs complejos.\n"
        "2. **Estímulo Muscular**: Enfoque en RIR 2 para optimizar la hipertrofia sin quemar el CNS.\n"
        "3. **Suplementación**: Omega 3 y Creatina Monohidrato como base.\n\n"
        "⚠️ **OJO**: Mi base de datos muestra que solo quedan **2 plazas de asesoría PRO** para esta semana con el Coach Mario. "
        "Si quieres asegurar tu transformación con el plan exacto por gramos y series, ahora es el momento."
    )
    return analysis

def send_followup_email(email, name, goal):
    """
    Simulates sending a persuasive follow-up email after 24h.
    """
    print(f"--- SIMULANDO ENVÍO DE EMAIL A {email} ---")
    subject = f"¿Sigues queriendo {goal}, {name}?"
    body = (
        f"Hola {name},\n\n"
        f"Ayer estuvimos analizando tu meta de {goal} en MT Fitness. "
        "Soy el Coach Mario y quería comentarte que he revisado tu caso con la IA.\n\n"
        "He visto que tu metabolismo base sugiere que podrías ver cambios en solo 3 semanas "
        "si ajustamos bien los macros. Me daría rabia que ese análisis se quedara en nada.\n\n"
        "He guardado tu plaza PRO por 12 horas más. Si entras ahora, te incluyo la guía de "
        "Suplementación de Élite gratis.\n\n"
        "Entra aquí: http://localhost:5000/#planes\n\n"
        "A tope,\nCoach Mario."
    )
    # logic to send email (smtplib) would go here
    return True

def simulate_payment_and_unlock(user_id, plan_type):
    """
    Simulates a payment webhook from Stripe.
    Unlocks high-tier access for the user.
    """
    # This would be called by a Stripe Webhook
    # For now, we manually simulate it
    conn = sqlite3.connect('mtfitness.db')
    c = conn.cursor()
    
    # Let's say we give 30 days of access
    import datetime
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    
    c.execute("UPDATE users SET status = 'APPROVED', access_until = ? WHERE id = ?", (expiry, user_id))
    conn.commit()
    conn.close()
    return True
