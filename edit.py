# Autor: Alejandro Labannere
# Fecha: 13/02/2024
# Version 1.1

import argparse
import curses
import os  # Agrega la importación del módulo os
import re
import curses.ascii
from commands import process_command  # Importa la función desde el archivo commands.py
from syntax_rules import HTML_KEYWORDS, PYTHON_KEYWORDS  # Importa las reglas de resaltado


class Buffer:
    def __init__(self, lines):
        self.lines = lines

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    @property
    def bottom(self):
        return len(self) - 1

    def insert(self, cursor, string):
        row, col = cursor.row, cursor.col
        current = self.lines.pop(row)
        new = current[:col] + string + current[col:]
        self.lines.insert(row, new)

    def split(self, cursor):
        row, col = cursor.row, cursor.col
        current = self.lines.pop(row)
        self.lines.insert(row, current[:col])
        self.lines.insert(row + 1, current[col:])

    def delete(self, cursor):
        row, col = cursor.row, cursor.col
        if 0 <= row < len(self.lines) and 0 <= col <= len(self.lines[row]):
            current = self.lines.pop(row)
            if col < len(current):
                new = current[:col] + current[col + 1:]
                self.lines.insert(row, new)
            elif row < len(self.lines):
                next_line = self.lines.pop(row)
                self.lines.insert(row, current + next_line)


class Cursor:
    def __init__(self, row=0, col=0, col_hint=None):
        self.row = row
        self._col = col
        self._col_hint = col if col_hint is None else col_hint

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_hint = col

    def _clamp_col(self, buffer):
        self._col = min(self._col_hint, len(buffer[self.row]))

    def up(self, buffer):
        if self.row > 0:
            self.row -= 1
            self._clamp_col(buffer)

    def down(self, buffer):
        if self.row < len(buffer) - 1:
            self.row += 1
            self._clamp_col(buffer)

    def left(self, buffer):
        if self.col > 0:
            self.col -= 1
        elif self.row > 0:
            self.row -= 1
            self.col = len(buffer[self.row])

    def right(self, buffer):
        if self.col < len(buffer[self.row]):
            self.col += 1
        elif self.row < len(buffer) - 1:
            self.row += 1
            self.col = 0


class Window:
    def __init__(self, filename, n_rows, n_cols, row=0, col=0):
        self.filename = filename
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row = row
        self.col = col
        # AGREGADO
        self.show_command_input = False  # Flag para mostrar u ocultar el input de comando
        self.command_input = ''  # Para almacenar el texto ingresado en el textbox

    def translate_cursor(self, cursor):
        row_offset = cursor.row - self.row  # Ajustar el offset del cursor visual
        col_offset = cursor.col - self.col
        return row_offset, max(col_offset, 0)

    @property
    def bottom(self):
        return self.row + self.n_rows

    def up(self, cursor):
        if cursor.row == self.row - 1 and self.row > 0:
            self.row -= 1

    def down(self, buffer, cursor):
        if cursor.row > self.row + self.n_rows - 2 and self.bottom < len(buffer) - 1:
            self.row += 4

    def horizontal_scroll(self, cursor, left_margin=5, right_margin=2):
        n_pages = cursor.col // (self.n_cols - right_margin)
        self.col = max(n_pages * self.n_cols - right_margin - left_margin, 0)

    def translate(self, cursor):
        # Cambio el margen del cursor a la izquierda ahora esta en 6
        # y baja una linea a la linea 1
        return cursor.row - self.row + 2, cursor.col - self.col + 6

    def adjust_cursor_position(self, cursor, buffer):
        max_row = min(len(buffer), self.bottom - 2)  # Restamos 1 para dejar espacio para el pie de página
        cursor.row = min(max(cursor.row, self.row), max_row)


def left(window, buffer, cursor):
    cursor.left(buffer)
    window.up(cursor)
    window.horizontal_scroll(cursor)


def right(window, buffer, cursor):
    cursor.right(buffer)
    window.down(buffer, cursor)
    window.horizontal_scroll(cursor)


