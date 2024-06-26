# -*- coding: utf-8 -*-
"""STSOAPS.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/13R78aJ74Kel9nvp6Xpw6BgJGchCLZuW0

# Speech -> Text -> SOAP -> Search Notebook

***A proof of concept for automated veterinary scribing technology.***

## 1. Install dependencies

We will leverage OpenAI's Whisper model for transcription and GPT-4 transformer model for SOAP note generation via their API. See https://platform.openai.com/docs/introduction for general API information. For examples of calling Whisper in Python, see https://github.com/openai/openai-python#audio-whisper. For calling GPT-4 in Python, see https://github.com/openai/openai-python#chat-completions.

For a vector database and embeddings (used to test search functionality over the generated notes), we will leverage [qdrant-python](https://github.com/qdrant/qdrant-client) in conjunction with their newly released [fastembed](https://github.com/qdrant/fastembed) library. This leverages BAAI's general embedding model which is more performant and accurate than Ada and free. In production, this would mean huge memory and speed savings and moderate cost savings (embeddings are cheap) in comparison to using OpenAI. For examples on how to use the search/embedding functionality, see: https://github.com/qdrant/qdrant-client#fast-embeddings--simpler-api.
"""

!pip install openai
!pip install qdrant-client[fastembed]

"""# 2. Import libraries"""

# configuration (securely access secret keys)
from google.colab import userdata
from google.colab import drive
drive.mount('/content/drive')

# core imports
from qdrant_client import QdrantClient
from openai import OpenAI

"""# 3. Initialize clients"""

# NOTE: we are running an in-memory qdrant test client. It is trivial to switch
# this out later to an on-disk version.
client = QdrantClient(":memory:")

# NOTE: you must first create an OpenAI account and get an API key. Then, you
# must click on the key icon in the left margin of this page (directly under
# "{x}") and create a secret with name "OPENAI_API_KEY" and value equal to your
# newly created API key. Then, you need to toggle "NotebookAccess" on for the
# secret.
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=userdata.get("OPENAI_API_KEY"),
)

# You can now use the qdrant client API and call OpenAI completion/audio
# transcription endpoints...

"""# 4. Audio -> SOAP Demo

We will first need an audio file for transcription. We will transcribe it with Whisper. Then we will transform the raw transcription to SOAP notes with GPT-4 and a descriptive prompt explaining what SOAP notes are. We can probably simply get away with literally copying and pasting a document like [this](https://www.vetmed.wisc.edu/wp-content/uploads/2019/07/soapwriting.pdf) into the prompt and perhaps providing a single example (I bet the example is unnecessary, so I wouldn't waste time on it for this PoC unless the quality of generated notes is empirically bad). Afterwards, we will need to review the quality of the generated SOAP notes. If it's not good, we need to collect more examples and manually edit the generated notes for each sample until the model is able to produce high quality notes.
"""

# Import openai library and use the transcribe() function to convert sample
# audio clip into text using whisper-1 model.

# import openai
audio_file= open("/content/Remy.m4a", "rb")
# NOTE: prompting with a limited dictionary of words that it is observed to
# transcribe incorrectly aids the model in recognizing them at transcription
# time. See https://platform.openai.com/docs/guides/speech-to-text/improving-reliability.
# This is a bit finnicky and doesn't work too well but we can test further post
# processing with GPT-4 or using semantic/lexical search and matching (fuzzy
# match or Levenshtein distance). For PoC, this is fine.
transcript = client.audio.transcriptions.create(file=audio_file, model="whisper-1", prompt="Hobin, lymph nodes, distemper, lepto")
print(transcript.text)

# TO-DO: Use text output from transcription to generate SOAP notes
# by sending into GPT.
# Other model option is gpt-4

import openai
MODEL = "gpt-3.5-turbo"

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Please convert the following text into SOAP notes for a veterinary appointment:" + transcript.text},
    ],
    temperature=0,
)

