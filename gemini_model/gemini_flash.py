from google import genai

if __name__ == "__main__":
    client = genai.Client(api_key="AIzaSyD9iAUKqNHWerRAQJSpmcq-cGelmX9AtPs")

    cur_file = client.files.upload(file="C:\\Users\\Admin\\Downloads\\a.mp4")

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=[cur_file, "Summarize this video. Then create a quiz with an answer key based on the information in this video."]
    )

    print(response.text)

