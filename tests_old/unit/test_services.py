from src.allocation.adapters import repository
import pytest
from src.allocation.service_layer import services, unit_of_work
from src.allocation.domain.model import OrderLine, Batch, allocate
from datetime import date, timedelta

class FakeRepository(repository.AbstractProductsRepository):
    def __init__(self, products):
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeRepository([
            Batch(ref, sku, qty, eta)
        ])
    
class FakeSession():
    commited = False

    def commit(self):
        self.commited = True

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True
    
    def rollback(self):
        pass

tomorrow = date(2021, 1, 2)    # Arbitrary date

def test_returns_allocation():
    repo = FakeRepository.for_batch("batch1", "COMPLICATED-LAMP", 100, eta=None)
    uow = FakeUnitOfWork()
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"

def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()
    line = OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = Batch("b1", "SSSSS", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)

def test_commits():
    uow = FakeUnitOfWork()
    batch = Batch('b1', 'OMINOUS-MIRROR', 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert session.commited is True

def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("oref", "RETRO-CLOCK", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100

def test_prefers_warehouse_batches_to_shipments():
    uow = FakeUnitOfWork()
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()
    services.allocate("oref", "RETRO-CLOCK", 10, uow)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100

def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"

def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "AREALSKU", 100, None, uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)