print(response.choices[0].message.content)

# Experimental Section
# TODO: pass template in system message
# TODO: generate each section in a separate request (and potentially pass different instructions / templates to each request)
system_message = """You are a veterinary medical scribe that will convert provider-patient interaction transcriptions to SOAP notes.

Tips for SOAP Writing
The VMTH physical exam sheet uses a check list system, but in practice, you will want
to develop a systematic written format to make sure that you describe all relevant exam
findings, even when they are normal.
During your 4th year, in order to develop your ability to generate differential lists, you
should initially list out all problems and your top 3 rule-outs for each problem. As you
gain experience with cases and SOAP writing, you will be able to group certain problems
together for one list of differentials, but to start, list them out with their differentials.Then
you can determine whether one differential could explain all of the important problems.
SOAP format:

SUBJECTIVE
  subjective findings – how does your patient generally look today (bright, alert, responsive, dull, depressed, etc., compared with yesterday if applicable)

OBJECTIVE
all objective findings. Findings are simply reported here with no assessment. Every clinician has a slightly different take, but here is a general example:
  1st line – T, P, R, BCS, body weight, mucous membranes, CRT, hydration status
  EENT – (eyes, ears, nose, throat)
  PLNS – (peripheral lymph nodes)
  H/L – (heart, lungs)
  ABD – (abdomen, rectal exam findings)
  UG – (urogenital, rectal exam – prostate or urethral palpation per rectum)
  MS– (musculoskeletal)
  Integ - integument
  N – (basic neurologic exam – not a full exam, but general assessment of mentation, gait, cranial nerves)
Some parts of the SOAP are more thorough depending on the presenting complaint:
  1) NEURO – (full neurologic exam – mentation, gait, cranial nerves, reflexes, etc.)
  2) ORTHO – (this is not a separate section, it falls under the MSI section, but may be much more thorough with a complaint of lameness)
Example of a objective section from a normal physical exam:
  T 100.1 , P 80 , R pant; BW – 24.5 kg, BCS 5/9; m.m. pink, moist, CRT < 2sec, hydrated
  EENT – no evidence of dental calculus, no nasal discharge, no other significant findings
  PLNS – peripheral LNs are normal in size, and no firm or painful LNs were identified
  H/L – normal sinus rhythm, no murmurs ausculted, pulses strong and synchronous; no
  evidence of increased respiratory rate or effort, bronchovesicular sounds are normal
  ABD – soft, non-painful, no palpable organomegaly, masses, or other abnormalities;
  normal rectal exam with no palpable masses, and normal brown stool on exam glove
  UG – moderate sized bladder; prostate is normal size, symmetric, and non-painful
  MSI – no evidence of lameness, ideal BCS; nice hair coat, no abnormal findings
  NEURO – normal gait and mentation, CNs normal; full neurologic exam not performed
If a patient is hospitalized, the OBJECTIVE section is also where you put any lab results, imaging results, or other diagnostic testing results after the exam findings.
EX:
  CBC – Low PCV 20% (37-55), High MCV 82 fl (60-78), Low MCHC 30 g/dL (32-36),
  Low TP 5 g/dL (6-7.9), normal platelets 392,000, normal leukogram (WBC 12,000).
  *Note, that not every value is written down, but all abnormals, and any relevant normals
  are written (it is nice to know that when you think an animal may have blood loss, that
  the platelets are normal, details make it easier to form a helpful differential list that way).

ASSESSMENT
assessment of your subjective and objective findings. Again, each clinician has a
different take on the format of this, but when you are starting, the easiest thing is to list
each problem (A1, A2, A3, etc.), and a list of rule-outs for each problem.
EX:
  Ginger is a 4 y o S golden retriever who was presented today for a 3 day history of
  vomiting and diarrhea. Problems include:
    A1 – acute vomiting – R/O primary GI (foreign body, dietary indiscretion/gastroenteritis,
    parasites, GI lymphoma, other) vs. secondary metabolic (pancreatitis, Addison’s disease,
    acute renal failure, hepatitis, other)
    A2 – small bowel diarrhea (large vs. small depends on your history taking and exam
    findings) – list of rule-outs
Your problem list is generated from historical findings (history of vomiting and small bowel diarrhea in above example even if you don’t witness it), physical exam, and labwork, and yes, you should write out differentials for individual lab abnormalities (hypercalcemia, elevated ALT, low cholesterol, each individually at least initially).

PLAN
plan! Now you take your problem list and you can do one of two things. You can address each problem with a corresponding plan (P1 for A1 and so on), but this leads to repeated writing of tests if they address two problems (i.e. a chemistry panel may be part of your plan vomiting and diarrhea, why write it twice?). A simpler way to do it is to write what you want to do and why. This section includes diagnostic and treatment plan.
  EX:
    Diagnostics:
    Complete blood count - to assess for neutrophilia, bands toxic change suggestive of
    inflammation or infection
    Chemistry profile – screen for metabolic causes of V/D and changes in proteins and
    electrolytes
    Urinalysis – to assess renal tubular function
    Fecal exam – to rule out parasites
    Abdominal radiographs – to look for obstruction, abdominal masses, foreign objects
    Treatment:
    NPO – to rest the GI tract and decrease vomiting
    Dolasetron – to treat vomiting
    IV fluids – for rehydration

When you are writing the plan for hospitalized patients, include details! For instance, if
you want to give fluids, you should write what type, what rate, and how you decided on
that rate (calculate dehydration + maintenance + losses). If you plan to give a drug, say
what it is, the dose and route and frequency, and why. Remember that the SOAP is
dynamic for inpatients and that with each day: your S is compared to the last S, your O
should focus on the changes in findings, the A should change as diagnoses are made,
things resolve or new problems arise, and the P should change as the needs for the patient
change. Do not write a SOAP that says, “no changes from yesterday, continue with plan
from yesterday.” SOAPing inpatients is an exercise in developing your critical thinking
about cases, and you’ll get out of it what you put into it. You will understand your case
that much better if you put the time into your assessment each day.
"""

