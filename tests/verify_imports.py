import sys
print('Python:', sys.version)
print()

results = []

tests = [
    ('langgraph', 'langgraph'),
    ('langchain', 'langchain'),
    ('langchain_core', 'langchain_core'),
    ('langchain_google_genai', 'langchain_google_genai'),
    ('langchain_openai', 'langchain_openai'),
    ('langchain_text_splitters', 'langchain_text_splitters'),
    ('chromadb', 'chromadb'),
    ('pydantic', 'pydantic'),
    ('pydantic_settings', 'pydantic_settings'),
    ('tavily', 'tavily'),
    ('sentence_transformers', 'sentence_transformers'),
    ('streamlit', 'streamlit'),
    ('pytest', 'pytest'),
    ('openai', 'openai'),
    ('dotenv', 'dotenv'),
]

for name, mod in tests:
    try:
        m = __import__(mod)
        ver = getattr(m, '__version__', 'installed')
        results.append(f'  PASS  {name:<30} {ver}')
    except Exception as e:
        results.append(f'  FAIL  {name:<30} {e}')

print('\n'.join(results))
print()

# Now test our own modules
print('--- Testing project imports ---')
sys.path.insert(0, '.')
own_tests = [
    ('app.config.settings', 'from app.config.settings import settings; print("  settings OK:", settings.app_name)'),
    ('app.utils.logger', 'from app.utils.logger import get_logger; logger = get_logger("test"); print("  logger OK")'),
    ('app.utils.helpers', 'from app.utils.helpers import truncate_text, safe_json_parse; print("  helpers OK")'),
    ('app.utils.validators', 'from app.utils.validators import validate_user_idea; print("  validators OK")'),
]

for name, stmt in own_tests:
    try:
        exec(stmt)
    except Exception as e:
        print(f'  FAIL  {name}: {e}')
