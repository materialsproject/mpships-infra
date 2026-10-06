from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

import dash
import dash_mp_components as mpc
from crystal_toolkit.core.mpcomponent import MPComponent
from dash import html
from dash.dependencies import Input, Output
from pydash import get

from mpships_infra.utility.utils import (
    MP_UI_INSTALLED,
    require_mp_ui,
)

logger = logging.getLogger(__name__)

_RESERVED_ATTRS: ClassVar[frozenset[str]] = frozenset(
    {
        "name",
        "description",
        "url",
        "author",
        "category",
        "credits",
        "icon",
        "dois",
        "docs_url",
        "external_links",
        "contributed",
        "contributed_app",
        "long_description",
    }
)


if not MP_UI_INSTALLED:
    logger.debug("No mp_ui available. Local development setting is used")


class MPShipsApp(MPComponent, ABC):
    # used to defer generation of callbacks until app.layout defined
    # can be helpful to callback exceptions retained
    _mpships_callbacks_to_generate: ClassVar[set[MPShipsApp]] = set()

    def __init__(self):
        super().__init__()
        self._mpships_callbacks_to_generate.add(self)

        try:
            self.ships_setup()
        except AttributeError as e:
            reserved_hit = next(
                (attr for attr in _RESERVED_ATTRS if attr in str(e)), None
            )
            if reserved_hit:
                raise AttributeError(
                    f"'{reserved_hit}' is a reserved MPShipsApp property and cannot be "
                    f"assigned in ships_setup(). It's set automatically by the framework "
                    f"(e.g. 'name' is derived from your class name). Use a different "
                    f"attribute name instead, like 'self.my_{reserved_hit}'."
                ) from e
            raise

    def get_layout(self):
        """Return a Dash layout for the app."""
        return self.ships_layout()

    @abstractmethod
    def ships_layout(self):
        """Return a Dash layout for the app."""
        ...

    def ships_asset(self, filename: str) -> str:
        """Prefix-aware asset URL for files in the assets folder."""
        return dash.get_asset_url(filename)

    def ships_setup(self, *args, **kwargs):
        pass

    def ships_callbacks(self, app, cache):
        pass

    def _get_app_meta_data(self, field):
        defaults = {
            "description": None,
            "long_description": None,
            "url": None,
            "author": None,
            "category": None,
            "credits": None,
            "icon": None,
            "dois": [],
            "docs_url": None,
            "external_links": None,
            "contributed": None,
        }

        if field not in defaults:
            raise ValueError(f"Unknown metadata field: {field}")

        app_metadata = {}
        if MP_UI_INSTALLED:
            from mp_ui.metadata.constants import CONTRIBUTED_APP_METADATA

            app_metadata = CONTRIBUTED_APP_METADATA.get(self.__class__.__name__, {})

        if field == "long_description":
            return app_metadata.get("long_description", app_metadata.get("description"))

        value = app_metadata.get(field, defaults[field])
        return [] if field == "dois" and value is None else value

    @property
    def name(self):
        """Name of your app, will be included in navigation menu."""
        return self.__class__.__name__

    @property
    def contributed_app(self) -> bool:
        return True

    @property
    def description(self):
        return self._get_app_meta_data("description")

    @property
    def long_description(self):
        return self._get_app_meta_data("long_description")

    @property
    def url(self):
        return self._get_app_meta_data("url")

    @property
    def author(self):
        return self._get_app_meta_data("author")

    @property
    def category(self):
        return self._get_app_meta_data("category")

    @property
    def credits(self):
        return self._get_app_meta_data("credits")

    @property
    def icon(self):
        return self._get_app_meta_data("icon")

    @property
    def dois(self):
        return self._get_app_meta_data("dois")

    @property
    def docs_url(self):
        return self._get_app_meta_data("docs_url")

    @property
    def external_links(self):
        return self._get_app_meta_data("external_links")

    @property
    def contributed(self):
        return self._get_app_meta_data("contributed")

    def get_mpships_app_content(self):
        return html.Section(
            [
                html.Div(
                    [
                        html.Progress(
                            className="progress is-primary",
                        ),
                    ],
                    id=self.id("mp-app-content"),
                )
            ],
            className="mp-app-content section",
        )

    def get_mpships_app_container(
        self,
        mp_app_content: html.Section,
    ):
        return html.Div(
            [
                html.Div(
                    mpc.DrawerContextProvider(
                        [
                            html.Div(
                                [mp_app_content],
                                className="mp-app-content-container",
                            ),
                        ]
                    ),
                    id=self.id("app-container"),
                    className="mp-app-container is-gapless",
                ),
            ]
        )

    @require_mp_ui
    def get_breadcrumb_links(self, payload=None) -> list[mpc.Link]:
        """Get the list of links to display as breadcrumbs below the app name.
        Note that these use the custom mpc.Link component so that certain breadcrumb
        links can preserve query parameters when the link is clicked.

        :param payload: anything in the URL after https://materialsproject.org/your_app_name/
        :return: list of link components
        """
        from mp_ui.metadata.constants import APP_METADATA, APP_TREE

        breadcrumb_links = [
            mpc.Link("Home", href="/"),
        ]
        if self.contributed_app:
            breadcrumb_links.append(
                mpc.Link("Contributed Apps", href="/contributed-apps")
            )
        # having a category set means the MPApp is a top-level "App" on MP
        elif self.category:
            breadcrumb_links.append(mpc.Link("Apps", href="/apps"))

        parts = self.url.split("/")
        # traverse the app tree to get an appropriate breadcrumb
        for idx, _part in enumerate(parts):
            app_name = get(APP_TREE, parts[0 : idx + 1] + ["NAME"])
            if app_metadata := APP_METADATA.get(app_name):
                breadcrumb_links.append(
                    mpc.Link(
                        app_metadata.get("name"),
                        href=f"/{app_metadata['url']}",
                        preserveQuery=True,
                    )
                )
        if payload:
            breadcrumb_links.append(
                mpc.Link(payload, href=f"/{payload}", preserveQuery=True)
            )

        return breadcrumb_links

    def get_mp_layout(self, payload=None):
        mp_app_content = self.get_mpships_app_content()
        mp_app_container = self.get_mpships_app_container(mp_app_content)
        if MP_UI_INSTALLED:
            from mp_ui.layouts.mpapp import (
                get_apps_sidebar,
                get_breadcrumbs,
                get_citations,
                get_contribute_form_button,
                get_credits,
                get_docs_link,
                get_drawers,
                get_external_links,
                get_icon,
                get_mp_app_container,
                get_mp_app_content,
                get_mp_app_header,
                get_mp_app_login_content,
            )
            from mp_ui.metadata.constants import (
                _MAIN_CITATIONS,
                APP_CITATION_DICT,
                APP_METADATA,
                MP_APPS_BY_CATEGORY,
            )

            icon = get_icon(self.icon)
            citations = get_citations(self.dois, APP_CITATION_DICT)
            external_links = get_external_links(self.external_links)
            docs_link = get_docs_link(self.docs_url, self.name)
            credits = get_credits(self.credits)
            breadcrumbs = get_breadcrumbs(self.get_breadcrumb_links(payload))
            contribute_form_button = get_contribute_form_button(self.name)
            mp_app_header = get_mp_app_header(
                breadcrumbs,
                icon,
                contribute_form_button,
                self.name,
                self.id("references-drawer"),
                self.id("documentation-drawer"),
                contributed_class="contributed-app-header",
            )
            drawers = get_drawers(
                credits,
                _MAIN_CITATIONS,
                citations,
                docs_link,
                external_links,
                self.long_description,
                self.id("references-drawer"),
                self.id("documentation-drawer"),
            )

            if not MP_UI_INSTALLED:
                mp_app_content = get_mp_app_content(self.id("mp-app-content"), drawers)
            else:
                mp_app_content = get_mp_app_login_content(
                    self.__class__.__name__,
                    self.id("mp-app-content"),
                    "mpships",
                    drawers,
                )

            mp_apps_sidebar = get_apps_sidebar(
                self.name, APP_METADATA, MP_APPS_BY_CATEGORY
            )
            # final div
            mp_app_container = get_mp_app_container(
                mp_apps_sidebar, mp_app_header, mp_app_content, self.id("app-container")
            )

        return mp_app_container

    def generate_callbacks(self, app, cache):  # noqa: F811
        @app.callback(
            Output(self.id("mp-app-content"), "children"), Input("mp-url", "pathname")
        )
        def update_main_content(pathname):
            return self.get_layout()

        self.ships_callbacks(app, cache)