response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Please convert the following transcription of a veterinary appointment into SOAP notes."+
                                    "Please keep in mind that there may be some transcription errors, so using context will be important.\n\n" + transcript.text},
    ],
    temperature=0,
)

print(response.choices[0].message.content)

# TODO: define a proper JSON schema object with enumerated values, data types, etc. (these could be configurable and will help accuracy of generated notes immensely)
"""Define a JSON SOAP note structure
{
  "subjective": "",
  "objective": {
    "temperature": 0.0,
    "pulse": 0.0,
    "respiration": 0.0,
    "bodyConditionScore": 0,
    "weight": 0.0,
    "mucousMembranes": "",
    "capillaryRefillTime": 0.0,
    "hydrationStatus": "",
    "EENT": {
      "dental": "",
      "ears": "",
      "eyes": "",
      "throat": "",
      "nose": ""
    },
    "peripheralLymphNodes": "",
    "H/L": {
      "heart": "",
      "lungs": ""
    },
    "ABD": {
      "abdomen": "",
      "rectum": "",
    },
    "urogenital": "",
    "MSI": {
      "musculoskeletal": "",
      "integument": ""
      # TODO: add more criteria for full ortho exam
    },
    "neurologic": {
      "mentation": "",
      "gait": "",
      "cranialNerves": "",
      "reflexes": ""
      # TODO: add more criteria for full neuro exam
    }
  }
}
"""

