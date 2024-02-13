# Terminal Code Editor in Python

## Description
This is a code/text editor developed in Python, version 1.0.1. Although it's in an early stage of development, it aims to provide an experience similar to nano, with the ability to switch between two modes: edit mode and command mode.

## Known Issues
- Currently, syntax highlighting does not work properly for tag closures.
- When creating a new line while being on the last line of the file, there is an issue with scrolling that prevents the screen from scrolling downwards.

## Command Mode
Command mode is activated with the key combination Ctrl + X. In this mode, you can execute various commands, such as:
- `ins <line number> <text>`: Inserts a line with the specified text at the indicated line.
- `del <line number>`: Deletes the specified line.
- `save`: Saves the file.
- `find <text>`: Searches for text in the file.
- `go toline <line number>`: Takes you to the specified line.

## Author
- Alejandro Labannere
  
## Contributing
If you have ideas to improve this editor, you're welcome to contribute! Feel free to submit pull requests or report issues.

## License
This project is under the MIT License. See the LICENSE file for more details.
