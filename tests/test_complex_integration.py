import pytest

from src.manager import Manager
from src.models import ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2025-03-15",
            settlement_year=2025,
            settlement_month=2,
            amount_pln=1250.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-03-15",
            settlement_year=2024,
            settlement_month=2,
            amount_pln=1150.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-02-02",
            settlement_year=2024,
            settlement_month=1,
            amount_pln=222.0,
            type="electricity",
        )
    )

    costs = manager.get_apartment_costs("apartment-1", 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs("apart-polanka", 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs("apart-polanka", 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs("apart-polanka", 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs("apart-polanka", 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs("apart-polanka")
    assert costs == 3532.0


@pytest.mark.parametrize("invalid_month", [0, -1, 13, 99])
def test_get_apartment_costs_invalid_month(invalid_month):
    manager = Manager(Parameters())
    with pytest.raises(ValueError):
        manager.get_apartment_costs("apart-polanka", year=2026, month=invalid_month)


def test_create_apartment_settlement():
    manager = Manager(Parameters())

    # nieistniejace mieszkanie
    assert manager.create_apartment_settlement("non-existent", 2025, 1) is None

    # mieszkanie z rachunkami w 2025-01 (910pln)
    settlement_with_bills = manager.create_apartment_settlement(
        "apart-polanka", 2025, 1
    )
    assert settlement_with_bills is not None
    assert isinstance(settlement_with_bills, ApartmentSettlement)
    assert settlement_with_bills.apartment == "apart-polanka"
    assert settlement_with_bills.year == 2025
    assert settlement_with_bills.month == 1
    assert settlement_with_bills.total_rent_pln == 0.0
    assert settlement_with_bills.total_bills_pln == 910.0
    assert settlement_with_bills.total_due_pln == 910.0

    # mieszkanie bez rachunków
    settlement_no_bills = manager.create_apartment_settlement("apart-polanka", 2025, 3)
    assert settlement_no_bills is not None
    assert settlement_no_bills.apartment == "apart-polanka"
    assert settlement_no_bills.year == 2025
    assert settlement_no_bills.month == 3
    assert settlement_no_bills.total_bills_pln == 0.0
    assert settlement_no_bills.total_due_pln == 0.0


def test_create_tenant_settlements():
    manager = Manager(Parameters())

    # 1. Mieszkanie z 3 najemcami -> 910.0 PLN / 3
    apt_settlement = manager.create_apartment_settlement("apart-polanka", 2025, 1)
    assert apt_settlement is not None

    tenant_settlements = manager.create_tenant_settlements(apt_settlement)
    assert len(tenant_settlements) == 3
    assert all(isinstance(ts, TenantSettlement) for ts in tenant_settlements)

    expected_share = 910.0 / 3
    tenant_keys = {ts.tenant for ts in tenant_settlements}
    assert tenant_keys == {"tenant-1", "tenant-2", "tenant-3"}

    for ts in tenant_settlements:
        assert ts.apartment_settlement == "apart-polanka"
        assert ts.year == 2025
        assert ts.month == 1
        assert ts.rent_pln == 0.0
        assert ts.bills_pln == pytest.approx(expected_share)
        assert ts.total_due_pln == pytest.approx(expected_share)

    # 2. Mieszkanie z 1 najemcą
    manager.tenants = {
        "tenant-1": Tenant(
            name="Jan Nowak",
            apartment="apart-polanka",
            room="room-bigger",
            rent_pln=1500.0,
            deposit_pln=3000.0,
            date_agreement_from="2024-01-01",
            date_agreement_to="2025-12-31",
        )
    }
    single_settlements = manager.create_tenant_settlements(apt_settlement)
    assert len(single_settlements) == 1
    assert single_settlements[0].tenant == "tenant-1"
    assert single_settlements[0].bills_pln == 910.0
    assert single_settlements[0].total_due_pln == 910.0

    # 3. Mieszkanie bez żadnych najemców -> pusta lista
    manager.tenants = {}
    empty_settlements = manager.create_tenant_settlements(apt_settlement)
    assert empty_settlements == []
