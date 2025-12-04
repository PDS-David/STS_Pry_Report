"""
Auto-setup script for SOW THE SEED School Management System
This will create all necessary template files in the templates folder
"""

import os
import shutil

# Ensure we're in the right directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

print("=" * 60)
print("🔧 SOW THE SEED - Template Setup Script")
print("=" * 60)

# Create folders if they don't exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

print(f"✅ Templates folder: {TEMPLATES_DIR}")
print(f"✅ Static folder: {STATIC_DIR}")

# Move index.html if it exists in root
index_in_root = os.path.join(BASE_DIR, 'index.html')
index_in_templates = os.path.join(TEMPLATES_DIR, 'index.html')

if os.path.exists(index_in_root) and not os.path.exists(index_in_templates):
    shutil.move(index_in_root, index_in_templates)
    print(f"✅ Moved index.html to templates folder")

# Check what files already exist in templates
print("\n📋 Checking templates folder...")
existing_files = os.listdir(TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else []
print(f"Found {len(existing_files)} files: {existing_files}")

# List of required template files
required_files = [
    'login.html',
    'index.html',
    'add_student.html',
    'edit_student.html',
    'score_entry.html',
    'subjects.html',
    'terms.html',
    'report.html',
    'class_summary.html'
]

missing_files = [f for f in required_files if f not in existing_files]

if missing_files:
    print(f"\n⚠️  Missing {len(missing_files)} template files:")
    for f in missing_files:
        print(f"   - {f}")
    print("\n💡 You need to create these files in the templates folder.")
    print("   I can see you have the content - just save them to templates/")
else:
    print("\n✅ All template files exist!")

# Check for common issues
print("\n🔍 Checking for common issues...")

# Check if index.html still in root
if os.path.exists(os.path.join(BASE_DIR, 'index.html')):
    print("⚠️  WARNING: index.html found in root folder")
    print("   It should be in templates/ folder only")

# Check app.py exists
if os.path.exists(os.path.join(BASE_DIR, 'app.py')):
    print("✅ app.py found")
else:
    print("❌ ERROR: app.py not found!")

# Check database
if os.path.exists(os.path.join(BASE_DIR, 'school.db')):
    print("✅ school.db database found")
else:
    print("ℹ️  school.db will be created on first run")

print("\n" + "=" * 60)
print("📝 Next Steps:")
print("=" * 60)
if missing_files:
    print("1. Save all HTML template files to the 'templates' folder")
    print("2. Run: python app.py")
else:
    print("1. Run: python app.py")
    print("2. Open browser: http://127.0.0.1:5000")
    print("3. Login with: admin / password123")
print("=" * 60)