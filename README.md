# jonja
[![PyPI version](https://badge.fury.io/py/jonja.svg)](https://badge.fury.io/py/jonja)
![PyPI downloads per mounth](https://img.shields.io/pypi/dm/jonja)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/UT1C/jonja)

Jinja-based texts and objects render.

## Installation
```
pip install jonja
```

## Usage
1. Make template
`hello.j2`
```j2
Hello, {{ username }}!
*#!#*
world:
  $cls: "types:SimpleNamespace"
  $kwargs: {name: earth, size: {{ world_size }} }
```
2. Make env
```py
from pathlib import Path
from jonja import JonjaEnv
env = JonjaEnv(Path.cwd() / "static" / "templates")
```
3. Render
```py
text, objs = await env.render("hello", username="mikk", world_size=10_000)
```
