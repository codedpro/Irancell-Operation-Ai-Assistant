"""
Main file for the Irancell's Operation Operator project

this is only a Dummy preview from what will happen in main project

"""
from recorder import speech_to_text
import json
import asyncio
import pygame
from io import BytesIO
import requests
import base64
import soundfile as sf
import sounddevice as sd
import time
import numpy as np
from IPython.display import display
from Tapas import tapas_question_answer
from data import extract_data_from_excel
headers = {"Authorization": "Bearer APIKEY"}
async def save_audio(audio_bytes, filename):
    with open(filename, 'wb') as f:
        f.write(audio_bytes)
    await play_wav_file(filename)

async def play_wav_file(filename):
    wave_data, fs = sf.read(filename, dtype='float32')
    sd.play(wave_data, fs)
    sd.wait()

async def speech2text():
    url = "https://api.edenai.run/v2/audio/speech_to_text_async"
    data = {
        "providers": "openai",
        "language": "en",
    }
    files = {'file': open("/Users/codedpro/Desktop/Irancell/Irancell Operation Agent/demo/audio/recording.wav", 'rb')}
    response = requests.post(url, data=data, files=files, headers=headers)
    result = json.loads(response.text)
    return result['results']['openai']['text']

async def textGen(text: str):
    url = "https://api.edenai.run/v2/text/chat"
    payload = {
        "providers": "openai/gpt-4-32k-0314",
        "text": text,
        "chatbot_global_action": "You are MTN Irancell's Network Assistant bot that gives reports to The Managers with datas that you have",
        "previous_history": [],
        "temperature": 0.0,
        "max_tokens": 1500
    }
    response = requests.post(url, json=payload, headers=headers)
    result = json.loads(response.text)
    return result['openai/gpt-4-32k-0314']['generated_text']

async def makedecision(text: str):
    keyword_pairs = {
            ("network", "status"): get_network_status,
            ("test", "testx"): get_network_status,
        }
    for keywords, action in keyword_pairs.items():
        if all(keyword in text for keyword in keywords):
            return await confirm_action(text, action)
    return await normal_action(text)

async def get_network_status(text):
    data = {
        "availability": ["99.1", "99.5", "98.8", "99.21", "99.34", "99.98", "99.89", "99.25"],
        "Province": ["mazandaran", "golestan", "gilan", "ardebil", "zanjan", "Khorasan razavi", "Khorasan jonobi", "khorasan shomali"],
        "region": ["1", "1", "1", "2", "2", "3", "3", "3"]
    }
    queries = [
        "what is the average of the availabilitys of Provinces inside region 1",
        "what is the average of the availabilitys of Provinces inside region 2",
        "what is the average of the availabilitys of Provinces inside region 3",
        "which Provinces have an availability lower than 99?",
        "what Provinces are in region 1?",
        "what Provinces are in region 2?",
        "what Provinces are in region 3?",
    ]
    
    results = tapas_question_answer(data, queries)
    
    for result in results:
        if result["aggregation"] == "AVERAGE":
            cell_values = [float(value) for value in result["predicted_answer"].split(", ")]
            result["predicted_answer"] = sum(cell_values) / len(cell_values)

    return await table_prompt_generation(results, text)

async def table_prompt_generation(results, question_text):
    prompt = "Use these informations as your reference for responding as the informations about Networks in MTN Irancell, your answers must be based on the informations and numbers that we have and you must analyse the datas for answering the question\n\n"
    for result in results:
        prompt += f"{result['query']}:\n{result['predicted_answer']}\n\n"
    prompt += f"\nHere is the Question:\n\n{question_text}\n\nYour answer must be like meteorology or reading news."
    
    return prompt

