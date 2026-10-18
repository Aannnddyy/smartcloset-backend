# SmartCloset API

Backend para la digitalización y gestión de armarios personales desarrollado con Python y Django REST Framework.

El objetivo del proyecto es resolver el principal problema de las aplicaciones de armario digital: la fricción que supone tener que hacer fotos de catálogo a cada prenda a mano. La plataforma está pensada para automatizar la entrada de ropa (mediante importación por enlace de tienda o procesado de imagen) y servir como base para una futura aplicación móvil.

## Estado del proyecto

El backend se encuentra actualmente en desarrollo activo.

Funcionalidades implementadas:
- Arquitectura modular en Django con endpoints RESTful (CRUD completo para prendas).
- Aislamiento de datos por usuario (`request.user`) y control de permisos en API.
- Modelado de prendas con categorías, marcas, precios y metadatos de uso.
- Configuración para subida y almacenamiento de archivos multimedia.

Próximos pasos:
- Integración de `rembg` para recorte automático de fondos al subir fotos.
- Servicio de scraping para extraer datos y fotos directamente pegando la URL de una tienda.
- Perspectiva bifacial (vista frontal y trasera) para cada prenda.
- Asistente de estilismo semanal contextualizado con LLM (agenda personal y previsión meteorológica).

## Stack técnico

- Lenguaje: Python 3.12+
- Framework: Django 5+
- API: Django REST Framework
- Base de datos: SQLite en local (con vistas a migrar a PostgreSQL)
- Multimedia: Pillow (manejo de imágenes)

## Puesta en marcha en local

1. Clonar el repositorio y entrar en el directorio:
   git clone https://github.com/TU_USUARIO/smartcloset-backend.git
   cd smartcloset-backend

2. Crear y activar el entorno virtual:
   python3 -m venv .venv
   source .venv/bin/activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Ejecutar migraciones y arrancar el servidor:
   python manage.py migrate
   python manage.py runserver

La API queda disponible en http://127.0.0.1:8000/api/clothes/ y el panel de administración en http://127.0.0.1:8000/admin/.