"""
{
   "name":"generate_SOAP_notes",
   "description":"Generates human-readable SOAP notes from structured JSON data",
   "parameters":{
      "type":"object",
      "properties":{
         "subjective":{
            "type":"string",
            "description":"The subjective information provided by the patient about their condition."
         },
         "objective":{
            "type":"object",
            "description":"Objective, measurable data collected during the patient's examination.",
            "properties":{
               "temperature":{
                  "type":"number",
                  "description":"The patient's body temperature."
               },
               "pulse":{
                  "type":"number",
                  "description":"The patient's pulse rate."
               },
               "respiration":{
                  "type":"number",
                  "description":"The patient's respiration rate."
               },
               "bodyConditionScore":{
                  "type":"integer",
                  "enum": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                  "description":"Body Condition Score ( 1/9 – severely underweight, 9/9 severely overweight)"
               },
               "weight":{
                  "type":"number",
                  "description":"The patient's weight."
               },
               "mucousMembranes":{
                  "type":"string",
                  "description":"The condition of the patient's mucous membranes."
               },
               "capillaryRefillTime":{
                  "type":"number",
                  "description":"The time taken for color to return to an external capillary bed after pressure is applied."
               },
               "hydrationStatus":{
                  "type":"string",
                  "description":"The patient's hydration status."
               },
               "EENT":{
                  "type":"object",
                  "description":"Examination findings related to Eyes, Ears, Nose, and Throat.",
                  "properties":{
                     "dental":{
                        "type":"string",
                        "description":"Findings related to the dental examination."
                     },
                     "ears":{
                        "type":"string",
                        "description":"Findings related to the ear examination."
                     },
                     "eyes":{
                        "type":"string",
                        "description":"Findings related to the eye examination."
                     },
                     "throat":{
                        "type":"string",
                        "description":"Findings related to the throat examination."
                     },
                     "nose":{
                        "type":"string",
                        "description":"Findings related to the nose examination."
                     }
                  }
               },
               "peripheralLymphNodes":{
                  "type":"string",
                  "description":"Findings related to the peripheral lymph nodes examination."
               },
               "H/L":{
                  "type":"object",
                  "description":"Findings related to the Heart and Lungs examination.",
                  "properties":{
                     "heart":{
                        "type":"string",
                        "description":"Findings related to the heart examination."
                     },
                     "lungs":{
                        "type":"string",
                        "description":"Findings related to the lungs examination."
                     }
                  }
               },
               "ABD":{
                  "type":"object",
                  "description":"Findings related to the Abdomen and Rectum examination.",
                  "properties":{
                     "abdomen":{
                        "type":"string",
                        "description":"Findings related to the abdomen examination."
                     },
                     "rectum":{
                        "type":"string",
                        "description":"Findings related to the rectum examination."
                     }
                  }
               },
               "urogenital":{
                  "type":"string",
                  "description":"Findings related to the urogenital examination."
               },
               "MSI":{
                  "type":"object",
                  "description":"Findings related to the Musculoskeletal and Integument examination.",
                  "properties":{
                     "musculoskeletal":{
                        "type":"string",
                        "description":"Findings related to the musculoskeletal examination."
                     },
                     "integument":{
                        "type":"string",
                        "description":"Findings related to the integument examination."
                     }
                  },
                  "required": []
               },
               "neurologic":{
                  "type":"object",
                  "description":"Findings related to the Neurologic examination.",
                  "properties":{
                     "mentation":{
                        "type":"string",
                        "description":"Findings related to the patient's mentation."
                     },
                     "gait":{
                        "type":"string",
                        "description":"Findings related to the patient's gait."
                     },
                     "cranialNerves":{
                        "type":"string",
                        "description":"Findings related to the cranial nerves examination."
                     },
                     "reflexes":{
                        "type":"string",
                        "description":"Findings related to the reflexes examination."
                     }
                  },
                  "required": []
               }
            },
            "required":[
               "temperature",
               "pulse",
               "respiration",
               "bodyConditionScore",
               "weight",
               "mucousMembranes",
               "capillaryRefillTime",
               "hydrationStatus",
               "EENT",
               "peripheralLymphNodes",
               "H/L",
               "ABD",
               "urogenital",
               "MSI",
               "neurologic"
            ]
         },
         "assessment":{
            "type":"array",
            "items":{
               "type":"string"
            },
            "description":"The clinician's assessments of the patient's condition."
         },
         "plan":{
            "type":"string",
            "description":"The plan of action for treating the patient's condition."
         }
      },
      "required":[
         "subjective",
         "objective",
         "assessment",
         "plan"
      ]
   },
   "output":{
      "type":"string",
      "description":"The generated SOAP note in human-readable format."
   }
}
"""

