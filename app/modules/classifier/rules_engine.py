# Clasifica documentos por palabras clave encontradas en el texto OCR
class ClasificadorDocumentos:
    PALABRAS_CLAVE = {
        "VEP": ["VOLANTE ELECTRONICO DE PAGO", "VEP", "VOLANTE ELECTRONICO"],
        "SUSS": ["SISTEMA UNICO DE SEGURIDAD SOCIAL", "SUSS", "ANSES", "SEGURIDAD SOCIAL"],
        "IIBB": ["INGRESOS BRUTOS", "ARBA", "AGIP", "RENTAS"],
        "DECLARACION_IVA": ["DECLARACION JURADA", "IVA", "F. 2002", "FORMULARIO 2002"],
        "DECLARACION_GANANCIAS": ["GANANCIAS", "F. 713", "FORMULARIO 713"],
        "FACTURA_PROVEEDOR": ["FACTURA", "COMPROBANTE", "FC."],
    }

    def clasificar(self, texto: str) -> tuple[str, float]:
        """
        Determina el tipo de documento basandose en palabras clave.
        Retorna (tipo_documento, confianza).
        Si no matchea nada retorna ("OTRO", 0.3).
        """
        texto_upper = (texto or "").upper()
        mejor_tipo = "OTRO"
        mejor_confianza = 0.3
        mejor_matches = 0

        for tipo, palabras in self.PALABRAS_CLAVE.items():
            matches = sum(1 for p in palabras if p in texto_upper)
            if matches > mejor_matches:
                mejor_matches = matches
                mejor_tipo = tipo
                mejor_confianza = min(0.5 + (matches * 0.15), 0.95)

        return mejor_tipo, mejor_confianza
