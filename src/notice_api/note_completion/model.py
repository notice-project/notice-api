# ruff: noqa: RUF001

from typing import Sequence

from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from openai import OpenAI

from notice_api.core.config import settings

OpenAIClient = OpenAI(api_key=settings.OPENAI_API_KEY)

llm = ChatOpenAI(
    model="gpt-3.5-turbo-16k", temperature=0.3, api_key=settings.OPENAI_API_KEY
)

llm_stream = ChatOpenAI(
    model="gpt-3.5-turbo-16k",
    temperature=0.3,
    api_key=settings.OPENAI_API_KEY,
    streaming=True,
)

cleaning_template = """
- Eliminate redundant words from the following raw transcript
- The content of the raw transcript will be marked as such: RAW TRANSCRIPT ```(raw transcript content)```
- Words are considered redundant if it satisfy one of the following conditions:
    - 1. Time stamps
    - 2. Markings or abbriviations which seem to be generated by other speach-to-text/caption services. For example, "WEBVTT"

- RAW TRANSCRIPT ```{raw_transcript}```
"""

note_generation_template = """
- task：Your job is to generate bulletpoint notes from the provided transcript
    - input：
        - the latest transcript
        - the content of the transcript will be marked as such: transcript ```(transcript content)```
    - output：
        - represent the whole trancript content as bulletpoints without lost information
        - the bulletpoints should strictly follow the chronological order of the input transcript
        - output the bulletpoints using markdown
        - each content of the bulletpoints can only be one of the following: a single sentence, keyword(s), words used for formatting
        - a bulletpoint should be less than 60 characters. if it is longer that, split it into multiple sub-bulletpoints
        - sub-bulletpoints have additional tabs in front
        - the whole output should contain at least 1500 characters and be as detailed as possible
        - only output the bulletpoints and sub-bulletpoints texts
        - don't use the example output word for word
        - output format: "
            - <bulletpoint 1>
            - <bulletpoint 2>
                - <sub-bulletpoint 2-1>
                - <sub-bulletpoint 2-2>
                ...
            - <bulletpoint 3>
            ...
        "
        - example output: "
- Introduction to Algorithms lecture two
    - Erik Demaine loves algorithms
    - Today's topic: data structures
        - Multiple algorithms for free within data structures
    - Sequences, sets, linked lists, dynamic arrays
- Data Structures
    - Introduction to simple data structures
    - Difference between interface and data structure
        - Interface specifies what you want to do
        - Data structure specifies how to do it
    - Storing data and operations on data
        - Interface specifies what data can be stored
        - Data structure provides algorithms for supporting operations
    - Focus on two main interfaces: set and sequence
        - Set: store and search for values
        - Sequence: maintain a particular order of values
- Sequence Data Structure
    - Store n arbitrary things
    - Care about values and maintaining order
    - Today's focus: sequence data structure
- Static Sequence Interface
    - Number of items doesn't change
    - Operations: build, length, iteration, get, set
    - Build: create a new static sequence with specified items and order
    - Length: get the number of items in the sequence
    - Iteration: iterate through the items in the sequence
    - Get: retrieve the value at a specific index in the sequence
    - Set: update the value at a specific index in the sequence
        "

- transcript ```{transcript}```
"""

check_with_usernote_template = """
- task: Compare each line in the generated note with lines in the user knowledge
    - input:
        - the user knowledge, which will be marked as such: - user knowledge ```(user knowledge content)```
        - the generated note, which will be marked as such: - generated note ```(generated note content)```
    - output:
        - output each line in the generated note content, but at the end of each line, tell me the user knowledge which that generated note is referencing using a tag like such: <(referenced user knowledge)>
            - if you can't find any, output <N>
            - the <(referenced user knowledge)> tag STRICTLY ONLY contains lines from the input user knowledge, everything outside "- user knowledge ```(user knowledge content)```" is NOT user knowledge
        - don't output anything else besides the tags and the original lines from the generated note
        - example output: "
- Static sequence interface <N>
     - Number of items doesn't change <"- the number of items does not change">
     - Static array is the natural solution to this interface problem <N>
         - Data structures can be considered solutions <"- the data structures are the solutions to these kinds of problems">
         - Memory is an array of w-bit words <N>
     - Operations: build, length, iteration, get, set <"- for this case, we need operations build, length, iteration, get and set">
        "

- user knowledge: ```{usernote}```

- generated note: ```{generated_note}```
"""


def generate_note_langchain(transcript: str | Sequence[str], usernote: str) -> str:
    # 去除冗言贅字
    # prompt_template = PromptTemplate(
    #     input_variables=["raw_transcript"], template=cleaning_template
    # )
    # chain1 = LLMChain(llm=llm, prompt=prompt_template)

    # 整理成條列式
    prompt_template = PromptTemplate(
        input_variables=["transcript"], template=note_generation_template
    )
    chain2 = LLMChain(llm=llm, prompt=prompt_template)

    # 這部分你把prompt換成漢字季的筆記對比 我現在先用給我其中三點來測試
    # template1 = """give me three important part in this note
    # % note
    # {note}
    # """
    # prompt_template = PromptTemplate(input_variables=["note"], template=template1)
    # chain3 = LLMChain(llm=llm, prompt=prompt_template)

    # 串起三個部分
    # chain1 跑的時間很久目前先拔掉
    overall_chain = SimpleSequentialChain(chains=[chain2], verbose=True)
    return overall_chain.run("\n".join(transcript))


def generate_note_openai(transcript: str | Sequence[str], usernote: str, temparature: float = 0.7):
    # 整理成條列式
    note_generation_prompt = note_generation_template.format(
        transcript="\n".join(transcript)
    )
    response = OpenAIClient.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "user", "content": note_generation_prompt}],
        temperature=temparature,
    )
    generated_note = response.choices[0].message.content

    # 與使用者筆記做對照並標記
    check_with_usernote_prompt = check_with_usernote_template.format(
        usernote=usernote, generated_note=generated_note
    )
    response = OpenAIClient.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "user", "content": check_with_usernote_prompt}],
        temperature=0.0,
        stream=True,
    )

    check_string = ""  # 用來檢查目前收到的回應是否書要傳出去
    check_result = "<check result>\n"  # 紀錄完整的模型輸出
    for chunk in response:
        if chunk.choices[0].delta.content is None:
            # openai 回應結束
            break
        else:
            check_string += chunk.choices[0].delta.content
            check_result += chunk.choices[0].delta.content

            if '<N>' in check_string:
                index = check_string.find('<N>')
                yield check_string[:index]
                rest_of_string = check_string[index + len('<N>'):]
                check_string = rest_of_string

            elif '<' in check_string and '>' in check_string and check_string.find('>') > check_string.find('<'):
                index = check_string.find('>')
                rest_of_string = check_string[index + len('>'):]
                check_string = rest_of_string
    # 這個 function 最後會 yield 已經篩選過後的筆記

    # 以下可以用來 debug 模型原始輸出
    # yield check_result + "\n" 
    # yield '\n' + (generated_note or '')+'\n'
