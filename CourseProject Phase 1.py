
from datetime import datetime
from dataclasses import dataclass
import os
import sys
from typing import Optional


DATA_FILE = os.path.join(os.path.dirname(__file__), 'employees.txt')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.txt')


def parse_tax_rate(s: str) -> float:
    s = s.strip()
    if s.endswith('%'):
        s = s[:-1]
    v = float(s)
    if v > 1:
        v = v / 100.0
    return v


def money(v: float) -> str:
    return f"${v:,.2f}"


def get_employee_name() -> str:
    return input("Employee name: ").strip()


def get_hours() -> float:
    while True:
        s = input("Hours worked: ").strip()
        try:
            val = float(s)
            if val < 0:
                print("Hours cannot be negative.")
                continue
            return val
        except ValueError:
            print("Please enter a valid number for hours (e.g. 40 or 12.5).")


def get_hourly_rate() -> float:
    while True:
        s = input("Hourly rate: ").strip()
        try:
            val = float(s)
            if val < 0:
                print("Hourly rate cannot be negative.")
                continue
            return val
        except ValueError:
            print("Please enter a valid hourly rate (e.g. 12.50).")


def get_income_tax_rate() -> float:
    while True:
        s = input("Income tax rate (e.g. 20 or 0.2 or 20%): ").strip()
        try:
            r = parse_tax_rate(s)
            if r < 0 or r > 1:
                print("Please enter a reasonable tax rate between 0 and 100%.")
                continue
            return r
        except Exception:
            print("Please enter a valid tax rate (percent or decimal).")


def get_date_range():
    """Prompt for From and To dates in mm/dd/yyyy and return them as strings.
    This function validates the format and will re-prompt on invalid input.
    """
    while True:
        frm = input("From date (mm/dd/yyyy): ").strip()
        to = input("To date (mm/dd/yyyy): ").strip()
        try:
            
            datetime.strptime(frm, "%m/%d/%Y")
            datetime.strptime(to, "%m/%d/%Y")
            return frm, to
        except Exception:
            print("Please enter dates in mm/dd/yyyy format. Try again.")


def calculate_pay(hours: float, rate: float, tax_rate: float):
    gross = hours * rate
    taxes = gross * tax_rate
    net = gross - taxes
    return gross, taxes, net


def display_employee(name: str, hours: float, rate: float, gross: float, tax_rate: float, taxes: float, net: float):
    print()
    print(f"Employee: {name}")
    print(f"Hours worked: {hours}")
    print(f"Hourly rate: {money(rate)}")
    print(f"Gross pay: {money(gross)}")
    print(f"Income tax rate: {tax_rate:.2%}")
    print(f"Income taxes: {money(taxes)}")
    print(f"Net pay: {money(net)}")
    print("-" * 40)


def process_records(records: list) -> dict:
    
    totals = {
        'employees': 0,
        'hours': 0.0,
        'gross': 0.0,
        'taxes': 0.0,
        'net': 0.0,
    }
    for rec in records:
        gross, taxes, net = calculate_pay(rec['hours'], rec['rate'], rec['tax_rate'])
        print()
        print(f"From date: {rec['from']}")
        print(f"To date:   {rec['to']}")
        display_employee(rec['name'], rec['hours'], rec['rate'], gross, rec['tax_rate'], taxes, net)

        totals['employees'] += 1
        totals['hours'] += rec['hours']
        totals['gross'] += gross
        totals['taxes'] += taxes
        totals['net'] += net

    return totals

def append_record_to_file(frm: str, to: str, name: str, hours: float, rate: float, tax_rate: float, uid: Optional[str] = None):
    """Append a single record to the data file in pipe-delimited format.
    Format: from|to|name|hours|rate|tax_rate
    """
    
    try:
        frm_dt = datetime.strptime(frm, "%m/%d/%Y")
        to_dt = datetime.strptime(to, "%m/%d/%Y")
        frm_s = frm_dt.strftime("%m/%d/%Y")
        to_s = to_dt.strftime("%m/%d/%Y")
    except Exception:
        
        frm_s = frm
        to_s = to

    
    
    if uid:
        line = f"{uid}|{frm_s}|{to_s}|{name}|{hours}|{rate}|{tax_rate}\n"
    else:
        line = f"{frm_s}|{to_s}|{name}|{hours}|{rate}|{tax_rate}\n"
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(line)