functions = [{
   "name":"generate_SOAP_notes",
   "description":"Generates human-readable SOAP notes from structured JSON data",
   "parameters":{
      "type":"object",
      "properties":{
         "subjective":{
            "type":"string",
            "description":"The subjective information provided by the patient about their condition."
         },
         "objective":{
            "type":"object",
            "description":"Objective, measurable data collected during the patient's examination.",
            "properties":{
               "temperature":{
                  "type":"number",
                  "description":"The patient's body temperature."
               },
               "pulse":{
                  "type":"number",
                  "description":"The patient's pulse rate."
               },
               "respiration":{
                  "type":"number",
                  "description":"The patient's respiration rate."
               },
               "bodyConditionScore":{
                  "type":"integer",
                  "enum": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                  "description":"Body Condition Score ( 1/9 – severely underweight, 9/9 severely overweight)"
               },
               "weight":{
                  "type":"number",
                  "description":"The patient's weight."
               },
               "mucousMembranes":{
                  "type":"string",
                  "description":"The condition of the patient's mucous membranes."
               },
               "capillaryRefillTime":{
                  "type":"number",
                  "description":"The time taken for color to return to an external capillary bed after pressure is applied."
               },
               "hydrationStatus":{
                  "type":"string",
                  "description":"The patient's hydration status."
               },
               "EENT":{
                  "type":"object",
                  "description":"Examination findings related to Eyes, Ears, Nose, and Throat.",
                  "properties":{
                     "dental":{
                        "type":"string",
                        "description":"Findings related to the dental examination."
                     },
                     "ears":{
                        "type":"string",
                        "description":"Findings related to the ear examination."
                     },
                     "eyes":{
                        "type":"string",
                        "description":"Findings related to the eye examination."
                     },
                     "throat":{
                        "type":"string",
                        "description":"Findings related to the throat examination."
                     },
                     "nose":{
                        "type":"string",
                        "description":"Findings related to the nose examination."
                     }
                  }
               },
               "peripheralLymphNodes":{
                  "type":"string",
                  "description":"Findings related to the peripheral lymph nodes examination."
               },
               "H/L":{
                  "type":"object",
                  "description":"Findings related to the Heart and Lungs examination.",
                  "properties":{
                     "heart":{
                        "type":"string",
                        "description":"Findings related to the heart examination."
                     },
                     "lungs":{
                        "type":"string",
                        "description":"Findings related to the lungs examination."
                     }
                  }
               },
               "ABD":{
                  "type":"object",
                  "description":"Findings related to the Abdomen and Rectum examination.",
                  "properties":{
                     "abdomen":{
                        "type":"string",
                        "description":"Findings related to the abdomen examination."
                     },
                     "rectum":{
                        "type":"string",
                        "description":"Findings related to the rectum examination."
                     }
                  }
               },
               "urogenital":{
                  "type":"string",
                  "description":"Findings related to the urogenital examination."
               },
               "MSI":{
                  "type":"object",
                  "description":"Findings related to the Musculoskeletal and Integument examination.",
                  "properties":{
                     "musculoskeletal":{
                        "type":"string",
                        "description":"Findings related to the musculoskeletal examination."
                     },
                     "integument":{
                        "type":"string",
                        "description":"Findings related to the integument examination."
                     }
                  },
                  "required": []
               },
               "neurologic":{
                  "type":"object",
                  "description":"Findings related to the Neurologic examination.",
                  "properties":{
                     "mentation":{
                        "type":"string",
                        "description":"Findings related to the patient's mentation."
                     },
                     "gait":{
                        "type":"string",
                        "description":"Findings related to the patient's gait."
                     },
                     "cranialNerves":{
                        "type":"string",
                        "description":"Findings related to the cranial nerves examination."
                     },
                     "reflexes":{
                        "type":"string",
                        "description":"Findings related to the reflexes examination."
                     }
                  },
                  "required": []
               }
            },
            "required":[
               "temperature",
               "pulse",
               "respiration",
               "bodyConditionScore",
               "weight",
               "mucousMembranes",
               "capillaryRefillTime",
               "hydrationStatus",
               "EENT",
               "peripheralLymphNodes",
               "H/L",
               "ABD",
               "urogenital",
               "MSI",
               "neurologic"
            ]
         },
         "assessment":{
            "type":"array",
            "items":{
               "type":"string"
            },
            "description":"The clinician's assessments of the patient's condition."
         },
         "plan":{
            "type":"string",
            "description":"The plan of action for treating the patient's condition."
         }
      },
      "required":[
         "subjective",
         "objective",
         "assessment",
         "plan"
      ]
   },
   "output":{
      "type":"string",
      "description":"The generated SOAP note in human-readable format."
   }
}]

