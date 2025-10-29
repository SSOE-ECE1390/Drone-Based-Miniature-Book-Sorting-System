import re

class sorting_algorithm:
    def __init__(self):
        self.callnumbers = []

    def validate_callnumber(self, callnumber: str) -> bool:
        """
        Validates if the given call number is in a correct format.
        :param callnumber: The call number to validate.
        :return: True if the call number is valid, False otherwise.
        """
        if callnumber and callnumber[0].isdigit():
            return False


        invalid_chars = set('!@#$%^&*(),?":{}|<>')
        for ch in callnumber:
            if ch in invalid_chars:
                return False

        return True
    
    def add_callnumber(self, callnumber: str) -> dict:
        """
        Parses a call number into its components.
        :param callnumber: The call number to parse.
        :return: A dictionary with the parsed components.
        """
        if not self.validate_callnumber(callnumber):
            raise ValueError("Invalid call number format.")

        else:
            self.callnumbers.append(callnumber)
    
    def sort_callnumbers(self) -> list:
        """
        Sorts a list of call numbers based on their parsed components.
        :param callnumbers: A list of call numbers to sort.
        :return: A sorted list of call numbers.
        """
        sorted_list = self.callnumbers[:]  # make a copy

        for i in range(len(sorted_list)):
            for j in range(0, len(sorted_list) - i - 1):
                if self.callnumber_greaterthan(sorted_list[j], sorted_list[j + 1]):
                    sorted_list[j], sorted_list[j + 1] = sorted_list[j + 1], sorted_list[j]

        return sorted_list
            
    def callnumber_greaterthan(self, cn1: str, cn2: str) -> bool:
        """
        Compares two call numbers.
        Returns True if cn1 > cn2.
        """   
        parsed1= self.parse_callnumber(cn1)
        parsed2= self.parse_callnumber(cn2)

        if parsed1["Class Letters"] != parsed2["Class Letters"]:
            return parsed1["Class Letters"] > parsed2["Class Letters"] 
        #will AA come before A? AA vs B?

        if parsed1["Class Number"] != parsed2["Class Number"]:
            return float(parsed1["Class Number"]) > float(parsed2["Class Number"])
        
        if parsed1["Intermediate Letters"] != parsed2["Intermediate Letters"]:
            return (parsed1["Intermediate Letters"] or "") > (parsed2["Intermediate Letters"] or "")

        if parsed1["Decimal Number"] != parsed2["Decimal Number"]:
            return parsed1["Decimal Number"] > parsed2["Decimal Number"]

        if parsed1["Third Sequence"] != parsed2["Third Sequence"]:
            return (parsed1["Third Sequence"] or "") > (parsed2["Third Sequence"] or "")

        if parsed1["Year"] != parsed2["Year"]:
            return (parsed1["Year"] or 0) > (parsed2["Year"] or 0)
        
        if parsed1["Volume"] != parsed2["Volume"]:
            return parsed1["Volume"] > parsed2["Volume"]
        
        if parsed1["Copy"] != parsed2["Copy"]:
            return parsed1["Copy"] > parsed2["Copy"]
        
    def parse_callnumber(self, callnumber: str) -> dict:
        """
        Parses a call number into its six logical components:
        Class Letters, Class Number, Intermediate Letters,
        Decimal Number, Third Sequence, and Year.
        """

        remaining = callnumber.strip()
        parsed = {
            "Class Letters": None,
            "Class Number": None,
            "Intermediate Letters": None,
            "Decimal Number": 0,
            "Third Sequence": None,
            "Year": None
        }

        # ---------- 1. Class Letters ----------
        m = re.match(r'^([A-Z]+)', remaining)
        if not m:
            raise ValueError("Invalid format: missing class letters.")
        parsed["Class Letters"] = m.group(1)
        remaining = remaining[len(m.group(1)):]  # consume

        # ---------- 2. Class Number ----------
        m = re.match(r'^(\d+(\.\d+)?)', remaining)
        if m:
            parsed["Class Number"] = m.group(1)
            remaining = remaining[len(m.group(1)):]  # consume
        else:
            raise ValueError("Invalid format: missing class number.")

        # ---------- 3. Intermediate Letters ----------
        m = re.match(r'^([A-Z]+)', remaining)
        if m:
            parsed["Intermediate Letters"] = m.group(1)
            remaining = remaining[len(m.group(1)):]  # consume

        # ---------- 4. Decimal Number ----------
        m = re.match(r'^(\d+)', remaining)
        if m:
            parsed["Decimal Number"] = int(m.group(1))
            remaining = remaining[len(m.group(1)):]  # consume
        else:
            parsed["Decimal Number"] = 0

        # ---------- 5. Year (4-digit at end) ----------
        m = re.search(r'(\d{4})$', remaining)
        year = None
        if m:
            candidate = int(m.group(1))
            current_year = datetime.now().year
            if 1000 <= candidate <= current_year:
                year = candidate
                remaining = remaining[:remaining.rfind(m.group(1))]  # remove year
        parsed["Year"] = year

        # ---------- 6. Third Sequence ----------
        m = re.match(r'^([A-Z0-9]+)', remaining)
        if m:
            parsed["Third Sequence"] = m.group(1)
            remaining = remaining[len(m.group(1)):]  # consume
            
        # ---------- 7 & 8. Volume and Copy Identifiers ----------
        parsed["Volume"] = 0
        parsed["Copy"] = 0

        # Detect volume (v. or V.) followed by digits
        m = re.search(r'v\.\s*(\d+)', remaining, re.IGNORECASE)
        if m:
            parsed["Volume"] = int(m.group(1))
            remaining = remaining.replace(m.group(0), '')

        # Detect copy (c. or C.) followed by digits
        m = re.search(r'c\.\s*(\d+)', remaining, re.IGNORECASE)
        if m:
            parsed["Copy"] = int(m.group(1))
            remaining = remaining.replace(m.group(0), '')

        return parsed
    
if __name__ == "__main__":
    from datetime import datetime

    sorter = sorting_algorithm()

    # ---------- Test Data ----------
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
        "12345",            # Invalid: no leading letters
        "QA76!",           # Invalid: special character     
        "A12W13X2004",    # duplicate test
    ]

    # ---------- Add and Parse ----------
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

    # ---------- Sorting Test ----------
    print("\n=== SORTED ORDER ===")
    sorted_list = sorter.sort_callnumbers()
    for idx, cn in enumerate(sorted_list, start=1):
        print(f"{idx:2d}. {cn}")

    # ---------- Pairwise Comparison Sanity Check ----------
    print("\n=== COMPARISON LOGIC TEST ===")
    pairs_to_compare = [
        ("A12BQ12D", "A12W132004"),
        ("A12W132004", "A12W131990"),
        ("A12W132004 v.1 c.1", "A12W132004 v.1 c.2"),
        ("A12W132004 v.1", "A12W132004 v.2"),
        ("AA12", "A12"),
    ]
    for a, b in pairs_to_compare:
        result = sorter.callnumber_greaterthan(a, b)
        relation = ">" if result else "<="
        print(f"{a:<25} {relation} {b}")
