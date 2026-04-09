from PIL import Image
import numpy as np

def process_logo():
    print("Iniciando procesamiento de Logo V2...")
    # Cargar la foto intacta de la semana pasada (ahora en public/)
    img = Image.open('public/logo.png').convert('RGBA')
    data = np.array(img).astype(float)
    
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # 1. Inteligencia de Fondo: Leer el pixel de la esquina (arriba-izq)
    bg_r, bg_g, bg_b = r[0,0], g[0,0], b[0,0]
    print(f"Color de fondo detectado: RGB({bg_r}, {bg_g}, {bg_b})")
    
    # 2. Transparencia Agresiva: Todo lo parecido a ese fondo se va a 0 opacidad
    dist = np.sqrt((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2)
    bg_mask = dist < 45 # Tolerancia para borrar suciedad/bordes
    data[bg_mask, 3] = 0
    
    # 3. Detectar Azul (Incluso marinos/oscuros)
    # Cualquier pixel donde el azul domine sobre el rojo y verde minimamente
    blue_mask = (b > r + 5) & (b > g + 5) & (~bg_mask) & (a > 20)
    
    # 4. Inyectar Oro Puro (#D4AF37)
    data[blue_mask, 0] = 212
    data[blue_mask, 1] = 175
    data[blue_mask, 2] = 55
    data[blue_mask, 3] = 255 # Dejar opaco y solido
    
    # 5. Bordes dorados (Anti-aliasing)
    light_blue_mask = (b > r + 2) & (b > g + 2) & (~bg_mask) & (~blue_mask) & (a > 10)
    data[light_blue_mask, 0] = 212
    data[light_blue_mask, 1] = 175
    data[light_blue_mask, 2] = 55
    
    print("Guardando nueva version en TODAS las carpetas...")
    final_img = Image.fromarray(data.astype(np.uint8))
    
    # Sobreescribir tanto en public como en app para evitar rutas ciegas de flask
    final_img.save('app/logo.png', 'PNG')
    final_img.save('public/logo.png', 'PNG')
    print("Mision de Logo cumplida!")

if __name__ == '__main__':
    process_logo()
