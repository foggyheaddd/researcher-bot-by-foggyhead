import os
BOT_TOKEN = os.getenv("BOT_TOKEN", "8495367324:AAHNP5u3wrRRCxUBOa6VAi3xNZi_ctKaO0U")
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY", "1rW615gmemSRK-vaQx5C6sGbv1feLH8V_LaLYAd_7rP0")

# === Видео (ВСТАВЬ СВОЙ file_id!) ===
VIDEO_POSITIVE = "BAACAgIAAxkBAAICN2kL1bz7VXNK91QuiB02wKYnBUxxAAKxiQACHTxgSPMGU-HfQZlKNgQ"  # ← от @RawDataBot, блок "video"
VIDEO_NEGATIVE = "BAACAgIAAxkBAAICOWkL1esI1rvKs6R0ESGJkd3UBA9lAAKyiQACHTxgSEsnAoj7IYE9NgQ"  # ← от @RawDataBot, блок "video"

#import json


#def get_google_credentials_json_string(file_path="credentials.json"):

    #with open(file_path, "r", encoding="utf-8") as f:
     #   data = json.load(f)
    # json.dumps автоматически удаляет переносы и форматирует как одну строку
    #json_string = json.dumps(data, separators=(',', ':'))
   # return json_string


# Пример использования:
#if __name__ == "__main__":
 #   result = get_google_credentials_json_string("credentials.json")
  #  print(result)