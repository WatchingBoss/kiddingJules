import os
import glob
import re

def clean_text(text):
    lines = text.strip().split('\n')
    cleaned_lines = []

    date = ""
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', line):
            date = line.split('T')[0]
            continue

        if line.startswith('@'):
            continue

        if line in ['▪Читать', '▪ Читать', '▪Video', '▪ Видео', '▪ 1 часть']:
            continue

        cleaned_lines.append(line)

    res = "\n".join(cleaned_lines).strip()
    # remove multiple blank lines
    res = re.sub(r'\n{3,}', '\n\n', res)
    return date, res

def main():
    base_dir = "text_summery/python_ru"
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return

    years = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    for year in sorted(years):
        files = glob.glob(os.path.join(base_dir, year, "*.txt"))

        md_content = f"# Полезная информация за {year} год\n\n"

        has_content = False
        for f in sorted(files):
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()

            blocks = content.split('============================================================')
            for block in blocks:
                date, text = clean_text(block)
                if text and len(text) > 5:
                    has_content = True
                    md_content += f"## {date}\n\n{text}\n\n---\n\n"

        if has_content:
            with open(f"{year}.md", "w", encoding="utf-8") as out_file:
                out_file.write(md_content)

if __name__ == "__main__":
    main()
