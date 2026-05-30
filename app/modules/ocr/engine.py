# Motor de extraccion de texto de PDFs
# Estrategia 1: pdfplumber (texto nativo - rapido y preciso)
# Estrategia 2: easyocr (para PDFs escaneados o con imagenes)
# Se usa estrategia 2 solo si el texto extraido tiene menos de 100 caracteres

from pathlib import Path
import pdfplumber


class MotorOCR:
    def __init__(self):
        # Inicializacion lazy del lector OCR (no carga modelos hasta necesitar)
        self._lector_ocr = None

    @property
    def lector_ocr(self):
        if self._lector_ocr is None:
            try:
                import easyocr
                # Carga modelos para espaniol e ingles (los PDFs de AFIP pueden tener ambos)
                self._lector_ocr = easyocr.Reader(["es", "en"], gpu=False)
            except Exception:
                # easyocr no instalado o falla: dejar en None para que _extraer_ocr retorne ""
                self._lector_ocr = None
        return self._lector_ocr

    async def extraer(self, ruta_pdf: Path) -> dict:
        """
        Extrae texto de un PDF.
        Retorna: {"texto": str, "metodo": "nativo"|"ocr", "paginas": int}
        """
        texto = self._extraer_nativo(ruta_pdf)
        if len(texto.strip()) < 100:
            texto_ocr = self._extraer_ocr(ruta_pdf)
            return {
                "texto": texto_ocr,
                "metodo": "ocr",
                "paginas": self._contar_paginas(ruta_pdf),
            }
        return {
            "texto": texto,
            "metodo": "nativo",
            "paginas": self._contar_paginas(ruta_pdf),
        }

    def _extraer_nativo(self, ruta_pdf: Path) -> str:
        # Extrae texto nativo del PDF usando pdfplumber
        texto_completo = []
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text() or ""
                    texto_completo.append(texto)
        except Exception:
            return ""
        return "\n".join(texto_completo)

    def _extraer_ocr(self, ruta_pdf: Path) -> str:
        # Extrae texto usando OCR para PDFs escaneados
        lector = self.lector_ocr
        if lector is None:
            # easyocr no disponible - degradar elegantemente
            return ""
        try:
            import fitz  # PyMuPDF
            import numpy as np
            from PIL import Image
            import io
        except Exception:
            return ""

        texto_completo = []
        try:
            doc = fitz.open(str(ruta_pdf))
            for pagina in doc:
                pix = pagina.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                img_array = np.array(img)
                resultado = lector.readtext(img_array, detail=0)
                texto_completo.append(" ".join(resultado))
            doc.close()
        except Exception:
            return ""
        return "\n".join(texto_completo)

    def _contar_paginas(self, ruta_pdf: Path) -> int:
        # Cuenta las paginas del PDF
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
