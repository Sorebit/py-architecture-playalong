
from dataclasses import dataclass
from datetime import date


# Value Object here
@dataclass(frozen=True)
class OrderLine:
    order_ref: str
    sku: str
    qty: int


# class Order:
#     def __init__(self, ref: str):
#         self.ref: str = ref
#         """Reference - Identifies Order"""
#         self.lines: list[OrderLine] = []
#         """Order lines"""


# Entity here
class Batch:
    """Ordered by purchasing dpt. Small batch of stock."""
    
    def __init__(self, ref: str, sku: str, qty: int, eta: date | None = None) -> None:
        self.ref: str = ref
        """Reference - Identifies Batch"""
        self.sku: str = sku
        self.eta: date | None = eta or None
        """In stock when None, otherwise being shipped."""
        self._purchased_qty: int = qty
        self._allocations: set[OrderLine] = set()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.ref == self.ref

    def __hash__(self):
        return hash(self.ref)

    def __gt__(self, other):
        if self.eta is None:
            # In stock, it's preferred
            return False
        if other.eta is None:
            # Other is in stock, prefer it
            return True
        # Prefer the one that arrives earlier
        return self.eta > other.eta

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_qty(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_qty(self) -> int:
        return self._purchased_qty - self.allocated_qty

    def can_allocate(self, line: OrderLine) -> bool:
        if self.sku != line.sku:
            return False
        if self.available_qty < line.qty:
            # Don't allocate more than you've got
            return False
        return True


class OutOfStock(Exception):
    pass


def allocate(line: OrderLine, batches: list[Batch]):
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.ref
    except StopIteration:
        raise OutOfStock(f'Out of stock for SKU "{line.sku}"')
