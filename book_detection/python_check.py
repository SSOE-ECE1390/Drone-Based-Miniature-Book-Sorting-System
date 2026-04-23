import os
import sys
import subprocess
from pathlib import Path

print("="*70)
print("Deep Dependency Analysis for libh264decoder.pyd")
print("="*70)

project_dir = Path(__file__).parent.absolute()
pyd_file = project_dir / "libh264decoder.pyd"

if not pyd_file.exists():
    print("ERROR: libh264decoder.pyd not found!")
    sys.exit(1)

print(f"\nAnalyzing: {pyd_file}")
print(f"File size: {pyd_file.stat().st_size:,} bytes")

# Use dumpbin to check dependencies (comes with Visual Studio)
print("\n" + "="*70)
print("Checking dependencies with dumpbin...")
print("="*70)

# Try to find dumpbin
dumpbin_paths = [
    r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe",
    r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe",
    r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe",
]

dumpbin = None
for path in dumpbin_paths:
    if os.path.exists(path):
        dumpbin = path
        break

if dumpbin:
    try:
        result = subprocess.run(
            [dumpbin, '/DEPENDENTS', str(pyd_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(result.stdout)
        
        # Parse the dependencies
        lines = result.stdout.split('\n')
        dependencies = []
        in_deps_section = False
        
        for line in lines:
            if 'dependencies:' in line.lower():
                in_deps_section = True
                continue
            if in_deps_section and line.strip().endswith('.dll'):
                dll_name = line.strip()
                dependencies.append(dll_name)
        
        print("\n" + "="*70)
        print("Dependencies found:")
        print("="*70)
        
        missing_dlls = []
        for dll in dependencies:
            # Check if DLL exists in project dir or system
            if (project_dir / dll).exists():
                print(f"  ✓ {dll} (in project dir)")
            else:
                # Check system directories
                try:
                    import ctypes.util
                    dll_path = ctypes.util.find_library(dll.replace('.dll', ''))
                    if dll_path:
                        print(f"  ✓ {dll} (in system)")
                    else:
                        print(f"  ✗ {dll} MISSING!")
                        missing_dlls.append(dll)
                except:
                    print(f"  ? {dll} (unable to verify)")
        
        if missing_dlls:
            print("\n" + "="*70)
            print("MISSING DEPENDENCIES FOUND!")
            print("="*70)
            for dll in missing_dlls:
                print(f"  - {dll}")
            print("\nThese DLLs are required but not found.")
            print("\nMost likely missing:")
            print("  - Boost Python DLL (boost_python312-*.dll or similar)")
            print("  - Visual C++ Runtime (VCRUNTIME*.dll, MSVCP*.dll)")
            
    except subprocess.TimeoutExpired:
        print("Timeout running dumpbin")
    except Exception as e:
        print(f"Error running dumpbin: {e}")
else:
    print("dumpbin.exe not found. Cannot analyze dependencies.")
    print("\nAlternative: Download Dependencies tool from:")
    print("https://github.com/lucasg/Dependencies/releases")
    print("Then open libh264decoder.pyd with it to see missing DLLs")

print("\n" + "="*70)
print("Checking for Boost Python DLLs...")
print("="*70)

# Check for boost python DLLs
boost_patterns = [
    'boost_python*.dll',
    'boost_numpy*.dll'
]

found_boost = False
for pattern in boost_patterns:
    boost_dlls = list(project_dir.glob(pattern))
    if boost_dlls:
        found_boost = True
        for dll in boost_dlls:
            print(f"  ✓ {dll.name}")

if not found_boost:
    print("  ✗ No Boost Python DLLs found!")
    print("\n  This is likely the problem!")
    print("\n  Your libh264decoder.pyd was compiled with Boost.Python,")
    print("  but the Boost Python DLL is missing.")
    print("\n  SOLUTIONS:")
    print("  1. Copy boost_python312-vc143-mt-x64-*.dll to your project directory")
    print("     (Find it where Boost was installed, typically C:\\boost\\lib)")
    print("\n  2. Or rebuild without Boost (use pybind11 instead)")
    print("\n  3. Or add Boost lib directory to PATH")

print("\n" + "="*70)
print("Checking Visual C++ Runtime...")
print("="*70)

vcruntime_dlls = [
    'VCRUNTIME140.dll',
    'VCRUNTIME140_1.dll', 
    'MSVCP140.dll',
    'CONCRT140.dll'
]

for dll in vcruntime_dlls:
    try:
        import ctypes.util
        path = ctypes.util.find_library(dll.replace('.dll', ''))
        if path:
            print(f"  ✓ {dll} found in system")
        else:
            print(f"  ✗ {dll} NOT FOUND")
    except:
        print(f"  ? {dll} (unable to verify)")

print("\n" + "="*70)
print("\nRECOMMENDATION:")
print("="*70)
print("The most likely cause is MISSING BOOST PYTHON DLL.")
print("\nTo fix:")
print("1. Find boost_python312-vc143-mt-x64-*.dll on your system")
print("   (search C:\\boost, C:\\local, or wherever you installed Boost)")
print("2. Copy it to your project directory")
print("3. Try importing again")
print("\nIf you don't have Boost installed or can't find the DLL,")
print("you'll need to either:")
print("  - Install Boost properly")
print("  - Or rebuild the extension with pybind11 instead of Boost.Python")