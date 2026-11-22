from abc import ABC, abstractmethod  # Importa ABC y abstractmethod para definir clases y métodos abstractos
from datetime import datetime  # Importa datetime para marcar la hora de cada evento o error en el log
import re  # Importa re para validar formatos como el correo electrónico


# ==========================================
# 1. EXCEPCIONES PERSONALIZADAS DEL SISTEMA
# ==========================================

class ErrorSistemaFJ(Exception):
    """Excepción base para todos los errores controlados del sistema de Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL"):
        self.codigo = codigo  # Guarda un código identificador del tipo de error
        self.mensaje = mensaje  # Guarda el mensaje descriptivo del error
        super().__init__(f"[{self.codigo}] {self.mensaje}")  # Inicializa la clase base Exception


class DatoInvalidoError(ErrorSistemaFJ):
    """Se lanza cuando un dato de entrada (nombre, correo, duración, etc.) no es válido."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_DATO_INVALIDO")


class ServicioNoDisponibleError(ErrorSistemaFJ):
    """Se lanza cuando se intenta usar o reservar un servicio que no está disponible."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_SERVICIO_NO_DISPONIBLE")


class OperacionReservaError(ErrorSistemaFJ):
    """Se lanza cuando una transición de estado o regla de reserva no es permitida."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_OPERACION_RESERVA")


