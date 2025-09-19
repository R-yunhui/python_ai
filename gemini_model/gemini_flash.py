from google import genai
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyD9iAUKqNHWerRAQJSpmcq-cGelmX9AtPs")


def generate_image(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=[prompt],
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save("generated_image.png")


def chat_with_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=[prompt]
    )

    print(response.text)


if __name__ == "__main__":
    # generate_image("Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme")

    chat_with_gemini("你知道西游记这本书吗? 大概介绍一下，200字左右吧。")
