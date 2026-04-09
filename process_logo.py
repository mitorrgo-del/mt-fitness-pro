from PIL import Image
import numpy as np

def process_logo_v3():
    print("Iniciando Escáner Láser de Opacidad en V3...")
    
    # Cargamos el VIRGEN original recuperado del abismo
    img = Image.open('public/logo_original.png').convert('RGBA')
    data = np.array(img).astype(float)
    
    r, g, b = data[:,:,0], data[:,:,1], data[:,:,2]
    
    # Extraer el Brillo general de cada píxel para mapear el Alpha
    # El Negro Puro da ~0, el Blanco da ~255.
    max_c = np.max(data[:,:,:3], axis=2)
    
    # El Fondo es Gris Oscuro (Luminancia ~ 18/20).
    # Hacemos que la transparencia pase suavemente del valor 25 (0 alpha) a 100 (opaco puro)
    alpha = (max_c - 20) / (80 - 20) * 255
    alpha = np.clip(alpha, 0, 255)
    
    data[:,:,3] = alpha
    
    # Ahora detectamos qué letras son blancas y cuáles son AZULES.
    # El Azul puro destila un Azúl > Rojo considerablemente.
    blue_mask = (b > r + 15) & (b > g + 15) & (alpha > 10)
    
    # Bañamos solo a esta máscara en nuestro ORO puro iluminado
    brightness = max_c[blue_mask] / 255.0
    
    # Colores objetivo (D4AF37): 212, 175, 55
    # Boost del 1.5 en el brillo para que brille intenso.
    data[blue_mask, 0] = np.clip(212 * brightness * 1.5, 0, 255)
    data[blue_mask, 1] = np.clip(175 * brightness * 1.5, 0, 255)
    data[blue_mask, 2] = np.clip(55 * brightness * 1.5, 0, 255)
    
    # Guardamos forzosamente en el sistema
    print("Guardando Render Transparente Dorado y Puro ...")
    out = Image.fromarray(data.astype(np.uint8))
    out.save('public/logo_oro.png', 'PNG')
    out.save('app/logo_oro.png', 'PNG')
    print("¡Exito V3 Logo!")

if __name__ == '__main__':
    process_logo_v3()
