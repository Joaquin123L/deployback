class SiniestroDTO:
    def __init__(self, id, fecha_hora=None):
        self.id = id
        self.fecha_hora = fecha_hora  # Nueva propiedad

    def to_dict(self):
        return {
            "id": self.id,
            "fecha_hora": self.fecha_hora,  # Incluye fecha-hora en el diccionario
        }
