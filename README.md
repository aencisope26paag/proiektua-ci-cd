# LoL Tooltip Inspector

Aplicación web local para consultar las habilidades de los campeones de League of Legends, inspirada en
los tooltips ampliados del juego (tecla `Shift`). Muestra enfriamiento, coste, descripción, notas y un
desglose de fórmulas de escalado con código de colores por estadística, distinguiendo valores
**base**, **adicionales (bonus)**, **totales**, **máximos** y **faltantes**.

> Proyecto no oficial. No está afiliado ni respaldado por Riot Games. League of Legends y los recursos del
> juego son propiedad de Riot Games, Inc.

## Cómo funciona

```
Navegador (app.js) ──► Servidor Python (server.py) ──► CommunityDragon  (datos del juego, parche actual)
  tarjetas y fórmulas     API propia: /api/...           Meraki Analytics (respaldo)
```

El servidor descarga el `.bin.json` de cada campeón (cifras y fórmulas) y la plantilla de texto de
CommunityDragon, las combina en `gamedata.py` y devuelve un JSON normalizado, con caché en memoria.

### API del servidor

| Ruta | Descripción |
|---|---|
| `GET /api/list?lang=en\|es` | Lista de campeones |
| `GET /api/champion/<alias>_<id>?lang=en\|es` | Habilidades de un campeón |
| `GET /api/icons` | Iconos disponibles en `icons/` |
| `GET /api/version` | Parche actual |
| `GET /api/debug/<id>` | Textos crudos de CommunityDragon (diagnóstico) |

## Ejecutar

```bash
python server.py        # http://localhost:8000
```

Requiere Python 3.9 o superior. No necesita instalar paquetes.

## Estructura

```
server.py      servidor HTTP, caché y rutas de la API
gamedata.py    lector de datos del juego: fórmulas, variables @...@ y tabla de escalados
index.html, app.js, style.css    interfaz
icons/         iconos de estadísticas
```

## Pruebas, CI/CD y Docker

_(se documentan a medida que se añaden: tests con pytest, GitHub Actions, imagen Docker.)_
