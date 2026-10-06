import logging
from importlib.metadata import version

import dash
from dash import Dash, dcc, html
from flask import jsonify
from flask_caching import Cache

from mpships_infra import MPShipsApp
from mpships_infra.utility.utils import MP_UI_INSTALLED

logger = logging.getLogger(__name__)


# Initialize all MPApps unless marked as disabled
def get_all_subclasses(cls):
    # function below ensures that all indirect MPApp subclasses
    # are also initialized, such as GoogleApp(MaterialsApp)
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_all_subclasses(subclass))
    return subclasses


def register_apps():
    # Get all submodules of MPShipsApp
    mpships_app = {cls.__name__: cls for cls in get_all_subclasses(MPShipsApp)}
    initialized_mpships_apps = [mpships_app[app_name]() for app_name in mpships_app]

    def page_layout(app):
        def layout():
            return app.get_mp_layout()

        return layout

    for app in initialized_mpships_apps:  # Note: app is an instance of MPApp
        dash.register_page(
            app.name,
            path="/",
            name=app.name,
            layout=page_layout(app),
        )

    return initialized_mpships_apps


def register_callbacks(app, cache, initialized_mpships_apps):
    seen_classes = set()
    for component in initialized_mpships_apps:
        if type(component) not in seen_classes:
            component.generate_callbacks(app, cache)
            seen_classes.add(type(component))


def create_app(
    endpoint="/", pages_folder="pages", assets_folder="assets", logger_override=None
) -> Dash:
    """
    Create a "naked" app with minimum bulma styling

    Returns:
        Dash app
    """
    if not MP_UI_INSTALLED:
        logger.debug(
            "mp_ui not available. Using local development settings. This is expected for MPShips developers."
        )

    # modified_endpoint
    modified_endpoint = f"/MPShips{endpoint}" if MP_UI_INSTALLED else "/"

    # CSS
    BULMA_CSS = "https://cdn.jsdelivr.net/npm/bulma@1.0.0/css/bulma.min.css"

    app = Dash(
        __name__,
        assets_folder=assets_folder,
        external_stylesheets=[BULMA_CSS],
        external_scripts=[
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML",
            "https://materialsproject.statuspage.io/embed/script.js",
        ],
        use_pages=True,
        suppress_callback_exceptions=True,
        requests_pathname_prefix=modified_endpoint,
        routes_pathname_prefix="/",
        pages_folder=pages_folder,
    )

    # styling
    GLOBAL_BANNER = None
    NAVBAR_LAYOUT = None
    footer = None
    user_settings_modal = None

    # MP styling
    if MP_UI_INSTALLED:
        from mp_ui.layouts.main_app import (
            MPUserSettings,
            get_footer,
            get_global_banner,
            get_navbar_layout,
            get_user_settings_modal,
        )
        from mp_ui.metadata.constants import (
            GLOBAL_BANNER_MARKDOWN,
            GLOBAL_BANNER_VARIETY,
        )

        # MP UI
        GLOBAL_BANNER = get_global_banner(GLOBAL_BANNER_MARKDOWN, GLOBAL_BANNER_VARIETY)
        NAVBAR_LAYOUT = get_navbar_layout()
        footer = get_footer()
        user_settings_modal = get_user_settings_modal(user_settings=MPUserSettings())

        # global callbacks
        # from mp_ui import __version__ as mp_ui_version
        from mp_ui.core.cache import add_rq_caching_config, get_flask_caching
        from mp_ui.core.global_callbacks import get_main_callbacks

        # cache
        from mp_ui.core.settings import SETTINGS

        REDIS_URL = f"redis://{SETTINGS.REDIS_ADDRESS}"
        add_rq_caching_config(app, REDIS_URL, SETTINGS.QUEUE_NAME)
        # cache = get_flask_caching(app, SETTINGS, f"mp_ui_{mp_ui_version}")
        cache = get_flask_caching(app, SETTINGS, "mpships")
    else:
        cache = Cache(app.server, config={"CACHE_TYPE": "NullCache"})

    main_layout = html.Div(
        [
            html.Div(
                className="mp-container",
                children=[
                    dcc.Location(id="mp-url", refresh=False),
                    dcc.Store(
                        id="mp-title-meta",
                        data={
                            "title": "Materials Project",
                            "meta": "Materials Project",
                        },
                    ),
                    GLOBAL_BANNER,
                    NAVBAR_LAYOUT,
                    dash.page_container,
                    html.Div(id="request-headers", className="is-hidden"),
                ],
            ),
            footer,
            user_settings_modal,
            html.Div(id="dummy-content"),
        ]
    )
    app.layout = main_layout

    if MP_UI_INSTALLED:
        get_main_callbacks(app)  # the global callback functions

    initialized_mpships_apps = register_apps()
    register_callbacks(app, cache, initialized_mpships_apps)

    @app.server.route("/healthcheck")
    def serve_healthcheck():
        d = {
            "health": "OK",
            "pymatgen": version("pymatgen"),
            "crystal_toolkit": version("crystal_toolkit"),
            "emmet-core": version("emmet-core"),
            "mp_api": version("mp_api"),
            "dash": dash.__version__,
        }
        return jsonify(d)

    return app