def load_existing_ids() -> set:
    """Read DATA_FILE and return a set of existing user ids.

    This expects the file to use the extended format where the first field
    is an id: id|from|to|name|hours|rate|tax_rate. Lines in the old 6-field
    format are ignored for id collection to remain backward compatible.
    """
    ids = set()
    if not os.path.exists(DATA_FILE):
        return ids
    with open(DATA_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 7:
                ids.add(parts[0])
    return ids


def get_employee_id(existing_ids: set) -> str:
    """Prompt for a user id, validating it isn't already in existing_ids."""
    while True:
        uid = input("Employee ID: ").strip()
        if not uid:
            print("ID cannot be empty. Try again.")
            continue
        if uid in existing_ids:
            print("That ID already exists. Enter a different ID.")
            continue
        return uid


def load_existing_user_ids() -> set:
    """Read USERS_FILE and return a set of existing user ids.

    File format: id|password|auth_code (pipe-delimited). Lines that don't
    match are skipped.
    """
    ids = set()
    if not os.path.exists(USERS_FILE):
        return ids
    with open(USERS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 3:
                ids.add(parts[0])
    return ids


@dataclass
class Login:
    """Simple container for a user login record."""
    uid: str
    password: str
    authorization: str


def load_all_users() -> list:
    """Return a list of Login objects from USERS_FILE (empty if file missing)."""
    users = []
    if not os.path.exists(USERS_FILE):
        return users
    with open(USERS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) < 3:
                continue
            uid, pwd, auth = parts[0], parts[1], parts[2]
            users.append(Login(uid, pwd, auth))
    return users


def append_user_to_file(uid: str, password: str, auth_code: str):
    """Append a user record to USERS_FILE in pipe-delimited format.

    Format: id|password|auth_code
    """
    line = f"{uid}|{password}|{auth_code}\n"
    with open(USERS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)


def collect_user_accounts():
    """Interactive loop to collect user id, password, and auth code.

    Terminates when user types 'End' (case-insensitive) for the id. Validates
    that ID is unique (reads existing file into a set) and that auth_code is
    either 'Admin' or 'User' (case-insensitive). Writes accepted records to
    USERS_FILE and adds the id to the in-memory set.
    """
    print('\nUser account entry - type End as the ID to finish.')
    existing = load_existing_user_ids()
    while True:
        uid = input('Enter User ID (or End to finish): ').strip()
        if uid.lower() == 'end':
            break
        if not uid:
            print('User ID cannot be empty.')
            continue
        if uid in existing:
            print('That User ID already exists. Choose another.')
            continue

        password = input('Enter password: ').strip()
        if not password:
            print('Password cannot be empty.')
            continue

        auth = input('Enter authorization code (Admin or User): ').strip()
        if auth.lower() not in ('admin', 'user'):
            print("Authorization code must be 'Admin' or 'User'. Try again.")
            continue
        
        auth_norm = 'Admin' if auth.lower() == 'admin' else 'User'

        append_user_to_file(uid, password, auth_norm)
        existing.add(uid)
        print(f'User {uid} added.')

    
    display_all_users()


def display_all_users():
    """Read `users.txt` and display user id, password, and authorization code.

    This reads the file line-by-line and prints each user record in a compact
    table. Lines that don't match the expected format are skipped.
    """
    print()
    print("Existing user accounts:")
    users = load_all_users()
    if not users:
        print("(no user accounts found)")
        return
    for u in users:
        print(f"ID: {u.uid}    Password: {u.password}    Auth: {u.authorization}")


def perform_login() -> Login:
    """Perform an interactive login using records from USERS_FILE.

    Reads all users into a list, prompts for user id and password, validates
    both, and returns a Login object on success. On failure the function will
    print an error message and exit the program.
    """
    users = load_all_users()
    if not users:
        print("No users found. Please create user accounts first.")
        sys.exit(1)

    
    user_map = {u.uid: u for u in users}

    uid = input("Login - Enter user ID: ").strip()
    if not uid:
        print("No user ID entered. Exiting.")
        sys.exit(1)

    pwd = input("Enter password: ").strip()

    user = user_map.get(uid)
    if user is None:
        print("User ID not found. Exiting.")
        sys.exit(1)

    if pwd != user.password:
        print("Password does not match. Exiting.")
        sys.exit(1)

    
    login = Login(uid=user.uid, password=user.password, authorization=user.authorization)
    print(f"Login successful. Authorization: {login.authorization}")
    return login



def run_report(login: Optional[Login] = None):
    """Prompt for a From date (or 'All') and read the data file, printing
    the records that match. Compute gross, taxes and net for each and a final
    totals summary.
    """
    
    while True:
        choice = input("Enter From date to report on (mm/dd/yyyy) or 'All': ").strip()
        if choice.lower() == 'all':
            filter_all = True
            break
        try:
            parsed = datetime.strptime(choice, "%m/%d/%Y")
            
            choice = parsed.strftime("%m/%d/%Y")
            filter_all = False
            break
        except Exception:
            print("Please enter dates in mm/dd/yyyy format or 'All'.")

    
    totals = {
        'employees': 0,
        'hours': 0.0,
        'gross': 0.0,
        'taxes': 0.0,
        'net': 0.0,
    }

    
    if login is not None:
        print()
        print(f"Logged in as ID: {login.uid}    Password: {login.password}    Auth: {login.authorization}")
    if not os.path.exists(DATA_FILE):
        print("No employee records file found.")
        return totals

    with open(DATA_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            
            if len(parts) == 6:
                frm, to, name, hours_s, rate_s, tax_rate_s = parts
            elif len(parts) >= 7:
                
                _, frm, to, name, hours_s, rate_s, tax_rate_s = parts[:7]
            else:
                continue
            if (not filter_all) and (frm != choice):
                continue
            try:
                hours = float(hours_s)
                rate = float(rate_s)
                tax_rate = float(tax_rate_s)
            except Exception:
                
                continue

            gross, taxes, net = calculate_pay(hours, rate, tax_rate)
            print()
            print(f"From date: {frm}")
            print(f"To date:   {to}")
            display_employee(name, hours, rate, gross, tax_rate, taxes, net)

            totals['employees'] += 1
            totals['hours'] += hours
            totals['gross'] += gross
            totals['taxes'] += taxes
            totals['net'] += net

   
    display_summary(totals, login=login)
    return totals


def display_summary(totals: dict, login: Optional[Login] = None):
    """Display totals read from the totals dictionary.
    Expected keys: 'employees', 'hours', 'gross', 'taxes', 'net'.
    """
    
    if login is not None:
        print()
        print(f"Logged in as ID: {login.uid}    Password: {login.password}    Auth: {login.authorization}")

    print()
    print("Summary for all employees:")
    print(f"Total employees: {totals.get('employees', 0)}")
    print(f"Total hours worked: {totals.get('hours', 0.0)}")
    print(f"Total gross pay: {money(totals.get('gross', 0.0))}")
    print(f"Total income taxes: {money(totals.get('taxes', 0.0))}")
    print(f"Total net pay: {money(totals.get('net', 0.0))}")


def main():
    
    login = perform_login()

    
    existing_ids = load_existing_ids()

    
    if login.authorization == 'Admin':
        print("Payroll entry - enter employee data. Type 'End' for the name to finish.")
        records = []
        while True:
            name = get_employee_name()
            if name.lower() == 'end':
                break
            if not name:
                print("Name cannot be empty. Try again.")
                continue

            
            uid = get_employee_id(existing_ids)

            frm, to = get_date_range()
            
            try:
                frm_dt = datetime.strptime(frm, "%m/%d/%Y")
                to_dt = datetime.strptime(to, "%m/%d/%Y")
                frm = frm_dt.strftime("%m/%d/%Y")
                to = to_dt.strftime("%m/%d/%Y")
            except Exception:
                pass

            hours = get_hours()
            rate = get_hourly_rate()
            tax_rate = get_income_tax_rate()

            records.append({
                'id': uid,
                'from': frm,
                'to': to,
                'name': name,
                'hours': hours,
                'rate': rate,
                'tax_rate': tax_rate,
            })
            
            try:
                append_record_to_file(frm, to, name, hours, rate, tax_rate, uid=uid)
                existing_ids.add(uid)
            except Exception as e:
                print(f"Warning: could not write record to file: {e}")
    else:
        print(f"User '{login.uid}' logged in with view-only access. You may view reports but cannot enter data.")

    print()
    
    run_report(login=login)

if __name__ == '__main__':
    main()
