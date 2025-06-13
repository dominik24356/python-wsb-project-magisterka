import sqlite3
from werkzeug.security import generate_password_hash

try:
    print("[1] Łączenie z bazą danych...")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    print("[2] Tworzenie tabeli...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    print("[3] Dodawanie użytkowników...")
    uzytkownicy = [
        ("dominik", generate_password_hash("tajnehaslo1")),
        ("jakub", generate_password_hash("tajnehaslo2")),
        ("wojciech", generate_password_hash("tajnehaslo3"))
    ]
    c.executemany("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", uzytkownicy)

    print("[4] Zatwierdzanie i zamykanie połączenia...")
    conn.commit()
    conn.close()

    print("✔️ Baza danych 'users.db' została utworzona i użytkownicy dodani!")

except Exception as e:
    print(f"❌ Błąd podczas tworzenia bazy: {e}")
