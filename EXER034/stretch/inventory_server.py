"""A third MCP server for EXER034 stretch goal 2: stock levels.

It deliberately has a tool called `list_products`, the same name as a tool of
the coffee server, to create a name collision. Never print() to stdout here.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("inventory", log_level="WARNING")

STOCK = {"mount apo sunrise": 14, "benguet highlands": 0, "barako bold": 32, "nimbus house blend": 9, "decaf cloud": 3}


@mcp.tool()
def list_products() -> list[dict]:
    """List every product in the warehouse with the number of 250 g bags in stock."""
    return [{"name": name.title(), "bags_in_stock": bags} for name, bags in STOCK.items()]


@mcp.tool()
def get_stock(name: str) -> dict:
    """Number of 250 g bags of one coffee in the warehouse."""
    bags = STOCK.get(name.strip().lower())
    if bags is None:
        raise ValueError(f"Unknown product: {name}. Use list_products to see valid names.")
    return {"name": name.title(), "bags_in_stock": bags, "in_stock": bags > 0}


if __name__ == "__main__":
    mcp.run()
