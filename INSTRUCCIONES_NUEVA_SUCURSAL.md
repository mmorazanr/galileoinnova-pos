Instrucciones para Desplegar un Nuevo Restaurante
===================================================

Para conectar de manera oficial otro servidor de Comtrex (nueva sucursal) al sistema global en la nube de The Lazy Donkey, solo debes seguir esta guía de 3 sencillos pasos en la computadora principal donde este guardada la base de MS Access `CBOData_s.mdb`.

### 1. Requisitos Iniciales de la Nueva Computadora
- Microsoft Access Database Engine (el driver de Windows normal que ya deben tener para que Access funcione, usualmente incluido de fábrica).

**Ya NO hace falta instalar Python ni programar nada.**

### 2. Copiar los Archivos Esenciales
En la carpeta C:\ICOM\Database\ tienes un ejecutable empacado listo para usar (`Instalador_Ejecutable_Comtrex.zip`). En este archivo tienes:
- `agente_sync.exe` (El motor sincronizador en segundo plano, condensado en una sola app de Windows).
- `config.json` (Las llaves).

Lleva este archivo comprimido en una memoria USB al otro restaurante, extráelo preferiblemente en la ruta `C:\ICOM\Database\`.

### 3. Ajustar el Archivo config.json (CRUCIAL)
Usa el Bloc de Notas (Notepad) para editar el archivo `config.json` adentro del otro servidor recién copiado. 

Lo **único** que tienes que cambiar es la variable **"restaurant_name"**. Cambia el "The Lazy Donkey Restaurant" original al nuevo nombre para que en el panel web no se mezcle la contabilidad. Ejemplo:
```json
{
  "restaurant_name": "The Lazy Donkey Norte",
  "local_db_path": "C:\\ICOM\\Database\\CBOData_s.mdb",
  ... (deja lo demás intacto, son las credenciales a la nube MariaDB)
}
```
Si el archivo `.mdb` del segundo restaurante NO está en `C:\ICOM\Database\...`, puedes cambiar también el parametro `"local_db_path"` para indicarle al agente dónde buscar localmente en esa PC.

### 4. Ejecutar el Agente
Abre la carpeta, hazle doble-click al ejecutable `agente_sync.exe` e instalará los datos. Si quieres que arranque siempre con Windows, puedes crearle un acceso directo y arrastrarlo a la carpeta de `shell:startup` (Incio de Windows).

¡Listo! Apenas el `agente_sync.exe` arranque, la plataforma Web (index.php) en internet detectará automáticamente esta nueva sucursal y creará mágicamente su reporte con todos los sub-filtros de mesas y tickets en la zona de "Branch".
