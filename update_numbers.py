import re
import os
import sys
from main import COUNTRY_IDENTIFIERS

def detect_country(number):
    """Priority-based country detection"""
    cleaned = re.sub(r'\D', '', number)
    for country in COUNTRY_IDENTIFIERS:
        for pattern in country['patterns']:
            if (cleaned.startswith(pattern['prefix']) and 
                len(cleaned) == pattern['length']):
                return country['code']
    return "+966"  # Default to Saudi

def process_file(filename):
    """Process file with enhanced validation"""
    if not os.path.exists(filename):
        print(f"⚠️ File not found: {filename}")
        return 0

    updated = []
    changed_count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            num = line.strip()
            if not num:
                continue
                
            original = num
            if not num.startswith('+'):
                try:
                    country_code = detect_country(num)
                    num = f"{country_code}{re.sub(r'\D', '', num)}"
                    if num != original:
                        changed_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to process {num}: {e}")
                    continue
            
            updated.append(num)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated))
    
    return changed_count

def main():
    os.makedirs('data', exist_ok=True)
    total_changes = 0
    
    for risk_level in ['high_risk', 'medium_risk', 'unreported']:
        filename = f'data/{risk_level}_numbers.txt'
        changes = process_file(filename)
        total_changes += changes
        print(f"Processed {filename} - {changes} numbers updated")
    
    print(f"✅ Done! Total numbers updated: {total_changes}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)