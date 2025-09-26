import os
import fitz  # PyMuPDF 
import cv2
import numpy as np

input_folder = "entrada"    # pasta com os PDFs originais
output_folder = "saida"    # pasta onde salvará os PDFs tarjados

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".pdf"):
        input_pdf = os.path.join(input_folder, filename)
        output_pdf = os.path.join(output_folder, f"tarjado_{filename}")

        doc = fitz.open(input_pdf)

        for page in doc:
            # Converte página para imagem
            pix = page.get_pixmap(dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

            # Detecta QR code
            detector = cv2.QRCodeDetector()
            val, pts, _ = detector.detectAndDecode(img)

            # Só continua se realmente achou QR válido
            if pts is not None and val.strip() != "":
                pts = pts[0]
                x_min, y_min = np.min(pts, axis=0)
                x_max, y_max = np.max(pts, axis=0)

                # Coordenadas do QR no sistema PDF
                qr_rect = fitz.Rect(
                    x_min * page.rect.width / pix.width,
                    y_min * page.rect.height / pix.height,
                    x_max * page.rect.width / pix.width,
                    y_max * page.rect.height / pix.height
                )

                # Extrai blocos de texto para encontrar o bloco à direita do QR
                blocos = page.get_text("blocks")
                bloco_alvo = None
                menor_distancia = float("inf")

                for bloco in blocos:
                    x0, y0, x1, y1, texto, _, _ = bloco
                    if not (y1 < qr_rect.y0 or y0 > qr_rect.y1):
                        if x0 > qr_rect.x1:
                            distancia = x0 - qr_rect.x1
                            if distancia < menor_distancia:
                                menor_distancia = distancia
                                bloco_alvo = bloco

                if bloco_alvo:
                    x0_b, y0_b, x1_b, y1_b, texto_b, _, _ = bloco_alvo
                    largura_caixa_texto = x1_b - qr_rect.x1
                else:
                    largura_caixa_texto = 100  # fallback

                # Define a área a ser tarjada (QR + bloco texto à direita)
                rect_expandida = fitz.Rect(
                    qr_rect.x0,
                    qr_rect.y0,
                    min(page.rect.width, qr_rect.x1 + largura_caixa_texto),
                    qr_rect.y1
                )

                page.add_redact_annot(rect_expandida, fill=(0, 0, 0))
                page.apply_redactions()  # só aplica se adicionou algo

        doc.save(output_pdf)
print(f"Arquivo processado e salvo: {output_pdf}")
print(f" ")
print(f"Desenvolvido por Gcont/SEEDF")
print(f" ")