async def normal_action(text):
    file_path = "/Users/codedpro/Desktop/Irancell/Irancell Operation Agent/demo/CS-RAN -update3_2023120107_1701403565102.xlsx"

    keyword_mapping = {
        ("availability", "network"): {
            "header": "2G_TCH_AVAILABILITY_IR(%)",
            "function": extract_data_from_excel,
            "category": "TCH Availability of the network"
        },
        "TCH": {
            "header": "2G_TCH_AVAILABILITY_IR(%)",
            "function": extract_data_from_excel,
            "category": "TCH Availability of the network"
        },
        "CSSR": {
            "header": "2G_CSSR_IR(%)",
            "function": extract_data_from_excel,
            "category": "2G CSSR Availability"
        },
        "DCR": {
            "header": "2G_DCR_IR(%)",
            "function": extract_data_from_excel,
            "category": "2G DCR Availability"
        },
        "HOSR": {
            "header": "2G_HOSR_IR(%)",
            "function": extract_data_from_excel,
            "category": "2G HOSR Availability"
        },
        "ERLANG": {
            "header": "2G_ERLANG_IR(Erl)",
            "function": extract_data_from_excel,
            "category": "2G ERLANG Availability"
        },
    }

    prompt = f"Here is the question you have to answer:\n{text}\n\nUse these informations as your reference for responding as the informations about Networks in MTN Irancell and dont explain too much:\n\n"

    triggered_categories = set()

    for keywords, mapping in keyword_mapping.items():
        category = mapping.get("category")
        if all(keyword in text for keyword in keywords) and category not in triggered_categories:
            header = mapping["header"]
            extract_function = mapping["function"]
            result = extract_function(file_path, header)

            prompt += f"\nCategory: {category}\n"

            for info in result:
                header_name = list(info.keys())[0]
                availability_data = None
                for key in info[header_name]:
                    if header in key:
                        availability_data = info[header_name][key]
                        break
                
                if availability_data is None:
                    continue
                
                region_data = info[header_name]['region']
                for i in range(len(availability_data)):
                    prompt += f"Date: {header_name}, Region: {region_data[i]}, Availability: {availability_data[i]}%\n"

            triggered_categories.add(category)

    if not triggered_categories:
        prompt += "There is no data currently found in the database about that question. Your answer must be based on your own knowledge."

    print(prompt)
    return prompt



async def confirm_action(text, action):
    action_info = {
        "get_network_status": {
            "prompt": "Do You Confirm That You Want Get Status of The Network ?",
            "action": get_network_status
        },
    }
    action_name = action.__name__
    if action_name in action_info:
            confirmation_prompt = action_info[action_name]["prompt"]
            associated_action = action_info[action_name]["action"]
            
            system_response = await voiceGen(confirmation_prompt)
            wav_filename = "/Users/codedpro/Desktop/Irancell/Irancell Operation Agent/demo/audio/system_voice2.wav"
            await save_audio(system_response, wav_filename)
            print("go ahead im listening")
            speech_to_text()
            print("Done listening")
            user_response = await speech2text()
            confirmation_keywords = ["yes", "confirm", "absolutely", "yeah", "sure"]
            if any(keyword in user_response.lower() for keyword in confirmation_keywords):
                return await associated_action(text)
            else:
                print("Action canceled")
                return "Action canceled"
    else:
        print("Action not recognized")
        return "Action not recognized"

async def voiceGen(text: str):
    url = "https://api.edenai.run/v2/audio/text_to_speech"
    payload = {
        "providers": "openai",
        "language": "en",
        "option": "MALE",
        "text": text,
    }
    response = requests.post(url, json=payload, headers=headers)

    result = response.json()
    audio_bytes = base64.b64decode(result['openai']['audio'])
    return audio_bytes

async def main():
    while True:
        print("go ahead im listening")
        speech_to_text()
        print("Done listening")
        start_time = time.time()
        text = "what is the relation ship between DCR and TCH availability"
        print("User: " + text)
        decision = await makedecision(text)
        system = await textGen(decision)
        print("System: " + system)
        voice_bytes = await voiceGen(system)
        wav_filename = "/Users/codedpro/Desktop/Irancell/Irancell Operation Agent/demo/audio/system_voice.wav"
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed timce: {elapsed_time} seconds")
        await save_audio(voice_bytes, wav_filename)
        time.sleep(30)
if __name__ == "__main__":
    asyncio.run(main())

    
