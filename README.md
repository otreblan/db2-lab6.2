# Índice invertido

## Dependencias
- `coreutils`
- `grep`
- `nltk`

## Implementación

### `./r-index.py FILE...`

Por cada archivo el texto es separado en tokens,
las mayúsculas son convertidas en minúsculas y
las palabras que están en la stoplist son filtradas.
Después se saca la raíz de cada palabra y se retorna una lista.

```python
def preproccess(file: TextIOWrapper) -> List[str]:
    ss = SnowballStemmer("spanish")

    tr1 = Popen(['tr', '-s', '[:punct:][:space:]', '\n'], stdin=file, stdout=PIPE)
    tr2 = Popen(['tr', '[:upper:]', '[:lower:]'], stdin=tr1.stdout, stdout=PIPE)
    grep = Popen(['grep', '-Fvwf', 'stoplist.txt'], stdin=tr2.stdout, stdout=PIPE)

    words: List[str] = []
    for word in grep.stdout:
        words.append(ss.stem(word.decode('utf-8').strip('\n')))

    return words
```

Después de obtener la lista de raices de palabras,
se agregan las nuevas palabras a la lista de palabras de todos los archivos
y al `r_index`.
Al final el índice invertido es filtrado por las 500 palabras más frecuentes
y es escrito a `r_index.txt`.

```python
def generate_r_index(files: List[str], output: TextIO = stdout) -> None:
    words: List[str] = []
    r_index: Dict[str, Set[str]] = {}

    for file_name in files:
        with open(file_name, "r") as file:
            tokens: List[str] = preproccess(file)
            words.extend(tokens)
            for word in tokens:
                r_index.setdefault(word, set()).add(file_name)

    print_r_index(filter_r_index(r_index, words, 500), output)
```

### `./r-index.py`
El índice invertido es leido desde `r_index,txt`.
