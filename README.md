# Terminal Code Editor en Python

## Descripción
Este es un editor de código/texto desarrollado en Python, versión 1.0.1. Aunque está en una etapa temprana de desarrollo, tiene como objetivo proporcionar una experiencia similar a la de nano, con la capacidad de cambiar entre dos modos: modo edición y modo comando.

## Problemas Conocidos
- Actualmente, el resaltado de sintaxis no funciona correctamente para los cierres de etiquetas.
- Al crear una nueva línea mientras se está en la última línea del archivo, hay un problema con el desplazamiento que impide que la pantalla se desplace hacia abajo.

## Modo de Comandos
El modo de comandos se activa con la combinación de teclas Ctrl + X. En este modo, puedes ejecutar varios comandos, como:
- `ins <número de línea> <texto>`: Inserta una línea con el texto especificado en la línea indicada.
- `del <número de línea>`: Elimina la línea especificada.
- `save`: Guarda el archivo.
- `find <texto>`: Busca un texto en el archivo.
- `go toline <número de línea>`: Te lleva a la línea especificada.

## Autor
- Alejandro Labannere

## Contribuir
¡Si tienes ideas para mejorar este editor, eres bienvenido a contribuir! Siéntete libre de enviar solicitudes de extracción o informar problemas.

## Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para obtener más detalles.
