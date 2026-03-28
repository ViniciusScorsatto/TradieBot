from __future__ import annotations

from invoicebot.services.storage import Repository


FIRST_NAMES = (
    "Mia", "Noah", "Aria", "Luca", "Ella", "Finn", "Ruby", "Hugo", "Isla", "Leo",
    "Zoe", "Mason", "Sophie", "Jack", "Ava", "Max", "Harper", "Theo", "Willow", "James",
)

LAST_NAMES = (
    "Taylor", "Wilson", "Ngata", "Morgan", "Harris", "Bennett", "Clark", "Cooper", "Jones", "Fraser",
)

COMPANY_PREFIXES = (
    "North", "Summit", "Atlas", "Harbour", "Southern", "Urban", "Blue", "Prime", "Craft", "Metro",
)

COMPANY_SUFFIXES = (
    "Projects", "Electrical", "Plumbing", "Property", "Build", "Maintenance", "Fitout", "Contracting", "Interiors", "Roofing",
)

STREETS = (
    "Queen Street", "Cuba Street", "George Street", "Trafalgar Street", "Victoria Avenue",
    "Karamu Road", "Main South Road", "Devon Street", "High Street", "Marine Parade",
)

CITIES = (
    "Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga",
    "Dunedin", "Nelson", "Rotorua", "Whangarei", "New Plymouth",
)


def seed_mock_clients(repo: Repository, user_id: str, *, count: int = 50) -> int:
    created = 0
    existing_names = {client.name for client in repo.list_clients(user_id)}

    for index in range(count):
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index // len(FIRST_NAMES)) % len(LAST_NAMES)]
        client_name = f"{first_name} {last_name}"
        if client_name in existing_names:
            client_name = f"{client_name} {index + 1}"

        company = f"{COMPANY_PREFIXES[index % len(COMPANY_PREFIXES)]} {COMPANY_SUFFIXES[index % len(COMPANY_SUFFIXES)]}"
        email = f"{first_name.lower()}.{last_name.lower()}{index + 1}@example.nz"
        phone = f"+64 21 {700000 + index:06d}"
        address = f"{12 + index} {STREETS[index % len(STREETS)]}, {CITIES[index % len(CITIES)]}"

        repo.add_client(
            user_id,
            name=client_name,
            company=company,
            email=email,
            phone=phone,
            address=address,
        )
        created += 1
        existing_names.add(client_name)

    return created
