# ruff: noqa: RUF001

from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.llms.openai import OpenAI
from langchain.prompts import PromptTemplate

from notice_api.core.config import settings

llm = OpenAI(temperature=0.3, api_key=settings.OPENAI_API_KEY)


def gen_model(input1: str, input2: str):
    # 去除冗言贅字
    template = """Eliminate redundant words from this transcript
    % TRANSCRIPT
    {transcript}
    """
    prompt_template = PromptTemplate(input_variables=["transcript"], template=template)
    chain1 = LLMChain(llm=llm, prompt=prompt_template)

    # 整理成條列式
    writingstemplate = """
        - task：Your job is to generate bulletpoint notes from the provided transcript
            - input：
                - the latest transcript
                - the content of the transcript will be marked as such: % writings ```(transcript content)```
            - output：
                - represent the whole trancript content as bulletpoints without lost information
                - the bulletpoints should strictly follow the chronological order of the input transcript
                - output the bulletpoints using markdown
                - each content of the bulletpoints can only be one of the following: a single sentence, keyword(s), words used for formatting
                - if a bulletpoint sentence is too long, split it into multiple sub-bulletpoints
                - only output the bulletpoints and sub-bulletpoints texts
                - don't use the example output word for word
                - output format: [
                    - <bulletpoint 1>
                    - <bulletpoint 2>
                        - <sub-bulletpoint 2-1>
                        - <sub-bulletpoint 2-2>
                        ...
                    - <bulletpoint 3>
                    ...
                ]
                - example output: [
    - Introduction to Algorithms
        - Lecture two
        - Erik Demaine loves algorithms
    - Data Structures
        - Sequences, sets, linked lists, dynamic arrays
        - Simple data structures
        - Beginning of several data structures
    - Interface vs Data Structure
        - Interface specifies what you want to do
        - Data structure specifies how to do it
    - Operations on Data Structures
        - Storing data
        - Specifying operations and their meanings
        - Algorithms for supporting operations
    - Two main interfaces: set and sequence
        - Set: maintaining data in sorted order, searching for a key
        - Sequence: maintaining a particular sequence, storing n things
    - Two main approaches: arrays and pointers
    - Static Sequence Interface
        - Number of items doesn't change
        - Operations: build, length, iteration, get, set
    - Static Array
        - Solution to the static sequence interface problem
        - No static arrays in Python, only dynamic arrays
    - Word RAM model of computation
                        ]

    % writings ```{writings}```
    """
    prompt_template = PromptTemplate(
        input_variables=["writings"], template=writingstemplate
    )
    chain2 = LLMChain(llm=llm, prompt=prompt_template)

    # 這部分你把prompt換成漢字季的筆記對比 我現在先用給我其中三點來測試
    '''
    template1 = """give me three important part in this note
    % note
    {note}
    """
    prompt_template = PromptTemplate(input_variables=["note"], template=template1)
    chain3 = LLMChain(llm=llm, prompt=prompt_template)'''

    # 串起三個部分
    overall_chain = SimpleSequentialChain(chains=[chain1, chain2], verbose=True)
    return overall_chain.run(input1)
