from datetime import date, timedelta
import pytest

from model import Batch, OrderLine, allocate, OutOfStock

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch('batch-001', sku, batch_qty, eta=today),
        OrderLine('order-123', sku, line_qty),
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    big_batch, small_line = make_batch_and_line('SMALL-TABLE', 20, 2)
    big_batch.allocate(small_line)

    assert big_batch.available_qty == 18


def test_can_allocate_if_available_greater_than_required():
    big_batch, small_line = make_batch_and_line('SMALL-TABLE', 20, 2)
    assert big_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_smaller_than_required():
    small_batch, big_line = make_batch_and_line('BLUE-CUSHION', 2, 20)
    assert small_batch.can_allocate(big_line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line('BLUE-CUSHION', 2, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch('batch-001', 'UNCOMFY-CHAIR', 100, eta=None)
    different_sku_line = OrderLine('order-123', 'COMFY-CHAIR', 10)
    assert batch.can_allocate(different_sku_line) is False


def test_allocation_is_idempotent():
    big_batch, small_line = make_batch_and_line('SMALL-TABLE', 20, 2)
    big_batch.allocate(small_line)
    big_batch.allocate(small_line)
    assert big_batch.available_qty == 18


def test_can_only_dealocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line('DECORATIVE-TRIKET', 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_qty == 20


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("oref", "RETRO-CLOCK", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_qty == 90
    assert shipment_batch.available_qty == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
    latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
    line = OrderLine("order1", "MINIMALIST-SPOON", 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_qty == 90
    assert medium.available_qty == 100
    assert latest.available_qty == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow)
    line = OrderLine("oref", "HIGHBROW-POSTER", 10)
    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert allocation == in_stock_batch.ref


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    allocate(OrderLine("order1", "SMALL-FORK", 10), [batch])

    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        allocate(OrderLine("order2", "SMALL-FORK", 1), [batch])
