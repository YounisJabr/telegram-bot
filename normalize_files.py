from main import normalize_number

def normalize_all_files():
    for risk_level in ['high_risk', 'medium_risk', 'unreported']:
        try:
            with open(f'data/{risk_level}_numbers.txt', 'r+', encoding='utf-8') as f:
                numbers = []
                for line in f:
                    num = line.strip()
                    if num:  # Skip empty lines
                        try:
                            normalized = normalize_number(num)
                            numbers.append(normalized)
                        except ValueError as e:
                            print(f"⚠️ Skipping invalid number {num}: {e}")
                
                f.seek(0)
                f.write('\n'.join(numbers))
                f.truncate()
            print(f"Normalized {risk_level}_numbers.txt")
        except FileNotFoundError:
            print(f"⚠️ File not found: data/{risk_level}_numbers.txt")

if __name__ == "__main__":
    normalize_all_files()