"""Bus stop module."""


class Haltestelle:
    """Represents a bus stop."""

    def __init__(
        self, name: str, vag_number: str, vgn_number: str, products: str | None
    ) -> None:
        """Initialize bus stop object."""

        self._name: str = name
        self._vag_number: str = vag_number
        self._vgn_number: str = vgn_number

        if products and isinstance(products, str):
            self._products = products.split(",")
        else:
            self._products = []

    @property
    def name(self):
        """Returns bus stop name."""
        return self._name

    @property
    def vag_number(self):
        """Returns bus top vag number."""
        return self._vag_number

    @property
    def vgn_number(self):
        """Returns bus top vgn number."""
        return self._vgn_number

    @property
    def products(self):
        """Returns vag products supoorted by this bus stop."""
        return self._products
