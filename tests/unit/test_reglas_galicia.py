from app.modules.banking.reglas_galicia import clasificar_movimiento


def test_impuesto_debito_ley():
    assert clasificar_movimiento("Imp. Deb. Ley 25413 Gral.", "DEBITO")["codigo_cuenta"] == "5.5.02"

def test_impuesto_credito_ley():
    assert clasificar_movimiento("Imp. Cre. Ley 25413", "DEBITO")["codigo_cuenta"] == "1.1.3.401"

def test_iibb_sircreb():
    assert clasificar_movimiento("Ing. Brutos S/ Cred", "DEBITO")["codigo_cuenta"] == "1.1.3.204"

def test_iibb_general():
    assert clasificar_movimiento("Imp. Ing. Brutos", "DEBITO")["codigo_cuenta"] == "5.5.01"

def test_percepcion_iva():
    assert clasificar_movimiento("Percep. Iva", "DEBITO")["codigo_cuenta"] == "1.1.3.106"

def test_iva_bancario():
    assert clasificar_movimiento("Iva", "DEBITO")["codigo_cuenta"] == "2.1.3.101"

def test_percepcion_rg():
    assert clasificar_movimiento("Percepcion Rg 5617/24", "DEBITO")["codigo_cuenta"] == "1.1.3.205"

def test_sellos():
    assert clasificar_movimiento("Impuesto De Sellos", "DEBITO")["codigo_cuenta"] == "5.5.04"

def test_intereses_saldos():
    assert clasificar_movimiento("Intereses Sobre Saldos Deudores", "DEBITO")["codigo_cuenta"] == "5.4.02"

def test_afip():
    assert clasificar_movimiento("Transf. Afip", "DEBITO")["codigo_cuenta"] == "5.4.01"

def test_transferencia_cliente():
    assert clasificar_movimiento("Transferencia De Terceros", "CREDITO")["codigo_cuenta"] == "4.1.05"

def test_coelsa():
    assert clasificar_movimiento("Credito Transferencia Coelsa", "CREDITO")["codigo_cuenta"] == "4.1.05"

def test_echeq():
    assert clasificar_movimiento("G.de Echeq   Q01188004", "CREDITO")["codigo_cuenta"] == "4.1.05"

def test_comext():
    assert clasificar_movimiento("Comext.orden De Pago", "CREDITO")["codigo_cuenta"] == "4.2.01"

def test_proveedor_trf():
    assert clasificar_movimiento("Trf Inmed Proveed", "DEBITO")["codigo_cuenta"] == "5.1.01"

def test_proveedor_transf():
    assert clasificar_movimiento("Transf. A Terceros", "DEBITO")["codigo_cuenta"] == "5.1.01"

def test_sueldos():
    assert clasificar_movimiento("Servicio Acreditamiento De Haberes", "DEBITO")["codigo_cuenta"] == "5.2.01"

def test_fima_suscripcion():
    assert clasificar_movimiento("Suscripcion Fima", "DEBITO")["codigo_cuenta"] == "1.1.5.102"

def test_fima_rescate():
    assert clasificar_movimiento("Rescate Fima", "CREDITO")["codigo_cuenta"] == "1.1.5.102"

def test_comisiones():
    assert clasificar_movimiento("Comision Servicio De Cuenta", "DEBITO")["codigo_cuenta"] == "5.4.03"

def test_debito_comisiones():
    assert clasificar_movimiento("Debito Comisiones Varias", "DEBITO")["codigo_cuenta"] == "5.4.03"

def test_compra_debito():
    assert clasificar_movimiento("Compra Debito", "DEBITO")["codigo_cuenta"] == "5.2.15"

def test_deb_autom():
    assert clasificar_movimiento("Deb. Autom. De Serv.", "DEBITO")["codigo_cuenta"] == "5.2.18"

def test_pago_servicios():
    assert clasificar_movimiento("Pago De Servicios", "DEBITO")["codigo_cuenta"] == "5.2.18"

def test_visa():
    assert clasificar_movimiento("Pago Visa Empresa", "DEBITO")["codigo_cuenta"] == "5.2.15"

def test_fallback():
    assert clasificar_movimiento("Movimiento desconocido XYZ 999", "DEBITO")["codigo_cuenta"] == "6.0"

def test_case_insensitive():
    assert clasificar_movimiento("IMP. DEB. LEY 25413 GRAL.", "DEBITO")["codigo_cuenta"] == "5.5.02"

def test_descripcion_vacia():
    assert clasificar_movimiento("", "DEBITO")["codigo_cuenta"] == "6.0"

def test_descripcion_none():
    assert clasificar_movimiento(None, "DEBITO")["codigo_cuenta"] == "6.0"
