import json
import os
import argparse
import sys

def load_templates(db_path):
    if not os.path.exists(db_path):
        return {}
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_templates(templates):
    print("Available Legal Templates (Mexico):")
    for key, data in templates.items():
        print(f"- {key}: {data['title']}")

def generate_doc(template_key, values, templates):
    if template_key not in templates:
        print(f"Error: Template '{template_key}' not found.")
        return None
    
    template_data = templates[template_key]
    content = template_data['content']
    
    # Simple replacement for placeholders in [PLACEHOLDER] format
    for key, value in values.items():
        # Match [Key] or [KEY] or [key]
        content = content.replace(f"[{key}]", value)
        content = content.replace(f"[{key.upper()}]", value)
    
    # For templates with underscores (heuristic)
    # This is a bit more complex as underscores can be of variable length
    # but for this demo we'll use simple string replacement if provided
    for key, value in values.items():
        if key in content:
             content = content.replace(key, value)

    return content

def main():
    parser = argparse.ArgumentParser(description="Mexican Legal Document Generator")
    subparsers = parser.add_subparsers(dest="command")
    
    # List command
    subparsers.add_parser("list", help="List available templates")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a document from a template")
    gen_parser.add_argument("--template", required=True, help="Template key (e.g., contrato_servicios)")
    gen_parser.add_argument("--data", help="JSON string with placeholder values")
    gen_parser.add_argument("--output", help="Output file path")

    args = parser.parse_all() if hasattr(parser, 'parse_all') else parser.parse_args()
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'templates.json')
    templates = load_templates(db_path)
    
    if args.command == "list":
        list_templates(templates)
    elif args.command == "generate":
        values = {}
        if args.data:
            try:
                values = json.loads(args.data)
            except json.JSONDecodeError:
                print("Error: Invalid JSON data.")
                sys.exit(1)
        
        doc = generate_doc(args.template, values, templates)
        if doc:
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(doc)
                print(f"Document generated at {args.output}")
            else:
                print(doc)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