def highlight_code(stdscr, buffer, language, window):
    # Define las palabras clave según el lenguaje seleccionado
    if language == 'html':
        keywords = HTML_KEYWORDS
        comment_color_pair = 1  # Define un color para los comentarios HTML
        attribute_color_pair = 2  # Define un color para los atributos HTML
        value_color_pair = 3     # Define un color para los valores de los atributos HTML

    elif language == 'python':
        keywords = PYTHON_KEYWORDS
        comment_color_pair = 2  # Define un color para los comentarios Python si es necesario
    else:
        keywords = set()  # Si el lenguaje no está definido, no hay palabras clave
        comment_color_pair = 2  # Define un color por defecto para los comentarios
        attribute_color_pair = 4  # Define un color para los atributos HTML si es necesario
        value_color_pair = 5     # Define un color para los valores de los atributos HTML si es necesario

    # Recorre cada línea del buffer
    for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):
        col_offset = 0  # Inicializa el offset de la columna

        # Busca todas las etiquetas HTML
        words = re.findall(r'<\/?[^>]+>', line)
        # Busca comentarios HTML
        comments = re.findall(r'<!--.*?-->', line)
        # Busca atributos y valores
        attributes_values = re.findall(r'(\w+)(="[^"]*")?', line)

        # Resalta los comentarios HTML
        for comment in comments:
            col = line.find(comment, col_offset)
            if col != -1:  # Si se encontró el comentario
                adjusted_col = col - window.col
                if adjusted_col >= 0:
                    stdscr.addstr(row + 2, adjusted_col + 6, comment, curses.color_pair(comment_color_pair))
                col_offset = col + len(comment)

        # Resalta las etiquetas HTML
        for word in words:
            if any(keyword.lower() in word.lower() for keyword in keywords):
                col = line.lower().find(word.lower(), col_offset)
                if col != -1:  # Si se encontró la palabra
                    adjusted_col = col - window.col
                    if adjusted_col >= 0:
                        stdscr.addstr(row + 2, adjusted_col + 6, word, curses.color_pair(4))
                    col_offset = col + len(word)

        # Resalta los atributos y valores
        for attr, val in attributes_values:
            # Resalta el atributo
            if attr:
                attr_start = line.find(attr, col_offset)
                if attr_start != -1:
                    adjusted_col = attr_start - window.col
                    if adjusted_col >= 0:
                        stdscr.addstr(row + 2, adjusted_col + 6, attr, curses.color_pair(attribute_color_pair))
                col_offset = attr_start + len(attr)

            # Resalta el signo '='
            if val:
                equal_sign_start = line.find('=', col_offset)
                if equal_sign_start != -1:
                    adjusted_col = equal_sign_start - window.col
                    if adjusted_col >= 0:
                        stdscr.addstr(row + 2, adjusted_col + 6, '=', curses.color_pair(5))
                col_offset = equal_sign_start + 1  # Avanza después del '='

                # Resalta el valor
                val_start = line.find(val, col_offset)
                if val_start != -1:
                    adjusted_col = val_start - window.col
                    if adjusted_col >= 0:
                        stdscr.addstr(row + 2, adjusted_col + 6, val, curses.color_pair(value_color_pair))
                col_offset = val_start + len(val)

