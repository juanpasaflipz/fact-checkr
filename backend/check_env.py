
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_APP_SECRET",
    "TWITTER_BEARER_TOKEN",
    "SERPER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY"
]

print("Checking environment variables in .env...")
all_present = True
for var in required_vars:
    value = os.getenv(var)
    if not value or value.startswith("your_") or value == "":
        print(f"❌ {var} is MISSING or default")
        all_present = False
    else:
        # Print only first 4 chars for security
        masked = value[:4] + "..." if len(value) > 4 else "***"
        print(f"✅ {var} is set ({masked})")

if all_present:
    print("\n🎉 All critical environment variables are set!")
else:
    print("\n⚠️ Some variables are missing. Functionality will be limited.")
