# HVAC Pro — tablas P-T CoolProp

El workflow `Generar tablas CoolProp` instala CoolProp 8.0.0, genera `pt_data.js`, valida que cada curva sea creciente y guarda el archivo en la rama `main`.

Después de ejecutarlo una vez, GitHub Pages funciona desde `main / (root)` y la PWA utiliza un archivo estático local, también disponible sin conexión.

Criterios:
- presión de entrada: bar(g)
- referencia atmosférica: 1.01325 bar
- dew: Q=1
- bubble: Q=0
- resolución: 0.1 °C