class CalculoInconsistenteError(ErrorSistemaFJ):
    """Se lanza cuando ocurre una inconsistencia matemática o lógica en un cálculo."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_CALCULO_INCONSISTENTE")


# ==========================================
# 2. REGISTRADOR DE EVENTOS Y ERRORES (LOG)
# ==========================================

class GestorLogs:
    """Gestiona el registro en archivo de texto plano (.log) sin usar base de datos."""

    def __init__(self, ruta_archivo: str = "software_fj_eventos.log"):
        self.ruta_archivo = ruta_archivo  # Define la ruta del archivo donde se guardarán los logs

    def registrar(self, nivel: str, detalle: str) -> None:
        """Escribe una línea con marca de tiempo en el archivo de logs."""
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Obtiene fecha y hora actual
        linea = f"{marca_tiempo} | {nivel.upper()} | {detalle}\n"  # Formatea el registro del evento
        try:
            # Abre el archivo en modo 'a' (append) con codificación UTF-8 para no borrar registros previos
            with open(self.ruta_archivo, mode="a", encoding="utf-8") as archivo:
                archivo.write(linea)  # Escribe la línea en el archivo de log
        except OSError as exc:
            # Encadena la excepción del sistema operativo si falla la escritura del archivo
            raise ErrorSistemaFJ(f"No fue posible escribir en el log '{self.ruta_archivo}': {exc}") from exc


# ==========================================
# 3. CLASE ABSTRACTA BASE Y CLASE CLIENTE
# ==========================================

class EntidadBase(ABC):
    """Clase abstracta que representa entidades generales dentro del sistema."""

    def __init__(self, id_entidad: str):
        if not isinstance(id_entidad, str) or not id_entidad.strip():  # Verifica que el ID no esté vacío
            raise DatoInvalidoError("El identificador de la entidad debe ser un texto no vacío.")
        self._id = id_entidad.strip()  # Almacena el ID normalizado sin espacios extremos

    @property
    def id_entidad(self) -> str:
        """Devuelve el identificador de la entidad de solo lectura."""
        return self._id

    @abstractmethod
    def resumen(self) -> str:
        """Método abstracto que cada entidad concreta debe implementar."""
        pass


class Cliente(EntidadBase):
    """Representa un cliente con encapsulación de datos personales y validaciones estrictas."""

    def __init__(self, id_cliente: str, nombre: str, correo: str, documento: str):
        super().__init__(id_cliente)  # Valida y asigna el ID heredado de EntidadBase
        self.nombre = nombre  # Invoca el setter de nombre para validar
        self.correo = correo  # Invoca el setter de correo para validar
        self.documento = documento  # Invoca el setter de documento para validar

    @property
    def nombre(self) -> str:
        return self._nombre  # Retorna el atributo encapsulado _nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 3:  # Valida longitud mínima del nombre
            raise DatoInvalidoError("El nombre del cliente debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()  # Guarda el nombre limpio

    @property
    def correo(self) -> str:
        return self._correo  # Retorna el atributo encapsulado _correo

    @correo.setter
    def correo(self, valor: str) -> None:
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"  # Expresión regular básica para validar correo
        if not isinstance(valor, str) or not re.match(patron, valor.strip()):
            raise DatoInvalidoError(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()  # Guarda el correo en minúsculas

    @property
    def documento(self) -> str:
        return self._documento  # Retorna el atributo encapsulado _documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip().isdigit() or len(valor.strip()) < 5:
            raise DatoInvalidoError("El documento debe contener solo dígitos y tener al menos 5 caracteres.")
        self._documento = valor.strip()  # Guarda el documento validado

    def resumen(self) -> str:
        """Implementación del método abstracto resumen() para un cliente."""
        return f"Cliente[{self._id}] {self._nombre} | Doc: {self._documento} | Correo: {self._correo}"


# ==========================================
# 4. JERARQUÍA DE SERVICIOS Y POLIMORFISMO
# ==========================================

class Servicio(EntidadBase):
    """Clase abstracta base para los servicios ofrecidos por Software FJ."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True):
        super().__init__(id_servicio)  # Inicializa el ID de la entidad
        if not isinstance(nombre, str) or not nombre.strip():  # Valida el nombre del servicio
            raise DatoInvalidoError("El nombre del servicio no puede estar vacío.")
        if not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:  # Valida tarifa positiva
            raise DatoInvalidoError("La tarifa base debe ser un número mayor que cero.")
        self.nombre = nombre.strip()  # Asigna el nombre del servicio
        self.tarifa_base = float(tarifa_base)  # Convierte y guarda la tarifa base como flotante
        self.disponible = bool(disponible)  # Indica si el servicio admite reservas

    def verificar_disponibilidad(self) -> None:
        """Verifica que el servicio esté disponible o lanza ServicioNoDisponibleError."""
        if not self.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self.nombre}' ({self._id}) no está disponible.")

    @abstractmethod
    def validar_parametros(self, cantidad: int) -> None:
        """Valida la cantidad/duración específica según el tipo de servicio."""
        pass

    @abstractmethod
    def describir(self) -> str:
        """Describe las características particulares del servicio."""
        pass

    def calcular_costo(
        self,
        cantidad: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.19,
    ) -> float:
        """
        Calcula el costo total soportando variantes mediante argumentos opcionales
        (descuento e impuesto), simulando sobrecarga de métodos en Python.
        """
        self.validar_parametros(cantidad)  # Valida primero la cantidad o duración solicitada
        if not (0.0 <= descuento_pct < 100.0):  # Verifica que el porcentaje de descuento sea válido
            raise DatoInvalidoError("El descuento porcentual debe estar entre 0 y 99.9.")
        if impuesto_pct < 0.0:  # Verifica que el impuesto no sea negativo
            raise DatoInvalidoError("El impuesto porcentual no puede ser negativo.")

        subtotal = self.tarifa_base * cantidad  # Calcula el subtotal antes de descuentos e impuestos
        con_descuento = subtotal * (1.0 - descuento_pct / 100.0)  # Aplica el porcentaje de descuento
        total = con_descuento * (1.0 + impuesto_pct / 100.0)  # Aplica el impuesto correspondiente

        if total < 0:  # Comprueba que el resultado final no sea inconsistente
            raise CalculoInconsistenteError("El costo calculado resultó negativo.")
        return round(total, 2)  # Redondea el total a dos decimales

    def resumen(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"  # Texto legible del estado
        return f"Servicio[{self._id}] {self.nombre} | Tarifa: ${self.tarifa_base:,.2f} | {estado}"


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas (cantidad = horas de uso)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, capacidad: int, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_base, disponible)  # Llama al constructor de Servicio
        if not isinstance(capacidad, int) or capacidad <= 0:  # Valida capacidad positiva de la sala
            raise DatoInvalidoError("La capacidad de la sala debe ser un entero mayor que cero.")
        self.capacidad = capacidad  # Guarda el número máximo de personas

    def validar_parametros(self, cantidad: int) -> None:
        """La reserva de sala exige entre 1 y 12 horas continuas."""
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or not (1 <= cantidad <= 12):
            raise DatoInvalidoError("Para reserva de sala, las horas deben ser un entero entre 1 y 12.")

    def describir(self) -> str:
        return f"Sala '{self.nombre}' (capacidad: {self.capacidad} personas, tarifa/hora: ${self.tarifa_base:,.2f})."


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos (cantidad = días de alquiler)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, codigo_activo: str, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_base, disponible)  # Inicializa atributos comunes
        if not isinstance(codigo_activo, str) or not codigo_activo.strip():  # Valida código de inventario
            raise DatoInvalidoError("El código del equipo no puede estar vacío.")
        self.codigo_activo = codigo_activo.strip()  # Guarda el código del equipo

    def validar_parametros(self, cantidad: int) -> None:
        """El alquiler de equipos exige entre 1 y 30 días."""
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or not (1 <= cantidad <= 30):
            raise DatoInvalidoError("Para alquiler de equipo, los días deben ser un entero entre 1 y 30.")

    def describir(self) -> str:
        return f"Equipo '{self.nombre}' [Activo {self.codigo_activo}] (tarifa/día: ${self.tarifa_base:,.2f})."


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas (cantidad = sesiones de asesoría)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, especialidad: str, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_base, disponible)  # Inicializa atributos base
        if not isinstance(especialidad, str) or not especialidad.strip():  # Valida especialidad
            raise DatoInvalidoError("La especialidad de la asesoría no puede estar vacía.")
        self.especialidad = especialidad.strip()  # Guarda el área de especialidad

    def validar_parametros(self, cantidad: int) -> None:
        """Las asesorías especializadas requieren entre 1 y 20 sesiones."""
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or not (1 <= cantidad <= 20):
            raise DatoInvalidoError("Para asesoría especializada, las sesiones deben ser un entero entre 1 y 20.")

    def describir(self) -> str:
        return f"Asesoría en {self.especialidad} - '{self.nombre}' (tarifa/sesión: ${self.tarifa_base:,.2f})."


