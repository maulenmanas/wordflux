from wordflux import DocxTranslator
from wordflux.utils.spinner import Spinner
import os
import sys
import argparse
import yaml
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_config(config_path: str) -> dict:
    """Đọc config từ file YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"✓ Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"✗ Config file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"✗ Error parsing YAML config: {e}")
        raise

def main():
    config = load_config("config.yaml")
    parser = argparse.ArgumentParser(description="Translate a DOCX file")
    parser.add_argument("input_file", type=str, help="Input DOCX file")
    parser.add_argument("--output_dir", type=str, help="Output directory", default="output")
    args = parser.parse_args()

    input_file = args.input_file
    output_dir = args.output_dir
    
    provider = config.get("provider", "openai")
    
    if provider == "gemini":
        api_key = config.get("gemini_api_key")
        if not api_key:
             # Fallback if user put generic key in openai_api_key but switched provider
             api_key = config.get("openai_api_key")
    else:
        api_key = config.get("openai_api_key")

    if not api_key:
        raise ValueError(f"API key not found for provider {provider}. Please check your config.yaml file.")
        
    model = config.get("model")
    source_lang = config.get("source_lang")
    target_lang = config.get("target_lang")
    max_chunk_size = config.get("max_chunk_size")
    max_concurrent = config.get("max_concurrent")
    base_url = config.get("openai_api_base_url")
    rpm_limit = config.get("rpm_limit", 0)
    tpm_limit = config.get("tpm_limit", 0)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Determine list of files to process
    files_to_process = []
    if os.path.isdir(input_file):
        for root, dirs, files in os.walk(input_file):
            for file in files:
                if file.lower().endswith(".docx") and not file.startswith("~$"):
                     files_to_process.append(os.path.join(root, file))
        if not files_to_process:
            print(f"⚠️ No DOCX files found in directory: {input_file}")
            sys.exit(0)
        print(f"📂 Found {len(files_to_process)} DOCX files in directory '{input_file}'")
    else:
        if not os.path.exists(input_file):
             print(f"❌ Input file not found: {input_file}")
             sys.exit(1)
        files_to_process.append(input_file)

    print(f"⚙️ Starting translation process for {len(files_to_process)} file(s)...\n")

    for idx, doc_path in enumerate(files_to_process, 1):
        file_name = os.path.basename(doc_path)
        print(f"[{idx}/{len(files_to_process)}] Processing: {file_name}")
        
        spinner = Spinner(f"Translate {file_name}")
        spinner.start()
        try:
            docx_translator = DocxTranslator(doc_path, output_dir, api_key, model, source_lang, target_lang, max_chunk_size, max_concurrent, base_url, provider, rpm_limit, tpm_limit)
            docx_translator.translate()
            spinner.stop()
            print(f"✅ Completed: {file_name}\n→ Output: {docx_translator.get_output_path()}\n")
        except Exception as e:
            spinner.stop()
            print(f"❌ Failed to translate {file_name}: {e}\n")
            # Continue to next file instead of exiting
            continue

    print("🎉 All tasks finished!")

if __name__ == "__main__":
    main()