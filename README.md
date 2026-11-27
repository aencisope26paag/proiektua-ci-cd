# LoL Tooltip Inspector

[![CI](https://github.com/aencisope26paag/proiektua-ci-cd/actions/workflows/ci.yml/badge.svg)](https://github.com/aencisope26paag/proiektua-ci-cd/actions)

## Enunciado

**LoL Tooltip Inspector** web aplikazio bat da, League of Legends-eko edozein txapeldunen gaitasunak modu argi eta bisualean kontsultatzeko. Jokoaren tooltip-ak irakurtzeko zailak dira, testua, zifrak eta eskalatzeak nahasten baitituzte; aplikazioak informazioa antolatzen du eta eskalatzeak (AD, AP, bizitza, armadura...) kolore eta ikonoen bidez nabarmentzen ditu.

Funtzionalitate nagusiak: txapeldunen bilaketa, hizkuntza aukeratzea (gaztelania eta ingelesa), joko-bertsioaren (patch) bistaratzea eta gaitasun bakoitzaren datuak (deskribapena, hozte-denbora, kostua eta mailaka balioak).

Teknologiak: **Python** backend-a (`http.server`, REST API eta cachea), **HTML/CSS/JavaScript** frontend-a, **pytest** eta **Node** testak, kodearen kudeaketa **GitHub**-en (adar eta Pull Request-ekin), eta **GitHub Actions** bidezko CI/CD pipeline-a: testak push eta merge guztietan exekutatzen dira, hutsegiteak badaude integrazioa blokeatzen da, eta `main` adarrean **Docker** irudia sortu, **Docker Hub**-era igo eta urruneko zerbitzari batean zabaltzen da.

## Ejecutar en local

Requisitos: Python 3.10 o superior.

```bash
python server.py
```

Abre http://localhost:8000.

## Flujo de trabajo (Git)

- `main`: rama estable. Está protegida: no se hace push directo, solo merge de Pull Requests con el CI en verde.
- `feature/<nombre>`: una rama por cada cambio (por ejemplo `feature/tests-backend`).
- Pasos: crear rama → commits → push → Pull Request hacia `main` → CI en verde → merge.
- Mensajes de commit en imperativo y cortos: `Añadir tests del servidor`.

## Estructura

```
.
├── server.py            # backend (API + archivos estáticos)
├── index.html           # interfaz
├── app.js               # lógica del frontend
├── style.css
├── icons/               # iconos de estadísticas
├── requirements-dev.txt # dependencias de desarrollo (pytest)
└── README.md
```

Las carpetas de tests, el Dockerfile y el workflow de CI se irán añadiendo en los siguientes pasos.
