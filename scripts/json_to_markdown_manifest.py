import json
from pathlib import Path

def convert_json_to_markdown(json_path: Path, output_path: Path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    md = []
    md.append(f"# Архитектурный Манифест: {data['project_name']}")
    md.append(f"Версия системы: {data['version']}")
    md.append("\nЭтот документ описывает внутреннюю структуру и взаимосвязи модулей системы Марк.")
    
    md.append("\n## Основные компоненты и зависимости\n")

    for item in data['structure']:
        md.append(f"### 📄 Модуль: `{item['path']}`")
        if item['description']:
            md.append(f"**Описание**: {item['description']}")
        
        if item['classes']:
            md.append("- **Классы**:")
            for cls in item['classes']:
                methods_str = f" (Методы: {', '.join(cls['methods'])})" if cls['methods'] else ""
                desc = f" — {cls['description']}" if cls['description'] else ""
                md.append(f"  * `{cls['name']}`{methods_str}{desc}")
        
        if item['functions']:
            md.append("- **Функции**:")
            for fn in item['functions']:
                desc = f" — {fn['description']}" if fn['description'] else ""
                md.append(f"  * `{fn['name']}`{desc}")
        
        if item['dependencies']:
            # Filter internal dependencies to show only project connections
            internal_deps = [d for d in item['dependencies'] if any(p in d for p in ['core', 'layers', 'knowledge', 'queries', 'experience', 'api'])]
            if internal_deps:
                md.append(f"- **Связи**: {', '.join(internal_deps)}")
        
        md.append("\n---")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    root = Path.cwd()
    convert_json_to_markdown(root / "project_structure.json", root / "architecture_manifest.md")
    print(f"✅ Манифест успешно создан: architecture_manifest.md")

