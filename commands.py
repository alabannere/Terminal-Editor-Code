import sys
import os

def process_command(stdscr, window, buffer, cursor, command):
    if command == 'exit':
        window.command_input = '¿Desea guardar los cambios antes de salir? (y/n)'
        stdscr.refresh()  # Refrescar antes de obtener la entrada del usuario
        response = stdscr.getstr()  # Leer toda la línea de entrada
        if response.lower().strip() == 'y':
            with open(window.filename, 'w') as file:
                file.write('\n'.join(buffer.lines))
        sys.exit(0)

    elif command.startswith('open'):
        filename = command.split()[1]
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                buffer.lines = file.read().split('\n')
                window.command_input = ''  # Borrar el texto del campo de comando
        else:
            window.command_input = 'No se puede abrir '+str(filename) 

    elif command.startswith('replace'):
        args = command.split()[1:]
        if len(args) < 1:
            window.command_input = "Uso: replace old_text new_text"
        else:
            old_text = args[0]
            new_text = args[1] if len(args) > 1 else ''
            buffer.lines = [line.replace(old_text, new_text) for line in buffer.lines]
            window.command_input = ''  # Borrar el texto del campo de comando

    elif command.startswith('replaceinline'):
        args = command.split()[1:]
        if len(args) < 3:
            window.command_input = "Uso: replaceinline line_number old_text new_text"
        else:
            try:
                line_number = int(args[0])
                if line_number <= 0 or line_number > len(buffer.lines):
                    window.command_input = 'Línea '+str(line_number) +' fuera de rango'
                    return
                old_text = args[1]
                new_text = args[2] if len(args) > 2 else ''
                buffer.lines[line_number - 1] = buffer.lines[line_number - 1].replace(old_text, new_text)

                cursor.row = max(0, min(cursor.row, len(buffer.lines) - 1))  # Asegurar que el cursor no esté fuera de rango
                cursor.col = min(cursor.col, len(buffer.lines[cursor.row]))  # Asegurar que el cursor no esté fuera de rango

                window.command_input = ''  # Borrar el texto del campo de comando

            except ValueError:
                window.command_input = "El número de línea debe ser un entero"


    elif command.startswith('find'):
        target = command.split()[1]
        found = False

        for i in range(len(buffer.lines)):
            if target in buffer.lines[i]:
                window.show_command_input = not window.show_command_input
                found = True

                # Actualizar la posición del cursor en la ventana de texto
                window.cursor_y = i
                window.cursor_x = buffer.lines[i].index(target)

                # Mover el cursor visual a la nueva posición
                stdscr.move(window.row + window.cursor_y, window.cursor_x)
                stdscr.refresh()

                # Actualizar la posición del cursor en el objeto Cursor
                cursor.row = window.cursor_y
                cursor.col = window.cursor_x

                window.command_input = ''  # Borrar el texto del campo de comando
                break  # Salir del bucle una vez que se encuentra la primera ocurrencia

        if not found:
            window.command_input = 'No se encontró ' + str(target)



    elif command.startswith('go to line'):
        target_line = int(command.split()[3])
        if 0 < target_line <= len(buffer.lines):
            window.show_command_input = not window.show_command_input  # Alternar el modo de comandos
            window.command_input = ''  # Limpiar el textbox de comandos

            # Mover el cursor verticalmente a la línea especificada
            cursor.row = target_line - 1
        else:
            window.command_input = 'No se encontró la línea '+str(target_line) 

    elif command.startswith('ins'):
        args = command.split()[1:]
        if len(args) < 2:
            window.command_input = "Uso: ins line_number text_to_insert"

        else:
            try:
                line_number = int(args[0])
                if 0 < line_number <= len(buffer.lines):
                    text_to_insert = ' '.join(args[1:])
                    buffer.lines.insert(line_number - 1, text_to_insert)
                    window.command_input = ''  # Borrar el texto del campo de comando
                else:
                    window.command_input = 'Línea ' + str(line_number) + ' fuera de rango'

            except ValueError:
                window.command_input = 'El número de línea debe ser un entero'

    elif command.startswith('del'):
        args = command.split()[1:]
        if len(args) < 1:
            window.command_input = ''
        else:
            try:
                line_number = int(args[0])
                if len(buffer.lines) == 1:
                    window.command_input = 'No se puede eliminar la última línea'
                elif 0 < line_number <= len(buffer.lines):
                    del buffer.lines[line_number - 1]
                    window.command_input = ''  # Borrar el texto del campo de comando
                else:
                    window.command_input = 'Línea ' + str(line_number) + ' fuera de rango'
            except ValueError:
                window.command_input = 'El número de línea debe ser un entero'

    elif command.startswith('save '):
        new_filename = command[5:].strip()  # Obtener el nuevo nombre del archivo del comando, eliminando espacios en blanco
        try:
            with open(new_filename, 'w') as file:
                file.write('\n'.join(buffer.lines))
            window.filename = new_filename  # Actualizar el nombre del archivo en la ventana
            window.command_input = f'Saved as {window.filename}'
        except Exception as e:
            print(f'Error al guardar el archivo: {str(e)}')
            window.command_input = f'Error al guardar el archivo: {str(e)}'

    elif command.startswith('new '):
        new_filename = command[4:].strip()  # Obtener el nombre del archivo del comando, eliminando espacios en blanco
        try:
            with open(new_filename, 'w') as file:
                file.write('')
            window.filename = new_filename
            buffer.lines = ['']  # Inicializar el editor con una línea vacía
            window.command_input = f'New file created: {new_filename}'
        except Exception as e:
            window.command_input = f'Error al crear el archivo: {str(e)}'

    elif command == 'save':
        if window.filename:
            try:
                with open(window.filename, 'w') as file:
                    file.write('\n'.join(buffer.lines))
                window.command_input = f'Saved as {window.filename}'
            except Exception as e:
                print(f'Error al guardar el archivo: {str(e)}')
                window.command_input = f'Error al guardar el archivo: {str(e)}'
        else:
            window.command_input = 'Enter a filename to save as:'


    elif command.startswith('new2'):
        args = command.split()[1:]
        if len(args) < 1:
            window.command_input = 'Debe proporcionar un nombre de archivo'
        else:
            new_filename = args[0]
            try:
                with open(new_filename, 'w') as file:
                    file.write('')
                window.filename = new_filename
                buffer.lines = ['']  # Inicializar el editor con una línea vacía
                window.command_input = ''  # Borrar el texto del campo de comando
            except Exception as e:
                window.command_input = f'Error al crear el archivo: {str(e)}'



    elif command == 'lines':
        window.toggle_line_numbers()  # Llama al método para alternar la visibilidad de los números de línea
        window.command_input = ''  # Borrar el texto del campo de comando

    else:            
       #buffer.lines.append(f'Ejecutando comando: {command}')
        window.command_input = ''