system_message = """Don't make assumptions about what values to plug into functions. Do not provide values for parameters not specified in the request. If a required value is not provided, provide the JSON value 'null'."""

response = client.chat.completions.create(
    # response_format= {"type": "json_object"},
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Generate SOAP notes for the following patient interaction:\n\n" + transcript.text},
    ],
    functions=functions,
    temperature=0,
)

json.loads(response.choices[0].message.function_call.arguments)

"""# 5. SOAP Search Demo

At this point, we will want to test searching over SOAP notes. We will have to upload generated notes to our in-memory Qdrant test database[0] and then test running some sample search queries using the Qdrant test client. We will need Elena's input for generating the sample queries.

[0] I would start by essentially storing no additional metadata other than an ID and the original text along with the vector. But, we can play around with this later to improve search functionality. My guess is the basic (id, text, embedding) schema will blow current search functionality out of the water so that's good enough for a PoC.
"""

from google.colab import drive
drive.mount('/content/drive')



system_message = """You are a helpful assistant designed to generate OpenAI function descriptions that will be used to assist function calling with GPT-4. For example, given the following function name, description, and sample parameters

get_current_weather: gets the weather in the specified location in either degrees farenheit or celsius.

{
  "location": "Glasgow, Scotland",
  "format": "celsius"
}

you would return

[
    {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
            },
            "required": ["location", "format"],
        },
    },
]
"""

user_message = """generate_SOAP_notes: generates human readable SOAP notes from JSON notes.

{
  "subjective": "",
  "objective": {
    "temperature": 0.0,
    "pulse": 0.0,
    "respiration": 0.0,
    "bodyConditionScore": 0,
    "weight": 0.0,
    "mucousMembranes": "",
    "capillaryRefillTime": 0.0,
    "hydrationStatus": "",
    "EENT": {
      "dental": "",
      "ears": "",
      "eyes": "",
      "throat": "",
      "nose": ""
    },
    "peripheralLymphNodes": "",
    "H/L": {
      "heart": "",
      "lungs": ""
    },
    "ABD": {
      "abdomen": "",
      "rectum": "",
    },
    "urogenital": "",
    "MSI": {
      "musculoskeletal": "",
      "integument": ""
      # TODO: add more criteria for full ortho exam
    },
    "neurologic": {
      "mentation": "",
      "gait": "",
      "cranialNerves": "",
      "reflexes": ""
      # TODO: add more criteria for full neuro exam
    }
  },
  "assessment": [""],
  "plan": ""
}
"""

response = client.chat.completions.create(
    response_format= {"type": "json_object"},
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ],
    temperature=0,
)

import json
json.loads(response.choices[0].message.content)