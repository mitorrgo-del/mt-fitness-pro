from PIL import Image
import numpy as np

def process_logo(input_path, output_path):
    print("Loading image...")
    img = Image.open(input_path).convert('RGBA')
    data = np.array(img)

    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # 1. Hacer el fondo transparente
    # Suponemos que el fondo es blanco (valores altos en RGB)
    bg_mask = (r > 240) & (g > 240) & (b > 240)
    data[bg_mask, 3] = 0

    # 2. Convertir la parte azul a dorada
    # Azul: B > R y B > G de forma significativa
    blue_mask = (b > 100) & (b > r + 30) & (b > g + 30) & (a > 50)
    
    # Objetivo dorado: #D4AF37 (R:212, G:175, B:55)
    # Reemplazamos los píxeles azules, pero mantenemos una mínima preservación de sombra/brillo
    # Para ser simples y contundentes, si es azul, pasa a nuestro dorado:
    data[blue_mask, 0] = 212
    data[blue_mask, 1] = 175
    data[blue_mask, 2] = 55
    data[blue_mask, 3] = 255 # Opaco
    
    # Cuidado adicional con los bordes (anti-aliasing) que pueden verse celestes o grises azulados
    light_blue_mask = (b > r + 15) & (b > g + 15) & (~blue_mask) & (a > 50) & (~bg_mask)
    data[light_blue_mask, 0] = 212
    data[light_blue_mask, 1] = 175
    data[light_blue_mask, 2] = 55
    
    print("Saving modified image...")
    out_img = Image.fromarray(data)
    out_img.save(output_path, 'PNG')
    print("Logo processed successfully!")

if __name__ == '__main__':
    process_logo('app/logo.png', 'app/logo.png')
