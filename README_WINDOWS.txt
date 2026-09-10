NEW LAXMI MEDICAL & GENERAL STORE
Windows build package

WHAT IS INCLUDED
- medical_store.py: final desktop application source
- build_windows.bat: creates MedicalStore.exe on Windows
- medical_store_preview.html: browser preview

BUILD THE EXE ON WINDOWS
1. Install Python 3.10+ on Windows.
2. Extract this folder.
3. Double-click build_windows.bat.
4. The finished file is dist\\MedicalStore.exe.

The app stores data locally in medical_store.db beside the application.

FUNCTIONS VERIFIED IN THE SOURCE
- Purchase-bill-style stock entry
- Supplier/invoice fields
- Category dropdown with all requested categories
- Pack-aware inventory: 10S/15S/20S etc.
- Paid + free pack stock converted to individual units
- Purchase price + GST = selling price
- Per-unit billing: pack selling price divided by pack size
- Stock deduction after billing
- Four-calendar-month expiry warning
- Expired and low-stock dashboard counts
- Sales history
- Bill generation and print button

IMPORTANT
The environment used to create this package is not Windows, so a native Windows .exe cannot be compiled and tested here. The included build script uses PyInstaller on Windows to produce the executable.
