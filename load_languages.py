import json

# Load the language scorecard database
with open('languages.json') as f:
    languages = json.load(f)

def get_language_info(language_name):
    for lang in languages:
        if lang['language'].lower() == language_name.lower():
            return lang
    return None

# Example usage:
if __name__ == '__main__':
    lang = get_language_info('C/C++')
    if lang:
        print(f"Milan's comments for {lang['language']}:\n{lang['milan_comments']}")
    else:
        print("Language not found.") 