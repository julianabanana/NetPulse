# ⚡ Instrucciones Rápidas - NetPulse Entrega 2

## 🎯 Paso 1: Instalar el Módulo NetPulse en Odoo

Desde la raíz del proyecto, ejecuta:

```bash
docker compose run --rm odoo odoo -d netpulse -i netpulse --stop-after-init
```

**Espera 1-2 minutos.** Verás muchos logs. Al final debe decir algo como:
```
Modules loaded.
```

## 🔄 Paso 2: Reiniciar Odoo

```bash
docker compose restart odoo
```

Espera 10 segundos.

## ✅ Paso 3: Verificar que Odoo funciona

Abre tu navegador y ve a:
```
http://localhost:8069
```

Deberías ver la interfaz de Odoo. Si pide login:
- **Usuario:** `admin`
- **Contraseña:** `admin`

Una vez dentro, ve al menú de aplicaciones y busca "NetPulse" - debería aparecer como instalado.

## 🚀 Paso 4: Iniciar el Cliente React

Abre una **nueva terminal** (CMD o WSL) y ejecuta:

```bash
cd c:\Users\AdminNuevo\Documents\INGESOFT\NetPulse\client
npm run dev
```

Verás algo como:
```
  ➜  Local:   http://localhost:5173/
```

## 🎉 Paso 5: Probar la Aplicación

1. Abre `http://localhost:5173` en tu navegador
2. Haz login con:
   - **Usuario:** `admin`
   - **Contraseña:** `admin`
3. Deberías ver el dashboard de NetPulse

---

## 🐛 Si el Cliente React da "Error de red: Failed to fetch"

Esto significa que Odoo no está respondiendo correctamente. Verifica:

### A. ¿Odoo está corriendo?
```bash
docker compose ps
```
Ambos servicios deben estar "Up".

### B. ¿Responde Odoo?
Abre en el navegador: `http://localhost:8069/web/database/selector`

Si da error 404 o no carga, Odoo no está bien configurado.

### C. ¿Está instalado NetPulse?
```bash
docker compose logs odoo | grep netpulse
```
Deberías ver líneas que digan "Loading module netpulse".

### D. Solución nuclear (si nada funciona)

```bash
# Borrar todo y empezar de cero
docker compose down -v
docker compose up -d
# Espera 30 segundos
docker compose run --rm odoo odoo -d netpulse -i netpulse --stop-after-init
docker compose restart odoo
```

---

## 📋 Checklist de Verificación

- [ ] Contenedores corriendo (`docker compose ps` muestra ambos "Up")
- [ ] Odoo responde en http://localhost:8069
- [ ] Puedes hacer login en Odoo con admin/admin
- [ ] NetPulse aparece instalado en Odoo (menú Aplicaciones)
- [ ] Cliente React corriendo en http://localhost:5173
- [ ] Login exitoso desde el cliente React
- [ ] Puedes ver la lista de dispositivos (vacía al inicio está bien)

---

## 🎬 Crear Datos de Prueba

Una vez que todo funcione, crea dispositivos desde la interfaz de Odoo o desde el cliente React:

**Desde Odoo Web (http://localhost:8069):**
1. Ve a NetPulse > Dispositivos > Crear
2. Llena: Nombre, Tipo, Criticidad
3. Guarda

**Desde el Cliente React (http://localhost:5173):**
1. Click en "+ Nuevo dispositivo"
2. Llena el formulario
3. Submit

Los datos se sincronizarán automáticamente entre ambas interfaces.

---

¿Listo? Ejecuta los pasos en orden y me dices en cuál te quedas trabado.
