from src.models import (
    Apartment,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantSettlement,
    Transfer,
)


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(
        self, apartment_key: str, year: int | None = None, month: int | None = None
    ) -> float | None:
        if month is not None and not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Month must be between 1 and 12.")
        if apartment_key not in self.apartments:
            return None

        cost = 0.0
        for bill in self.bills:
            if month is not None and year is not None:
                if (
                    bill.apartment == apartment_key
                    and bill.settlement_year == year
                    and bill.settlement_month == month
                ):
                    cost += bill.amount_pln
            else:
                if year is not None:
                    if bill.apartment == apartment_key and bill.settlement_year == year:
                        cost += bill.amount_pln
                else:
                    if bill.apartment == apartment_key:
                        cost += bill.amount_pln

        return cost

    def create_apartment_settlement(
        self, apartment_key: str, year: int, month: int
    ) -> ApartmentSettlement | None:
        total_bills = self.get_apartment_costs(apartment_key, year, month)
        if total_bills is None:
            return None

        total_rent = 0.0
        total_due = total_rent + total_bills

        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=total_due,
        )

    def create_tenant_settlements(
        self, apartment_settlement: ApartmentSettlement
    ) -> list[TenantSettlement]:
        apartment_tenants = [
            tenant_key
            for tenant_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_settlement.apartment
        ]

        if not apartment_tenants:
            return []

        bills_per_tenant = apartment_settlement.total_bills_pln / len(apartment_tenants)

        settlements = []
        for tenant_key in apartment_tenants:
            rent = 0.0
            total_due = rent + bills_per_tenant
            balance = -total_due

            settlements.append(
                TenantSettlement(
                    tenant=tenant_key,
                    apartment_settlement=apartment_settlement.apartment,
                    month=apartment_settlement.month,
                    year=apartment_settlement.year,
                    rent_pln=rent,
                    bills_pln=bills_per_tenant,
                    total_due_pln=total_due,
                    balance_pln=balance,
                )
            )

        return settlements
