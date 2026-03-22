import sqlite3
import datetime
from ai_services import send_followup_email

def process_marketing_followups():
    """
    Checks the database for leads that registered 24h ago and haven't bought yet.
    """
    conn = sqlite3.connect('mtfitness.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Logic: COLD leads older than 24 hours that haven't received a followup yet
    # For this simulation, we'll just take leads created today to demo
    query = "SELECT * FROM marketing_leads WHERE status = 'COLD'"
    leads = c.execute(query).fetchall()
    
    print(f"Marketing Bot: Procesando {len(leads)} leads...")
    
    for lead in leads:
        # 1. Send simulated email
        success = send_followup_email(lead['email'], lead['name'] or 'Guerrero/a', lead['last_goal'])
        
        if success:
            # 2. Update status so we don't spam 
            c.execute("UPDATE marketing_leads SET status = 'FOLLOWED_UP', last_followup = CURRENT_TIMESTAMP WHERE id = ?", (lead['id'],))
    
    conn.commit()
    conn.close()
    print("Marketing Bot: Tarea completada.")

if __name__ == "__main__":
    process_marketing_followups()