# ==========================================
# 5. CLASE RESERVA Y GESTOR DEL SISTEMA
# ==========================================

class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado, con gestión de ciclo de vida."""

    ESTADOS_VALIDOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA")  # Tupla de estados permitidos

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: int,
        descuento_pct: float = 0.0,
    ):
        super().__init__(id_reserva)  # Valida y asigna el ID de la reserva
        if not isinstance(cliente, Cliente):  # Verifica que se pase una instancia válida de Cliente
            raise DatoInvalidoError("La reserva requiere un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):  # Verifica que se pase una instancia válida de Servicio
            raise DatoInvalidoError("La reserva requiere un objeto Servicio válido.")

        servicio.verificar_disponibilidad()  # Lanza ServicioNoDisponibleError si el servicio no está activo
        self.cliente = cliente  # Asocia el cliente a la reserva
        self.servicio = servicio  # Asocia el servicio a la reserva
        self.duracion = duracion  # Guarda la duración (horas, días o sesiones)
        self.estado = "PENDIENTE"  # Toda reserva nueva inicia en estado PENDIENTE
        self.total_estimado = servicio.calcular_costo(duracion, descuento_pct=descuento_pct)  # Calcula costo inicial

    def confirmar(self) -> None:
        """Confirma una reserva pendiente o lanza OperacionReservaError si no es posible."""
        if self.estado == "CANCELADA":
            raise OperacionReservaError(f"No se puede confirmar la reserva {self._id} porque está cancelada.")
        if self.estado == "CONFIRMADA":
            raise OperacionReservaError(f"La reserva {self._id} ya se encuentra confirmada.")
        self.servicio.verificar_disponibilidad()  # Revalida disponibilidad antes de confirmar
        self.estado = "CONFIRMADA"  # Actualiza el estado a CONFIRMADA

    def cancelar(self) -> None:
        """Cancela una reserva activa o lanza OperacionReservaError si ya está cancelada."""
        if self.estado == "CANCELADA":
            raise OperacionReservaError(f"La reserva {self._id} ya estaba cancelada.")
        self.estado = "CANCELADA"  # Actualiza el estado a CANCELADA

    def procesar(self) -> str:
        """Procesa una reserva confirmada y genera un comprobante textual."""
        if self.estado != "CONFIRMADA":
            raise OperacionReservaError(
                f"Solo se pueden procesar reservas CONFIRMADAS. Estado actual de {self._id}: {self.estado}."
            )
        return (
            f"Reserva {self._id} procesada para {self.cliente.nombre} | "
            f"Servicio: {self.servicio.nombre} | Duración: {self.duracion} | Total: ${self.total_estimado:,.2f}"
        )

    def resumen(self) -> str:
        return (
            f"Reserva[{self._id}] Estado: {self.estado} | Cliente: {self.cliente.nombre} | "
            f"Servicio: {self.servicio.nombre} | Total: ${self.total_estimado:,.2f}"
        )


class GestorSoftwareFJ:
    """Coordina listas internas de clientes, servicios y reservas sin usar base de datos."""

    def __init__(self, gestor_logs: GestorLogs):
        self.clientes: list[Cliente] = []  # Lista interna de clientes registrados
        self.servicios: list[Servicio] = []  # Lista interna de servicios disponibles o registrados
        self.reservas: list[Reserva] = []  # Lista interna de reservas creadas
        self.logs = gestor_logs  # Referencia al gestor de logs en archivo

    def registrar_cliente(self, id_cliente: str, nombre: str, correo: str, documento: str) -> Cliente:
        """Registra un cliente validado en la lista interna."""
        if any(c.id_entidad == id_cliente for c in self.clientes):  # Evita duplicados por ID
            raise DatoInvalidoError(f"Ya existe un cliente con el ID '{id_cliente}'.")
        cliente = Cliente(id_cliente, nombre, correo, documento)  # Construye y valida el objeto Cliente
        self.clientes.append(cliente)  # Agrega el cliente a la lista interna
        self.logs.registrar("INFO", f"Cliente registrado: {cliente.resumen()}")  # Registra el evento exitoso
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        """Agrega una instancia de Servicio (o subclase) a la lista interna."""
        if not isinstance(servicio, Servicio):  # Verifica tipo correcto
            raise DatoInvalidoError("Solo se pueden registrar objetos de tipo Servicio.")
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):  # Evita duplicados por ID
            raise DatoInvalidoError(f"Ya existe un servicio con el ID '{servicio.id_entidad}'.")
        self.servicios.append(servicio)  # Agrega el servicio a la lista interna
        self.logs.registrar("INFO", f"Servicio registrado: {servicio.resumen()}")  # Registra el evento
        return servicio

    def buscar_cliente(self, id_cliente: str) -> Cliente:
        """Busca un cliente por ID o lanza DatoInvalidoError encadenado si no existe."""
        try:
            for cliente in self.clientes:
                if cliente.id_entidad == id_cliente:
                    return cliente
            raise ValueError(f"ID de cliente '{id_cliente}' no encontrado.")  # Error interno de búsqueda
        except ValueError as err:
            # Encadena la excepción original (ValueError) dentro de una excepción del dominio
            raise DatoInvalidoError(f"No se pudo localizar el cliente '{id_cliente}'.") from err

    def buscar_servicio(self, id_servicio: str) -> Servicio:
        """Busca un servicio por ID o lanza DatoInvalidoError encadenado si no existe."""
        try:
            for servicio in self.servicios:
                if servicio.id_entidad == id_servicio:
                    return servicio
            raise ValueError(f"ID de servicio '{id_servicio}' no encontrado.")  # Error interno de búsqueda
        except ValueError as err:
            raise DatoInvalidoError(f"No se pudo localizar el servicio '{id_servicio}'.") from err

    def crear_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion: int,
        descuento_pct: float = 0.0,
    ) -> Reserva:
        """Crea y almacena una reserva validando cliente, servicio y duración."""
        if any(r.id_entidad == id_reserva for r in self.reservas):  # Evita duplicar ID de reserva
            raise OperacionReservaError(f"Ya existe una reserva con el ID '{id_reserva}'.")
        cliente = self.buscar_cliente(id_cliente)  # Obtiene el cliente o lanza error encadenado
        servicio = self.buscar_servicio(id_servicio)  # Obtiene el servicio o lanza error encadenado
        reserva = Reserva(id_reserva, cliente, servicio, duracion, descuento_pct=descuento_pct)  # Crea reserva
        self.reservas.append(reserva)  # Guarda la reserva en la lista interna
        self.logs.registrar("INFO", f"Reserva creada: {reserva.resumen()}")  # Registra en log
        return reserva


# ==========================================
# 6. SIMULACIÓN SECUENCIAL DE 12 OPERACIONES
# ==========================================

def ejecutar_simulacion() -> None:
    """Ejecuta al menos 10 operaciones válidas e inválidas demostrando robustez y continuidad."""
    gestor_logs = GestorLogs("software_fj_eventos.log")  # Inicializa el archivo de logs
    sistema = GestorSoftwareFJ(gestor_logs)  # Inicializa el gestor en memoria sin base de datos
    gestor_logs.registrar("INICIO", "Iniciando simulación de 12 operaciones para Software FJ.")

    # Lista de operaciones secuenciales: (etiqueta, función lambda que ejecuta la operación)
    operaciones = [
        # 1. Cliente válido
        ("Op 1 - Cliente válido", lambda: sistema.registrar_cliente("C01", "Narlis Orozco", "narlis@ejemplo.com", "1082999111")),
        # 2. Cliente inválido (correo mal formado -> DatoInvalidoError)
        ("Op 2 - Cliente correo inválido", lambda: sistema.registrar_cliente("C02", "Carlos Ruiz", "correo-no-valido", "1082999222")),
        # 3. Servicio válido: Reserva de sala
        ("Op 3 - Servicio Sala válido", lambda: sistema.registrar_servicio(ReservaSala("S01", "Sala Conferencias A", 80000, 12, True))),
        # 4. Servicio válido: Alquiler de equipo
        ("Op 4 - Servicio Equipo válido", lambda: sistema.registrar_servicio(AlquilerEquipo("S02", "Laptop Dev i7", 45000, "EQ-104", True))),
        # 5. Servicio válido: Asesoría especializada (no disponible para probar fallo de reserva)
        ("Op 5 - Servicio Asesoría no disp.", lambda: sistema.registrar_servicio(AsesoriaEspecializada("S03", "Arquitectura Cloud", 150000, "Cloud", False))),
        # 6. Servicio inválido (tarifa negativa -> DatoInvalidoError)
        ("Op 6 - Servicio tarifa inválida", lambda: sistema.registrar_servicio(ReservaSala("S04", "Sala Beta", -20000, 8, True))),
        # 7. Reserva exitosa con descuento opcional (sobrecarga por parámetros por defecto)
        ("Op 7 - Reserva exitosa sala", lambda: sistema.crear_reserva("R01", "C01", "S01", 3, descuento_pct=10.0)),
        # 8. Confirmación y procesamiento exitoso de la reserva R01
        ("Op 8 - Confirmar y procesar R01", lambda: (sistema.reservas[0].confirmar(), sistema.reservas[0].procesar())[1]),
        # 9. Reserva fallida por servicio no disponible (ServicioNoDisponibleError)
        ("Op 9 - Reserva servicio no disp.", lambda: sistema.crear_reserva("R02", "C01", "S03", 2)),
        # 10. Reserva fallida por duración inválida (DatoInvalidoError)
        ("Op 10 - Reserva duración inválida", lambda: sistema.crear_reserva("R03", "C01", "S02", 50)),
        # 11. Operación no permitida: intentar confirmar de nuevo R01 (OperacionReservaError)
        ("Op 11 - Reconfirmar R01 inválida", lambda: sistema.reservas[0].confirmar()),
        # 12. Reserva adicional exitosa para asesoría habilitada tras activar disponibilidad
        ("Op 12 - Activar S03 y reservar", lambda: (setattr(sistema.buscar_servicio("S03"), "disponible", True), sistema.crear_reserva("R04", "C01", "S03", 2))[1]),
    ]

    for nombre_op, accion in operaciones:
        print(f"\n--- Ejecutando {nombre_op} ---")
        try:
            resultado = accion()  # Intenta ejecutar la operación secuencial
        except ErrorSistemaFJ as error_controlado:
            # Captura errores propios del sistema y los registra en el log sin detener el programa
            print(f"  [ERROR CONTROLADO] {error_controlado}")
            if error_controlado.__cause__:
                print(f"  [CAUSA ENCADENADA] {error_controlado.__cause__}")
            gestor_logs.registrar("ERROR", f"{nombre_op} -> {error_controlado}")
        except Exception as error_inesperado:
            # Captura de respaldo ante cualquier excepción no prevista
            print(f"  [ERROR INESPERADO] {error_inesperado}")
            gestor_logs.registrar("CRITICO", f"{nombre_op} -> {error_inesperado}")
        else:
            # Se ejecuta solo si 'accion()' terminó sin lanzar excepciones
            print(f"  [OK] Resultado: {resultado.resumen() if hasattr(resultado, 'resumen') else resultado}")
            gestor_logs.registrar("EXITO", f"{nombre_op} completada correctamente.")
        finally:
            # Bloque de cierre que siempre se ejecuta por cada operación
            print("  [FINALLY] Paso de verificación de estabilidad completado.")

    gestor_logs.registrar("FIN", "Simulación finalizada. Sistema estable y operativo.")


if __name__ == "__main__":
    ejecutar_simulacion()  # Ejecuta la simulación al correr el archivo directamente