def main(stdscr, filename, buffer, language):
    # Inicializar pares de colores
    curses.start_color()

    # Definir colores personalizados en RGB
    curses.init_color(1, 0, 0, 0)      # Negro (para fondo)
    curses.init_color(2, 1000, 1000, 1000)  # Gris claro (para atributos y valores)
    curses.init_color(3, 500, 500, 1000)  # Azul claro (para etiquetas HTML)
    curses.init_color(4, 1000, 500, 500)  # Rojo claro (para comentarios)
    curses.init_color(5, 1000, 1000, 1000)  # Blanco (para valores, por ejemplo)

    # Inicializar pares de colores
    curses.init_pair(1, curses.COLOR_WHITE, 1)  # Texto blanco sobre fondo negro
    curses.init_pair(2, 2, curses.COLOR_BLACK)  # Texto gris claro sobre fondo negro (atributos y valores)
    curses.init_pair(3, 3, curses.COLOR_BLACK)  # Texto azul claro sobre fondo negro (etiquetas HTML)
    curses.init_pair(4, 4, curses.COLOR_BLACK)  # Texto rojo claro sobre fondo negro (comentarios)
    curses.init_pair(5, 5, 1)  # Texto rojo claro sobre fondo negro (comentarios)

    # Obtener el tamaño de la pantalla inicial
    height, width = stdscr.getmaxyx()

    window = Window(args.filename, height - 2, width - 1)  # Usar el tamaño inicial
    cursor = Cursor()
    stdscr.move(*window.translate_cursor(cursor))

    while True:
        stdscr.erase()

        # Obtener el tamaño de la pantalla actual en cada iteración
        height, width = stdscr.getmaxyx()

        # Actualizar el tamaño de la ventana y la posición del cursor
        window.n_rows = height - 3
        window.n_cols = width - 1
        window.adjust_cursor_position(cursor, buffer)

        # Redibujar la interfaz de usuario
        for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):
            line_number = window.row + row + 1
            line = f"{line_number:3d} | {line}"
            if row == cursor.row - window.row and window.col > 0:
                line = "«" + line[window.col + 1:]
            if len(line) > window.n_cols:
                line = line[:window.n_cols - 1] + "»"
            try:
                stdscr.addstr(row + 2, 0, line, curses.color_pair(2))  # Usar el par de colores definido para el fondo

            except curses.error:
                pass  # Ignorar excepción si estamos tratando de escribir más allá del tamaño de la pantalla

        highlight_code(stdscr, buffer, language, window)
        # Agregar el encabezado con el nombre del archivo en la primera fila
        filename_header = f"{window.filename}"
        stdscr.addstr(0, 2, filename_header)

        stdscr.hline(height - 2, 1, curses.ACS_HLINE, width - 2, curses.color_pair(1))  # Línea inferior
        stdscr.hline(1, 1, curses.ACS_HLINE, width - 2, curses.color_pair(1))  # Línea superior
        TAB_SIZE = 4  # Define el número de espacios que representa una tabulación

        # Agregar el input de comando en la última fila si es necesario
        if window.show_command_input:
            # Agregar el input de comando en la última fila
            stdscr.addstr(height - 1, 1, "# CMD: " + window.command_input)
            # Mover el cursor a la posición donde se escribe el comando
            # stdscr.move(height - 1,len("# CMD: ") + len(window.command_input)+1)
            command_text = "# CMD: " + window.command_input
            stdscr.attron(curses.color_pair(1))  # Activar el par de colores para texto blanco
            stdscr.addstr(height - 1, 1, command_text)
            stdscr.attroff(curses.color_pair(1))

            # Actualizar la posición del cursor visual
            # stdscr.refresh()
        else:
            num_lines = len(buffer.lines)
            num_words = sum(len(line.split()) for line in buffer.lines)

            # Agregar un mensaje para indicar el modo de edición
            file_info = f"# EDIT MODE     |  Lines: {num_lines}   |   Words: {num_words}"

            # Mostrar la información en el footer
            stdscr.addstr(height - 1, 1, file_info)
            # Mover el cursor a la posición en la parte inferior izquierda
            # Actualizar la posición del cursor visual
            stdscr.move(*window.translate(cursor))

        k = stdscr.getkey()
        if k == "KEY_RESIZE":
            # Manejar el evento de cambio de tamaño de la ventana aquí
            # No imprimir KEY_RESIZE

            # Obtener el nuevo tamaño de la pantalla
            height, width = stdscr.getmaxyx()

            # Actualizar el tamaño de la ventana y la posición del cursor
            window.n_rows = height - 2
            window.n_cols = width - 1
            window.adjust_cursor_position(cursor, buffer)
        else:

            # Resto del código para manejar otras entradas de teclado...

            if k == "\t":  # Detecta si se presiona la tecla Tab
                # Inserta un número de espacios en lugar de una tabulación
                for _ in range(TAB_SIZE):
                    buffer.insert(cursor, " ")
                    right(window, buffer, cursor)
            elif k == 'KEY_BTAB':
                # Si se presiona Shift + Tab, eliminar un número de espacios en lugar de insertar una tabulación
                for _ in range(TAB_SIZE):
                    if cursor.col > 0:
                        cursor.left(buffer)
                        buffer.delete(cursor)
                        window.horizontal_scroll(cursor)  # Ajusta el desplazamiento horizontal si es necesario
            elif k == "KEY_LEFT":
                left(window, buffer, cursor)
            elif k == "KEY_DOWN":
                cursor.down(buffer)
                window.down(buffer, cursor)
                window.horizontal_scroll(cursor)
            elif k == "KEY_UP":
                cursor.up(buffer)
                window.up(cursor)
                window.horizontal_scroll(cursor)
            elif k == "KEY_RIGHT":
                right(window, buffer, cursor)
            elif k == "\n":

                if window.show_command_input:
                    command = window.command_input.strip()
                    # Ejecutar el comando ingresado por el usuario
                    process_command(stdscr, window, buffer, cursor, command)
                    cursor.row = max(0, min(cursor.row, len(buffer.lines) - 1))  # Asegurar que el cursor no esté fuera de rango
                    cursor.col = min(cursor.col, len(buffer.lines[cursor.row]))  # Asegurar que el cursor no esté fuera de rango

                else:
                    buffer.split(cursor)
                    right(window, buffer, cursor)


            elif k in ("KEY_DELETE", "\x04"):
                buffer.delete(cursor)
            elif k in ("KEY_BACKSPACE", "\x7f"):
                if window.show_command_input:
                    # Borrar un carácter del input del comando en modo de comando
                    if window.command_input:
                        window.command_input = window.command_input[:-1]
                else:
                    if (cursor.row, cursor.col) > (0, 0):
                        left(window, buffer, cursor)
                        buffer.delete(cursor)
            elif k == "\x18":  # Ctrl + X
                window.show_command_input = not window.show_command_input  # Alternar el modo de comando
                window.command_input = ''  # Restablecer el texto de entrada del comando
            else:
                if window.show_command_input:
                    # Agregar caracteres al input de comando en modo de comando
                    window.command_input += k
                else:
                    buffer.insert(cursor, k)
                    for _ in k:
                        right(window, buffer, cursor)

        window.adjust_cursor_position(cursor, buffer)


def run_editor(filename=None, language="none"):  # Añadir el argumento 'language' con un valor predeterminado
    if filename and os.path.exists(filename):  # Verifica si se proporciona un nombre de archivo válido y si existe
        with open(filename) as f:
            buffer = Buffer(f.read().splitlines())
    else:
        buffer = Buffer([''])  # Crear un buffer con una línea en blanco si no se proporciona un archivo existente

    curses.wrapper(lambda stdscr: main(stdscr, filename, buffer, 'html'))  # Pasar 'language' a 'main'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs='?', default="untitled.txt")  # Hacer el nombre de archivo opcional
    parser.add_argument("--language", default="none", help="Language for syntax highlighting")  # Argumento para seleccionar el lenguaje
    args = parser.parse_args()

    run_editor(filename=args.filename, language=args.language)
