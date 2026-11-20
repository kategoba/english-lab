# English Lab — notas del proyecto

**Lema:** Practice. Measure. Predict. Improve.
**Frase:** "What gets measured, gets improved."

App personal para aprender inglés que Kate construye, usa a diario desde el celular y muestra en LinkedIn y GitHub con sus resultados reales. No es para vender.

## Reglas del proyecto
- Costo $0: nada de servicios pagados.
- Resultados reales, nunca inventados.
- Kate debe entender y poder explicar cada parte.
- Documentar el proceso: capturas, versiones y decisiones.

## Cómo funciona
- Se desarrolla en el PC y se publica gratis en internet desde la primera versión.
- La práctica diaria es desde el celular: diseño pensado para pantalla pequeña.
- Datos en una base de datos gratuita en la nube y acceso con clave.
- Colores: tonos de azul (marino `#0B2545`, rey `#1D4ED8`, medio `#3B82F6`, cielo `#93C5FD`, hielo `#DBEAFE`, fondo `#F5F9FF`). Verde y rojo solo para aciertos y errores.

## Etapas
1. **La base:** guardar palabras, repaso con repetición espaciada, audio (escuchar, dictado y pronunciación) y tablero de progreso. Desde aquí se guarda el detalle de cada repaso: fecha, si la recordó, tiempo de respuesta, tipo de ejercicio y días desde el último repaso.
2. **Analítica:** constancia, palabras que más se olvidan y tiempo de estudio.
3. **Machine learning:** predecir qué palabras va a olvidar y mostrarlas en el celular.

## Alertas diarias por Telegram (gratis)
- **7:00 a. m.:** Pronóstico de memoria (palabras estables, en riesgo y a punto de olvidarse, más una recomendación).
- **8:00 p. m.:** Reporte del laboratorio (palabras repasadas, comprensión auditiva, meta del día y la frase).
- Estilo propio de laboratorio de datos, no como Duolingo.

## GitHub
- Cuenta con el correo personal de Kate.
- Se sube: código, gráficos en el README, análisis, datos de ejemplo y una **copia exportada** de la base de datos real (sin datos personales aparte del nombre). Nunca el archivo de la base de datos en uso.

## Inglés
- Nivel inicial estimado: A2. Pendiente medirlo con el examen gratuito EF SET y repetirlo cada 2 o 3 meses.
- Meta final: una certificación de inglés publicada junto con el proyecto.

## LinkedIn
Inicio de la publicación: "Siempre digo que lo que no se mide no se puede controlar. Así que decidí medir mi propio aprendizaje de inglés..."

## Archivos
- `app.py`: lo que se ve en pantalla (la "vitrina").
- `logica.py`: las reglas de repaso y la racha (el "cerebro").
- `datos.py`: guarda y lee palabras y repasos (la "bodega"). Es el único archivo que cambia al pasar a la nube.
- `.streamlit/config.toml`: los colores azules.
- `requirements.txt`: las herramientas que necesita la app.
- `.gitignore`: lo que no se sube a GitHub (la base de datos en uso).
- `Abrir English Lab.bat`: doble clic para abrir la app en el PC.

## Bitácora
- **19 nov 2026 — Versión 1 en el PC:** agregar palabras, repasar con repetición espaciada, escuchar en voz normal y lenta, lista de palabras, progreso (guardadas, aprendidas, aciertos, días seguidos y gráfico) y exportar CSV. Probada en tamaño celular.
- **19 nov 2026 — Preparada para internet:** `datos.py` funciona con SQLite en el PC y con PostgreSQL en la nube (usando SQLAlchemy). La app pide clave cuando está en internet. Git instalado.
- **19 nov 2026 — ¡En internet!** Código en GitHub, base de datos en Neon y app publicada en Streamlit Community Cloud.

## Siguientes pasos
1. Dictado (escuchar y escribir).
2. Pronunciación (hablar con el micrófono).
3. Publicarla en internet con base de datos en la nube y clave, para usarla desde el celular.
4. Alertas por Telegram.

## Pendientes
- [ ] Hacer el examen EF SET y anotar nivel y puntaje.
- [x] Crear la cuenta de GitHub con el correo personal (19 nov 2026): usuario **kategoba** — github.com/kategoba
- [ ] Completar el perfil de GitHub y activar la verificación en dos pasos.
- [x] Configurar Git con el nombre y el correo privado de GitHub.
- [x] Subir English Lab a GitHub (19 nov 2026): github.com/kategoba/english-lab
- [x] Crear la base de datos gratuita en la nube (Neon): proyecto english-lab, región AWS US East 2 (Ohio). Contraseña cambiada después de quedar expuesta.
- [x] Publicar la app en Streamlit Community Cloud con los secretos DATABASE_URL y APP_PASSWORD (19 nov 2026).
- [x] Probar la app publicada (19 nov 2026): primera palabra real "I want to see you", repasada y guardada en Neon. ¡Funciona!
- [x] Abrirla en el celular (19 nov 2026): probada y funcionando.
- [x] Link de la app en el README: https://hl67p8jyjexmyqeevtkztt.streamlit.app/
- [ ] Cerrar el Bloc de notas sin guardar.
- [ ] Activar la verificación en dos pasos en GitHub.

## Pendientes fuera del proyecto
- [ ] Ejercicio de la lección 1 de Python (tarifa por hora en dólares y pesos).
- [ ] Enviar a sistemas el mensaje para reinstalar Survey123.
- [x] Instalar Streamlit y pandas.
- [x] Crear esta carpeta.
