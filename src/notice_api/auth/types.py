from typing import Any, Protocol

from fastapi import Request
from fastapi.datastructures import URL
from fastapi.responses import RedirectResponse


class StarletteOAuthApp(Protocol):
    async def authorize_redirect(
        self,
        request: Request,
        redirect_uri: str | URL,
        **kwargs: Any,
    ) -> RedirectResponse:
        """Create a HTTP Redirect for Authorization Endpoint.

        Args:
            request: HTTP request instance from Starlette view.
            redirect_uri: Callback or redirect URI for authorization.
            kwargs: Extra parameters to include.
        Returns:
            A HTTP redirect response.
        """

        raise NotImplementedError("Method not implemented.")

    async def authorize_access_token(
        self,
        request: Request,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch access token in authorization grant.

        Args:
            request: HTTP request instance from Starlette view.
            kwargs: Extra parameters to include.
        Returns:
            A token JSON object.
        """

        raise NotImplementedError("Method not implemented.")


class OnAfterTokenResponse(Protocol):
    async def __call__(self, token: dict[str, Any]) -> None:
        """Hook function that will be called after token response.

        Args:
            token: Token JSON object.
        """

        raise NotImplementedError("Method not implemented.")
