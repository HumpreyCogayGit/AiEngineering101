"""A ready-made MCP server for EXER032 (you don't need to change it).

It exposes the three kinds of MCP capabilities:
  TOOLS      — functions the model can call        (get_product, list_products, store_hours)
  RESOURCES  — read-only data the app can load     (menu://today)
  PROMPTS    — reusable prompt templates           (barista_recommendation)

It speaks MCP over stdio: the client starts this script as a subprocess and
exchanges JSON-RPC messages through stdin/stdout. That's why this file must
never print() to stdout.

Try it in the MCP Inspector:
    npx @modelcontextprotocol/inspector uv run python EXER032/servers/coffee_server.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nimbus-coffee", log_level="WARNING")

PRODUCTS = {
    "mount apo sunrise": {"price": 520, "roast": "light", "notes": "citrus, honey, jasmine"},
    "benguet highlands": {"price": 480, "roast": "medium", "notes": "chocolate, caramel, red apple"},
    "barako bold": {"price": 390, "roast": "dark", "notes": "strong, smoky, long finish"},
    "nimbus house blend": {"price": 420, "roast": "medium-dark", "notes": "balanced, nutty"},
    "decaf cloud": {"price": 550, "roast": "medium", "notes": "smooth, cocoa"},
}
HOURS = {"makati": "6:30–21:00 daily", "bgc": "7:00–22:00 daily", "quezon city": "7:00–20:00, closed Mondays"}


@mcp.tool()
def list_products() -> list[str]:
    """List the names of all coffee beans Nimbus sells."""
    return [name.title() for name in PRODUCTS]


@mcp.tool()
def get_product(name: str) -> dict:
    """Get price (PHP per 250 g), roast level and tasting notes of a coffee by name."""
    info = PRODUCTS.get(name.strip().lower())
    if info is None:
        raise ValueError(f"Unknown product: {name}. Use list_products to see valid names.")
    return {"name": name.title(), **info}


@mcp.tool()
def store_hours(branch: str) -> str:
    """Opening hours of a Nimbus café branch: Makati, BGC or Quezon City."""
    return HOURS.get(branch.strip().lower(), f"No branch called {branch}. Branches: Makati, BGC, Quezon City.")


@mcp.resource("menu://today")
def todays_menu() -> str:
    """Today's café specials."""
    return "Today's specials: Ube Cold Brew (₱180), Calamansi Tonic Espresso (₱165), Ensaymada (₱75)."


@mcp.prompt()
def barista_recommendation(taste: str) -> str:
    """A prompt asking for a coffee recommendation for someone's taste."""
    return (f"You are an expert Nimbus barista. A customer likes {taste}. "
            "Use the list_products and get_product tools, then recommend ONE coffee and explain why.")


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
