import re
from datetime import datetime


class sorting_algorithm:
    def __init__(self):
        self.callnumbers = []

    def validate_callnumber(self, callnumber: str) -> bool:
        if not callnumber or callnumber[0].isdigit():
            return False

        invalid_chars = set('!@#$%^&*(),?":{}|<>')
        for ch in callnumber:
            if ch in invalid_chars:
                return False

        return True

    def add_callnumber(self, callnumber: str) -> dict:
        if not self.validate_callnumber(callnumber):
            raise ValueError("Invalid call number format.")
        self.callnumbers.append(callnumber)

    def sort_callnumbers(self) -> list:
        sorted_list = self.callnumbers[:]
        for i in range(len(sorted_list)):
            for j in range(0, len(sorted_list) - i - 1):
                if self.compare(sorted_list[j], sorted_list[j + 1]) > 0:
                    sorted_list[j], sorted_list[j + 1] = (
                        sorted_list[j + 1],
                        sorted_list[j],
                    )
        return sorted_list

    def compare(self, cn1: str, cn2: str) -> int:
        """
        Compares two call numbers.
        Returns: 1 if cn1 > cn2, -1 if cn1 < cn2, 0 if equal
        """
        parsed1 = self.parse_callnumber(cn1)
        parsed2 = self.parse_callnumber(cn2)

        if parsed1["Class Letters"] != parsed2["Class Letters"]:
            return 1 if parsed1["Class Letters"] > parsed2["Class Letters"] else -1

        if parsed1["Class Number"] != parsed2["Class Number"]:
            return (
                1
                if float(parsed1["Class Number"]) > float(parsed2["Class Number"])
                else -1
            )

        il1 = parsed1["Intermediate Letters"] or ""
        il2 = parsed2["Intermediate Letters"] or ""
        if il1 != il2:
            return 1 if il1 > il2 else -1

        if parsed1["Decimal Number"] != parsed2["Decimal Number"]:
            return 1 if parsed1["Decimal Number"] > parsed2["Decimal Number"] else -1

        ts1 = parsed1["Third Sequence"] or ""
        ts2 = parsed2["Third Sequence"] or ""
        if ts1 != ts2:
            return 1 if ts1 > ts2 else -1

        y1 = parsed1["Year"] or 0
        y2 = parsed2["Year"] or 0
        if y1 != y2:
            return 1 if y1 > y2 else -1

        if parsed1["Volume"] != parsed2["Volume"]:
            return 1 if parsed1["Volume"] > parsed2["Volume"] else -1

        if parsed1["Copy"] != parsed2["Copy"]:
            return 1 if parsed1["Copy"] > parsed2["Copy"] else -1

        return 0

    def parse_callnumber(self, callnumber: str) -> dict:
        remaining = callnumber.strip().replace(" ", "")
        parsed = {
            "Class Letters": None,
            "Class Number": None,
            "Intermediate Letters": None,
            "Decimal Number": 0,
            "Third Sequence": None,
            "Year": None,
            "Volume": 0,
            "Copy": 0,
        }

        # 1. Class Letters
        m = re.match(r"^([A-Z]+)", remaining)
        if not m:
            raise ValueError("Invalid format: missing class letters.")
        parsed["Class Letters"] = m.group(1)
        remaining = remaining[len(m.group(1)) :]

        # 2. Class Number
        m = re.match(r"^(\d+(\.\d+)?)", remaining)
        if m:
            parsed["Class Number"] = m.group(1)
            remaining = remaining[len(m.group(1)) :]
        else:
            raise ValueError("Invalid format: missing class number.")

        # 3. Intermediate Letters
        m = re.match(r"^\.?([A-Z]+)", remaining)
        if m:
            parsed["Intermediate Letters"] = m.group(1)
            remaining = remaining[len(m.group(0)) :]

        # 4. Decimal Number
        m = re.match(r"^(\d+)", remaining)
        if m:
            parsed["Decimal Number"] = int(m.group(1))
            remaining = remaining[len(m.group(1)) :]

        # 5. Year (4-digit at end)
        m = re.search(r"(\d{4})$", remaining)
        if m:
            candidate = int(m.group(1))
            current_year = datetime.now().year
            if 1000 <= candidate <= current_year:
                parsed["Year"] = candidate
                remaining = remaining[: remaining.rfind(m.group(1))]

        # 6. Third Sequence
        m = re.match(r"^([A-Z0-9]+)", remaining)
        if m:
            parsed["Third Sequence"] = m.group(1)
            remaining = remaining[len(m.group(1)) :]

        # 7. Volume (v. or V.)
        m = re.search(r"v\.?(\d+)", remaining, re.IGNORECASE)
        if m:
            parsed["Volume"] = int(m.group(1))

        # 8. Copy (c. or C.)
        m = re.search(r"c\.?(\d+)", remaining, re.IGNORECASE)
        if m:
            parsed["Copy"] = int(m.group(1))

        return parsed


if __name__ == "__main__":
    sorter = sorting_algorithm()

    test_callnumbers = [
        "A12BQ12D",
        "A12W132004",
        "A12.5",
        "A12W131990",
        "A12W132004 v.2 c.1",
        "A12W132004 v.1 c.2",
        "B10A12003",
        "AA12",
        "A12",
        "QA76.73.P98 2020",
        "QA76.73.J38 2018 v.1",
        "12345",
        "QA76!",
        "A12W13X2004",
    ]

    print("=== VALIDATION & PARSING TESTS ===")
    for cn in test_callnumbers:
        try:
            valid = sorter.validate_callnumber(cn)
            if valid:
                sorter.add_callnumber(cn)
                parsed = sorter.parse_callnumber(cn)
                print(f"{cn:<25} VALID  → {parsed}")
            else:
                print(f"{cn:<25} INVALID FORMAT")
        except Exception as e:
            print(f"{cn:<25} ERROR: {e}")

    print("\n=== SORTED ORDER ===")
    sorted_list = sorter.sort_callnumbers()
    for idx, cn in enumerate(sorted_list, start=1):
        print(f"{idx:2d}. {cn}")

    print("\n=== COMPARISON LOGIC TEST ===")
    pairs_to_compare = [
        ("A12BQ12D", "A12W132004"),
        ("A12W132004", "A12W131990"),
        ("A12W132004 v.1 c.1", "A12W132004 v.1 c.2"),
        ("A12W132004 v.1", "A12W132004 v.2"),
        ("AA12", "A12"),
    ]
    for a, b in pairs_to_compare:
        result = sorter.compare(a, b)
        if result > 0:
            relation = ">"
        elif result < 0:
            relation = "<"
        else:
            relation = "="
        print(f"{a:<25} {relation} {b}")
