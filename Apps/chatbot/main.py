from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import os
from io import BytesIO
import re
import base64
from openai import OpenAI
import iris
from llama_index.legacy import SimpleDirectoryReader, StorageContext, ServiceContext
from llama_index.legacy.indices.vector_store import VectorStoreIndex
from llama_iris import IRISVectorStore
app = Flask(__name__)


namespace="USER"
port = "1972"
hostname= "localhost"
username = "demo"
password = "demo"
CONNECTION_STRING = f"iris://{username}:{password}@{hostname}:{port}/{namespace}"

@app.route('/')
def index():
    return render_template('chatbot.html')

@app.route('/process_voice', methods=['POST'])
def process_voice():
    data = request.get_json()
    # Receive transcribed speech text from frontend
    speech_text = data.get('speechText', '')  
    client = OpenAI(api_key="")
    processed_text = ""

    #captures user prompt for a meal planner
    #"""Uses OpenAI API to check if the user is asking to plan an exercise schedule."""
    prompt = f"""
    Determine if the user is asking you to plan for them what to exercise based on the sentence below.
    Respond only with 'Yes' or 'No'.
    Sentence: '{speech_text}'
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    result = response.choices[0].message.content
    if result.lower() == "yes":
        print("user wants to plan a exercise scheduler")
        #reconnect to vector store
        vector_store = IRISVectorStore.from_params(
        connection_string=CONNECTION_STRING,
        table_name="patient_report",
        embed_dim=1536,  # openai embedding dimension
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        query_engine = index.as_query_engine()
        #extract medical history for patient exercise planner
        patient_info = query_engine.query("Provide Medical History of patient")
        print(patient_info)
        #gpt-4 generation for exercise planner
        exercise_prompt = f"""
            Plan a weekly exercise planner taking into to account the following medical history {patient_info}, use singlish to make it sound casual 
            """
        exercise_response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": exercise_prompt}],
        stream=False
        )
        print(exercise_response)
        processed_text = exercise_response.choices[0].message.content

    #captures user prompt for a meal planner
    #"""Uses OpenAI API to check if the user is asking to plan an meal schedule."""
    prompt2 = f"""
        Determine if the user is asking you to plan for them their meals based on the sentence below.
        Respond only with 'Yes' or 'No'.
        Sentence: '{speech_text}'
        """
    response2 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt2}],
        stream=False
    )
    result2 = response2.choices[0].message.content
    if result2.lower() == "yes":
        print("user wants to plan a meal planner")
        #reconnect to vector store
        vector_store = IRISVectorStore.from_params(
        connection_string=CONNECTION_STRING,
        table_name="patient_report",
        embed_dim=1536,  # openai embedding dimension
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        query_engine = index.as_query_engine()
        #extract dietary concern of patient for meal planner
        patient_info = query_engine.query("Provide Dietary concerns of patient")
        print(patient_info)
        #gpt-4 generation for meal planner
        meal_prompt = f"""
            Plan a weekly meal planner taking into to account the following dietary concerns {patient_info}, use singlish to make it sound casual 
            """
        meal_response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": meal_prompt}],
        stream=False
        )
        print(meal_response)
        processed_text = meal_response.choices[0].message.content

    #if user did not ask for meal planner or exercise planner
    prompt3 = f""" 
        You are emotional AI assistant, respond to {speech_text} using singlish
    """
    if processed_text == "":
        response3 = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt3}],
            stream=False
        )

        processed_text = response3.choices[0].message.content

    # if is_chinese(processed_text) is True:
    #     tts = gTTS(text=processed_text, lang='zh-cn')
    # else:
    tts = gTTS(text=processed_text, lang='en',tld='co.in')
    # Save the speech to a temporary file on the disk
    temp_filename = "temp_audio.mp3"
    tts.save(temp_filename)  # Save to a temporary file
    # Read the temporary file into a BytesIO object (in-memory file)
    with open(temp_filename, 'rb') as f:
            audio_file = BytesIO(f.read())
    # Clean up the temporary file
    os.remove(temp_filename)
    audio_base64 = base64.b64encode(audio_file.getvalue()).decode('utf-8')
    print(processed_text)
    # Return the speech text and audio as base64 in JSON
    return jsonify({
                "speechText": processed_text,
                "audioData": audio_base64
            })
                    
            # Send the audio file back as a response (MP3 format)
            # return send_file(audio_file, mimetype='audio/mp3', as_attachment=False)
    #     else:
    #         return jsonify({"message": "Failed to process text in Google Colab"})
    # else:
    #     return jsonify({"message": "No speech text received"})

if __name__ == '__main__':
    app.run(debug=True)
