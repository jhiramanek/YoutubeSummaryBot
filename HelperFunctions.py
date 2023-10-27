# from tkinter import INSERT
# from arrow import get
# from attr import validate
# from numpy import add, empty
from more_itertools import last

import os
import openai
import time
import json
from youtube_transcript_api import YouTubeTranscriptApi
from RecordJSON import *
from GPTMessages import *


def read_summary_from_file(JSON_FILE_PATH):
    summary = []
    areTagsProcessed = False
    number_processed_chunks = 0
    with open(JSON_FILE_PATH, 'r', encoding='UTF-8') as f:
        try:
            temp_file = json.load(f)
            for i in temp_file:
                for key, value in i.items():
                    # count processed chunks
                    if key == 'chunk_id':
                        number_processed_chunks += 1
                        print(f'Chunk_id_read = {value}')
                        # load processed summaries

                    if key == 'chunk_summary':
                        summary.append(value)
                        print("Updating Summary")

                    if key == 'tag':
                        areTagsProcessed = True
                        print("Tags are processed")

        except Exception as error:
            print("An exception occurred:", error)
        f.close

    print("number_of_processed_chunks: ", number_processed_chunks)

    return (summary, areTagsProcessed, number_processed_chunks)


def break_down_into_chunks(transcript):
    chunked_transcript = []
    for line in transcript:
        split_into_chunks(line, chunked_transcript)
    # Remove any empty chunk_transcript (keep if chunky monkeys)
    chunked_transcript = [chunk for chunk in chunked_transcript if chunk]
    return chunked_transcript

    return (summary, areTagsProcessed, number_processed_chunks)


def split_into_chunks(line, chunks):
    # 100 Tokens is 75 words... therefore 3500 Tokens = 2625 words
    # since the limit of openAI is 4,096 tokens, tokens we will use 2600 words.
    chunk_size = 2600
    words = line.split()
    if len(words) <= chunk_size:
        chunks.append(' '.join(words))
    else:
        chunk = ' '.join(words[:chunk_size])
        chunks.append(chunk)
        split_into_chunks(' '.join(words[chunk_size:]), chunks)


def get_chunked_transcript(video_id):

    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    output_transcript = ""
    for line in transcript:
        output_transcript += line['text'] + ' '
    # breakdown the output_transcript into 500 word chunks to nearest complete sentence
    output_transcript = output_transcript.split('\n')
    chunk_transcript = break_down_into_chunks(output_transcript)
    return chunk_transcript


def append_to_json_file(JSON_FILE_PATH, record_json, isLastChunk):

    with open(JSON_FILE_PATH, 'a') as f:
        # Serializing json
        f.write(record_json + '\n')
        # if last record close the json array
        if (isLastChunk):
            f.write(']'+'\n')
        else:
            f.write(','+'\n')
            f.close


def create_json_file_and_add(JSON_FILE_PATH, record_json, isLastChunk):

    with open(JSON_FILE_PATH, 'w') as f:
        # Serializing json
        f.write('[' + '\n')
        f.write(record_json)
        # if last record close the json array
        if (isLastChunk):
            f.write(']'+'\n')
        else:
            f.write(','+'\n')

    f.close


def process_transcript_using_gpt3(summary, title, video_id, num_processed_chunks, chunked_transcript, JSON_FILE_PATH):

    tempFileExists = os.path.exists(JSON_FILE_PATH)

    request_pause = 40

    for achunk in chunked_transcript:

        message = get_summary_message(achunk)

        num_chars = len(str(achunk))
        print(
            f'processing transcript chunk {num_processed_chunks} with length {num_chars} approx {num_chars*0.75} Tokens ...')

        # Measure the time before the API request is made
        start_time = time.time()

        # generate summary from chatGPT3
        gpt_chunk_summary_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message,
            temperature=0.1,
            max_tokens=1000,
            n=1,
            stop=None)

        # Measure the time after the API request is completed
        end_time = time.time()
        # Calculate time to sleep
        remaining_sleep_time = end_time - start_time

        chunk_summary_response = gpt_chunk_summary_response.choices[0].message.content

        summary.append(chunk_summary_response)

        record_json = get_record_json(
            num_processed_chunks, title, video_id, chunk_summary_response)

        # check if temp file with video_id exists if not create it
        if tempFileExists:
            isLastChunk = achunk == last(chunked_transcript)
            append_to_json_file(JSON_FILE_PATH, record_json, isLastChunk)
            print(chunk_summary_response)
            num_processed_chunks += 1

        else:
            isLastChunk = achunk == last(chunked_transcript)
            create_json_file_and_add(JSON_FILE_PATH, record_json, isLastChunk)

            # create new file and write first record
            print(chunk_summary_response)
            num_processed_chunks += 1
            tempFileExists = True

            # Pause the program for x seconds before making the next API request
    time.sleep(request_pause - remaining_sleep_time)

    # returns summary and number of processed chunks
    return (summary, num_processed_chunks)


def generate_tags_from_summary(chunked_summary):

    Tags = []
    for achunk in chunked_summary:
        msg = get_makeTag_message(achunk)
        try:
            tag_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=msg,
                temperature=0.1,
                max_tokens=1000,
                n=1,
                stop=None)

            Tags.append(tag_response['choices'][0]['message']['content'])
            return Tags

        except openai.error.RateLimitError:
            # Output the data from memory onto the console
            print("Rate Limit Error")
            return Tags
