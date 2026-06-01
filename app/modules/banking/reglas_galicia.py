# Reglas de asignación contable para movimientos del Banco Galicia
# Basadas en el extracto real del cliente y su plan de cuentas real de Dolibarr
# Plan de cuentas completo de la empresa (agencia de marketing argentina)

PLAN_DE_CUENTAS = {
    # ACTIVO
    "1.1.3.104": "IVA Crédito fiscal 27%",
    "1.1.3.105": "IVA Crédito fiscal 10,5%",
    "1.1.3.106": "IVA percepciones sufridas",
    "1.1.3.107": "IVA Retenciones sufridas",
    "1.1.3.201": "Ingresos brutos saldo a favor CABA",
    "1.1.3.202": "IIBB saldo a favor BA",
    "1.1.3.203": "IIBB saldo a favor RN",
    "1.1.3.204": "IIBB Percepciones bancarias (SIRCREB)",
    "1.1.3.205": "IIBB Percepciones sufridas",
    "1.1.3.206": "IIBB Retenciones sufridas",
    "1.1.3.301": "Impuesto a las ganancias saldo a favor",
    "1.1.3.302": "IIGG Retenciones sufridas",
    "1.1.3.303": "IIGG Percepciones",
    "1.1.3.401": "Impuesto sobre Créditos y débitos bancarios (activo)",
    "1.1.5.101": "Depósitos a plazo fijo",
    "1.1.5.102": "Fondos de Inversión",
    # PASIVO
    "2.1.1.201": "Anticipo de clientes",
    "2.1.2.101": "Sueldos a pagar",
    "2.1.2.102": "SUSS a pagar",
    "2.1.2.201": "Provisión SAC",
    "2.1.2.202": "Provisión Vacaciones a pagar",
    "2.1.3.101": "IVA saldo DDJJ a pagar",
    "2.1.3.102": "IVA Débito fiscal 21%",
    "2.1.3.201": "IIBB CABA DJ a pagar",
    "2.1.3.202": "IIBB BA DJ a pagar",
    "2.1.3.203": "IIBB RN DJ a pagar",
    "2.1.5.101": "Acreedores varios",
    "2.1.5.102": "Dividendos a pagar",
    "2.1.6":     "Plan Mis Facilidades a Pagar",
    "2.2.4.101": "Deudas bancarias a mas de un año",
    "2.2.5.101": "Acreedores Varios L/P",
    "2.2.5.102": "Deudas impositivas a mas de un año",
    # INGRESOS
    "4.1.02":    "Consultoría en informática",
    "4.1.03":    "Comercialización de espacios publicitarios",
    "4.1.04":    "Organización de convenciones",
    "4.1.05":    "Venta de servicios varios",
    "4.1.101":   "Portales Web",
    "4.1.20.1":  "Otros Ingresos del Giro",
    "4.2.01":    "Portales Web exterior",
    "4.2.02":    "Consultoría en informática exterior",
    "4.2.03":    "Comercialización espacios publicitarios exterior",
    "4.4":       "Otros Ingresos",
    # EGRESOS
    "5.1.01":    "Costo servicios subcontratados a terceros",
    "5.1.02":    "Costo de insumos",
    "5.2.01":    "Sueldos administracion",
    "5.2.02":    "Cargas sociales administracion",
    "5.2.03":    "Honorarios servicios administracion",
    "5.2.04":    "Alquiler de oficina",
    "5.2.15":    "Gastos varios de administración",
    "5.2.16":    "Seguros",
    "5.2.17":    "Amortizaciones",
    "5.2.18":    "Servicios contratados",
    "5.3":       "Gastos de comercialización",
    "5.4.01":    "Impuestos y cargas fiscales",
    "5.4.02":    "Intereses fiscales",
    "5.4.03":    "Intereses financieros",
    "5.4.04":    "Multas",
    "5.5.01":    "Impuesto a los ingresos brutos",
    "5.5.02":    "Impuesto sobre Créditos y débitos bancarios",
    "5.5.03":    "Impuesto bs personales acciones",
    "5.5.04":    "Impuesto a los sellos",
    "5.5.05":    "Otros impuestos y tasas",
    "5.5.06":    "Impuesto a las ganancias",
    "5.6.01":    "Diferencia de cambio",
    "5.6.02":    "RECPAM",
    "5.6.03":    "AXI global cuenta de egresos",
    # TRANSITORIA
    "6.0":       "Transferencias bancarias transitorias",
}

