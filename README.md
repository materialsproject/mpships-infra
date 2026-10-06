# mpships-infra

Core infrastructure for MPShips, the contributed-app platform for Materials Project. It provides the base class that contributed apps extend, a shared client for Materials Project data, and the app factory that wires everything together.

## What's in this package

| Piece | Purpose |
|---|---|
| `MPShipsApp` | Base class for every contributed app. Contributors fill in three hooks. |
| `get_rester()` | The one way an app gets a Materials Project API client. |

## Installation

<!-- TODO: confirm the published package name and install command -->

```bash
pip install mpships-infra
```

## `MPShipsApp`

`MPShipsApp` extends `MPComponent` (from `crystal_toolkit`) and is an abstract base class. A contributed app is a subclass that implements the hooks below. The framework calls the hooks for you, so the subclass never calls any of them directly, and none of them needs a `super()` call.

```python
from dash import html
from mpships_infra import MPShipsApp


class MyApp(MPShipsApp):
    def ships_setup(self, *args, **kwargs):      # optional
        self.greeting = "Hello"

    def ships_layout(self):                      # required
        return html.Div(f"{self.greeting}")

    def ships_callbacks(self, app, cache):       # optional
        pass
```

### Hooks

| Hook | Required? | Called | Purpose |
|---|---|---|---|
| `ships_setup(*args, **kwargs)` | No | At the end of `__init__` | Set instance state |
| `ships_layout()` | **Yes** (`@abstractmethod`) | Each time the page renders | Return the app's Dash layout |
| `ships_callbacks(app, cache)` | No | Once per app class, after the page layout exists | Register callbacks with `@app.callback` |

A subclass that omits `ships_layout` can't be instantiated, and Python raises a `TypeError` at load time.


### What subclasses must not override

`__init__`, `get_layout`, and `generate_callbacks` carry framework behavior. Overriding them without calling the base implementation silently breaks registration or routing, which is why the contributor-facing surface is limited to the three `ships_` hooks.

### Metadata properties

These read-only properties describe the app in navigation and documentation views:

`name`, `description`, `long_description`, `url`, `author`, `category`, `credits`, `icon`, `dois`, `docs_url`, `external_links`, `contributed`, `contributed_app`

- `name` is the **class name**.

Because they are properties without setters, assigning to one (for example `self.name = "x"` in `ships_setup`) raises an `AttributeError`. Use a different attribute name for custom values.

## `get_rester()`

`get_rester()` returns the Materials Project API client that apps use to fetch data. Apps call it instead of constructing their own `MPRester`, so the platform controls how the client is configured in one place.

### Setup
Set your Materials Project API key as an environment variable before running your app:

```bash
export MP_API_KEY=<YOUR_API_KEY>
```

The export applies to the current terminal session. Add it to your shell profile (for example `~/.zshrc`) to keep it across sessions.

### Usage
```python
from mpships_infra import get_rester

docs = get_rester().materials.summary.search(
    chemsys=["Au"], fields=["material_id", "has_props"]
)
```

```python
from mpships_infra import get_rester

contribs_docs = mpr.contribs.query_contributions(
    query={
        "project": "<YOUR_PROJECT>",
    }
)
```

See the [Materials Project API documentation](https://docs.materialsproject.org/downloading-data/using-the-api/getting-started) for the available endpoints.
