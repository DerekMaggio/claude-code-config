# /// script
# dependencies = [
#   "extract-msg",
#   "beautifulsoup4",
# ]
# ///

import extract_msg
import sys
import re
from bs4 import BeautifulSoup

def clean_whitespace(text):
    # Regex: Look for 3 or more newline characters (with potential whitespace between them)
    # and replace them with exactly 2 newlines.
    return re.sub(r'(\n\s*){3,}', '\n\n', text)

def process_msg(file_path):
    try:
        msg = extract_msg.Message(file_path)
        
        # Prefer HTML for better structural parsing, fallback to plain text
        if msg.htmlBody:
            soup = BeautifulSoup(msg.htmlBody, "html.parser")
            # Get text but try to preserve some block structure
            body_content = soup.get_text(separator='\n')
        else:
            body_content = msg.body

        # Apply the whitespace collapse logic
        cleaned_body = clean_whitespace(body_content)

        md_output = [
            f"# Email Thread: {msg.subject}",
            f"- **Latest From:** {msg.sender}",
            f"- **Date:** {msg.date}",
            "\n## Content & Thread History\n",
            "---",
            cleaned_body,
            "\n---"
        ]
        
        if msg.attachments:
            md_output.append("\n## Attachments Identified")
            for att in msg.attachments:
                md_output.append(f"- {att.getFilename()}")

        return "\n".join(md_output)
    except Exception as e:
        return f"Error processing {file_path}: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    # Output the final cleaned string to stdout
    print(process_msg(sys.argv[1]))