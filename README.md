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
{% jobj cached schema %}
world:
  $cls: "types:SimpleNamespace"
  $kwargs: {name: earth, size: {{ world_size }} }
{% endjobj %}
```
2. Load extension
```py
from pathlib import Path

import jinja2 as j2
from jonja import Jonja

env = j2.Environment(..., extensions=(Jonja, ))
```
3. Render
```py
text, objs = await env.render("hello", username="mikk", world_size=10_000)
```

## TODO
- [ ] make deepcopy of cached generated objects (maybe controlled by option on both env and render side)
- [ ] make di socially independent (allow multiple instances of ext with different di container instances)