REGLAS_CONTABLES = [

    # ══════════════════════════════════════════
    # IMPUESTOS BANCARIOS AUTOMÁTICOS
    # ══════════════════════════════════════════
    {
        "prioridad": 10,
        "nombre": "Impuesto débito bancario Ley 25413",
        "patrones": ["Imp. Deb. Ley 25413", "IMP. DEB. LEY 25413"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.5.02",
        "nombre_cuenta": "Impuesto sobre Créditos y débitos bancarios",
    },
    {
        "prioridad": 11,
        "nombre": "Impuesto crédito bancario Ley 25413",
        "patrones": ["Imp. Cre. Ley 25413", "IMP. CRE. LEY 25413"],
        "tipo": "DEBITO",
        "codigo_cuenta": "1.1.3.401",
        "nombre_cuenta": "Impuesto sobre Créditos y débitos bancarios (activo)",
    },
    {
        "prioridad": 12,
        "nombre": "IIBB sobre créditos bancarios SIRCREB",
        "patrones": ["Ing. Brutos S/ Cred", "ING. BRUTOS S/ CRED"],
        "tipo": "DEBITO",
        "codigo_cuenta": "1.1.3.204",
        "nombre_cuenta": "IIBB Percepciones bancarias (SIRCREB)",
    },
    {
        "prioridad": 13,
        "nombre": "Impuesto Ingresos Brutos general",
        "patrones": ["Imp. Ing. Brutos", "IMP. ING. BRUTOS"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.5.01",
        "nombre_cuenta": "Impuesto a los ingresos brutos",
    },
    {
        "prioridad": 14,
        "nombre": "Percepción IVA bancaria",
        "patrones": ["Percep. Iva", "PERCEP. IVA"],
        "tipo": "DEBITO",
        "codigo_cuenta": "1.1.3.106",
        "nombre_cuenta": "IVA percepciones sufridas",
    },
    {
        "prioridad": 15,
        "nombre": "IVA bancario",
        "patrones": ["Iva", "IVA"],
        "tipo": "DEBITO",
        "codigo_cuenta": "2.1.3.101",
        "nombre_cuenta": "IVA saldo DDJJ a pagar",
    },
    {
        "prioridad": 16,
        "nombre": "Percepción RG 5617/24",
        "patrones": ["Percepcion Rg 5617", "PERCEPCION RG 5617"],
        "tipo": "DEBITO",
        "codigo_cuenta": "1.1.3.205",
        "nombre_cuenta": "IIBB Percepciones sufridas",
    },
    {
        "prioridad": 17,
        "nombre": "Impuesto de sellos",
        "patrones": ["Impuesto De Sellos", "IMPUESTO DE SELLOS"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.5.04",
        "nombre_cuenta": "Impuesto a los sellos",
    },
    {
        "prioridad": 18,
        "nombre": "Intereses fiscales sobre saldos deudores",
        "patrones": ["Intereses Sobre Saldos Deudores", "INTERESES SOBRE SALDOS DEUDORES"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.4.02",
        "nombre_cuenta": "Intereses fiscales",
    },

    # ══════════════════════════════════════════
    # PAGOS A AFIP
    # ══════════════════════════════════════════
    {
        "prioridad": 20,
        "nombre": "Transferencia a AFIP",
        "patrones": ["Transf. Afip", "TRANSF. AFIP"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.4.01",
        "nombre_cuenta": "Impuestos y cargas fiscales",
    },

    # ══════════════════════════════════════════
    # COBROS DE CLIENTES (créditos)
    # ══════════════════════════════════════════
    {
        "prioridad": 30,
        "nombre": "Transferencia recibida de cliente local",
        "patrones": [
            "Transferencia De Terceros", "TRANSFERENCIA DE TERCEROS",
            "Credito Transferencia Coelsa", "CREDITO TRANSFERENCIA COELSA",
            "Transferencias Cash Proveedores",
        ],
        "tipo": "CREDITO",
        "codigo_cuenta": "4.1.05",
        "nombre_cuenta": "Venta de servicios varios",
    },
    {
        "prioridad": 31,
        "nombre": "Cobro cheque electrónico ECHEQ",
        "patrones": ["G.de Echeq", "G.DE ECHEQ", "G.DE CHEQUE"],
        "tipo": "CREDITO",
        "codigo_cuenta": "4.1.05",
        "nombre_cuenta": "Venta de servicios varios",
    },
    {
        "prioridad": 32,
        "nombre": "Cobro del exterior / comex",
        "patrones": ["Comext.orden De Pago", "COMEXT.ORDEN DE PAGO"],
        "tipo": "CREDITO",
        "codigo_cuenta": "4.2.01",
        "nombre_cuenta": "Portales Web exterior",
    },
    {
        "prioridad": 33,
        "nombre": "Anticipo de cliente",
        "patrones": ["Anticipo", "ANTICIPO"],
        "tipo": "CREDITO",
        "codigo_cuenta": "2.1.1.201",
        "nombre_cuenta": "Anticipo de clientes",
    },

    # ══════════════════════════════════════════
    # PAGOS A PROVEEDORES (débitos)
    # ══════════════════════════════════════════
    {
        "prioridad": 40,
        "nombre": "Transferencia inmediata a proveedor",
        "patrones": [
            "Trf Inmed Proveed", "TRF INMED PROVEED",
            "Transf. A Terceros", "TRANSF. A TERCEROS",
            "Transferencia A Terceros", "TRANSFERENCIA A TERCEROS",
        ],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.1.01",
        "nombre_cuenta": "Costo servicios subcontratados a terceros",
    },
    {
        "prioridad": 41,
        "nombre": "Pago a proveedor via servicio Galicia",
        "patrones": ["Servicio Pago A Proveedores", "SERVICIO PAGO A PROVEEDORES"],
        "tipo": None,
        "codigo_cuenta": "5.1.01",
        "nombre_cuenta": "Costo servicios subcontratados a terceros",
    },
    {
        "prioridad": 42,
        "nombre": "Alquiler de oficina",
        "patrones": ["Alquiler", "ALQUILER", "Expensas", "EXPENSAS"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.04",
        "nombre_cuenta": "Alquiler de oficina",
    },
    {
        "prioridad": 43,
        "nombre": "Seguro",
        "patrones": ["Seguro", "SEGURO"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.16",
        "nombre_cuenta": "Seguros",
    },

    # ══════════════════════════════════════════
    # SUELDOS Y CARGAS SOCIALES
    # ══════════════════════════════════════════
    {
        "prioridad": 50,
        "nombre": "Acreditación de sueldos",
        "patrones": [
            "Servicio Acreditamiento De Haberes",
            "SERVICIO ACREDITAMIENTO DE HABERES",
        ],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.01",
        "nombre_cuenta": "Sueldos administracion",
    },
    {
        "prioridad": 51,
        "nombre": "Pago SUSS / cargas sociales",
        "patrones": ["SUSS", "Suss", "Cargas Sociales", "CARGAS SOCIALES"],
        "tipo": "DEBITO",
        "codigo_cuenta": "2.1.2.102",
        "nombre_cuenta": "SUSS a pagar",
    },
    {
        "prioridad": 52,
        "nombre": "Honorarios profesionales",
        "patrones": ["Honorarios", "HONORARIOS"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.03",
        "nombre_cuenta": "Honorarios servicios administracion",
    },

    # ══════════════════════════════════════════
    # INVERSIONES FIMA
    # ══════════════════════════════════════════
    {
        "prioridad": 60,
        "nombre": "Suscripción Fondo FIMA",
        "patrones": ["Suscripcion Fima", "SUSCRIPCION FIMA"],
        "tipo": "DEBITO",
        "codigo_cuenta": "1.1.5.102",
        "nombre_cuenta": "Fondos de Inversión",
    },
    {
        "prioridad": 61,
        "nombre": "Rescate Fondo FIMA",
        "patrones": ["Rescate Fima", "RESCATE FIMA"],
        "tipo": "CREDITO",
        "codigo_cuenta": "1.1.5.102",
        "nombre_cuenta": "Fondos de Inversión",
    },
    {
        "prioridad": 62,
        "nombre": "Plazo fijo",
        "patrones": ["Plazo Fijo", "PLAZO FIJO"],
        "tipo": None,
        "codigo_cuenta": "1.1.5.101",
        "nombre_cuenta": "Depósitos a plazo fijo",
    },

    # ══════════════════════════════════════════
    # GASTOS BANCARIOS Y COMISIONES
    # ══════════════════════════════════════════
    {
        "prioridad": 70,
        "nombre": "Comisiones bancarias",
        "patrones": [
            "Comision Servicio De Cuenta", "COMISION SERVICIO DE CUENTA",
            "Debito Comisiones Varias", "DEBITO COMISIONES VARIAS",
            "Com. Gestion Transf.fdos Entre Bcos",
            "COM. GESTION TRANSF",
        ],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.4.03",
        "nombre_cuenta": "Intereses financieros",
    },

    # ══════════════════════════════════════════
    # GASTOS CON TARJETA Y SERVICIOS
    # ══════════════════════════════════════════
    {
        "prioridad": 80,
        "nombre": "Compra con débito o tarjeta",
        "patrones": ["Compra Debito", "COMPRA DEBITO", "COMPRA CON TARJETA"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.15",
        "nombre_cuenta": "Gastos varios de administración",
    },
    {
        "prioridad": 81,
        "nombre": "Débito automático servicios",
        "patrones": ["Deb. Autom. De Serv.", "DEB. AUTOM. DE SERV."],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.18",
        "nombre_cuenta": "Servicios contratados",
    },
    {
        "prioridad": 82,
        "nombre": "Pago de servicios",
        "patrones": ["Pago De Servicios", "PAGO DE SERVICIOS"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.18",
        "nombre_cuenta": "Servicios contratados",
    },
    {
        "prioridad": 83,
        "nombre": "Pago Visa empresa",
        "patrones": ["Pago Visa Empresa", "PAGO VISA EMPRESA"],
        "tipo": "DEBITO",
        "codigo_cuenta": "5.2.15",
        "nombre_cuenta": "Gastos varios de administración",
    },

    # ══════════════════════════════════════════
    # DIFERENCIA DE CAMBIO / RECPAM
    # ══════════════════════════════════════════
    {
        "prioridad": 90,
        "nombre": "Diferencia de cambio",
        "patrones": ["Diferencia De Cambio", "DIFERENCIA DE CAMBIO"],
        "tipo": None,
        "codigo_cuenta": "5.6.01",
        "nombre_cuenta": "Diferencia de cambio",
    },

    # ══════════════════════════════════════════
    # FALLBACK — siempre aplica al final
    # ══════════════════════════════════════════
    {
        "prioridad": 999,
        "nombre": "Sin clasificar - requiere revisión manual",
        "patrones": [],
        "tipo": None,
        "codigo_cuenta": "6.0",
        "nombre_cuenta": "Transferencias bancarias transitorias",
    },
]


def clasificar_movimiento(descripcion: str, tipo_movimiento: str) -> dict:
    """
    Dado una descripción y tipo de movimiento bancario,
    retorna la regla contable que aplica.
    Siempre retorna algo — en el peor caso el fallback 6.0.
    """
    desc_upper = (descripcion or "").upper()

    for regla in sorted(REGLAS_CONTABLES, key=lambda r: r["prioridad"]):
        if not regla["patrones"]:
            continue
        if regla["tipo"] and regla["tipo"] != tipo_movimiento:
            continue
        for patron in regla["patrones"]:
            if patron.upper() in desc_upper:
                return regla

    return next(r for r in REGLAS_CONTABLES if r["prioridad"] == 999)
